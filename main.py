import telebot
from telebot import types
import webbrowser
import sqlite3
import asyncio


bot = telebot.TeleBot('')

# Создание базы данных и таблицы
conn = sqlite3.connect('user_cards.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT,
    height REAL,
    weight REAL,
    age INTEGER,
    activities TEXT
)
''')
conn.commit()
cursor.execute('''
CREATE TABLE IF NOT EXISTS commands (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    commands_name TEXT NOT NULL UNIQUE  
)
''')
conn.commit()

cursor.execute("SELECT COUNT(*) FROM commands")
count = cursor.fetchone()[0]

if count == 0:
    cursor.execute('''
    INSERT INTO commands (commands_name) VALUES  
        ('Команда 1'),
        ('Команда 2'),
        ('Команда 3')
    ''')
    conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users_comm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    user_id INTEGER,
    full_name TEXT,
    height REAL,
    weight REAL,
    age INTEGER,
    activities TEXT,
    FOREIGN KEY (team_id) REFERENCES commands(team_id) ON DELETE CASCADE
)
''')
conn.commit()
cursor.execute("SELECT team_id FROM commands WHERE commands_name IN ('Команда 1', 'Команда 2', 'Команда 3')")
existing_teams = cursor.fetchall()
print("Существующие команды:", existing_teams)
cursor.execute("SELECT * FROM users_comm WHERE team_id = 1")
teams = cursor.fetchall()
print("Команда 1 в таблице:", teams)
cursor.execute("SELECT * FROM users_comm WHERE team_id =2")
teams = cursor.fetchall()
print("Команда 2 в таблице:", teams)
cursor.execute("SELECT * FROM users_comm WHERE team_id = 3")
teams = cursor.fetchall()
print("Команда 3 в таблице:", teams)

# Словарь для временного хранения данных пользователя
user_data = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
   chat_id = message.chat.id

   cursor.execute('SELECT * FROM users WHERE user_id = ?', (chat_id,))
   user = cursor.fetchone()

   markup = types.InlineKeyboardMarkup() 

   if user:
        # Если пользователь уже существует
        btn_show = types.InlineKeyboardButton('Показать мою карточку',callback_data='show_card')
        markup.add(btn_show)
        bot.send_message(
            chat_id,
            "Вы уже создали карточку. Нажмите кнопку ниже, чтобы посмотреть её.",
            reply_markup=markup
        )
   else:
      btn_create = types.InlineKeyboardButton('Создать карточку пользователя', callback_data='create_card')
      markup.add(btn_create)
    
      commands_text = """
<b>Список доступных команд:</b>

/start - Начать работу с ботом

/myinfo - Показать мою карточку

/help - Помощь

"""
      bot.send_message(chat_id, commands_text, parse_mode='HTML', reply_markup=markup)

# Обработчик кнопки "Создать карточку пользователя"
@bot.callback_query_handler(func=lambda call: call.data == 'create_card')
def create_card(call):
    user_data[call.message.chat.id] = {}
    msg = bot.send_message(call.message.chat.id, "Введите ФИО:")
    bot.register_next_step_handler(msg, process_full_name)

def process_full_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['full_name'] = message.text
    msg = bot.send_message(chat_id, "Введите ваш рост (в см):")
    bot.register_next_step_handler(msg, process_height)

def process_height(message):
    chat_id = message.chat.id
    try:
        height = float(message.text)
        user_data[chat_id]['height'] = height
        msg = bot.send_message(chat_id, "Введите ваш вес (в кг):")
        bot.register_next_step_handler(msg, process_weight)
    except ValueError:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число для роста.")
        bot.register_next_step_handler(msg, process_height)

def process_weight(message):
    chat_id = message.chat.id
    try:
        weight = float(message.text)
        user_data[chat_id]['weight'] = weight
        msg = bot.send_message(chat_id, "Введите ваш возраст:")
        bot.register_next_step_handler(msg, process_age)
    except ValueError:
        msg = bot.send_message(chat_id, "Пожалуйста, введите число для веса.")
        bot.register_next_step_handler(msg, process_weight)

def process_age(message):
    chat_id = message.chat.id
    try:
        age = int(message.text)
        user_data[chat_id]['age'] = age
        msg = bot.send_message(chat_id, "Введите виды вашей активности (через запятую):")
        bot.register_next_step_handler(msg, process_activities)
    except ValueError:
        msg = bot.send_message(chat_id, "Пожалуйста, введите целое число для возраста.")
        bot.register_next_step_handler(msg, process_age)

def process_activities(message):
    chat_id = message.chat.id
    user_data[chat_id]['activities'] = message.text
    
    # Сохраняем данные в базу данных
    cursor.execute('''
    INSERT INTO users (user_id, full_name, height, weight, age, activities)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, 
          user_data[chat_id]['full_name'], 
          user_data[chat_id]['height'], 
          user_data[chat_id]['weight'], 
          user_data[chat_id]['age'], 
          user_data[chat_id]['activities']))
    conn.commit()
    
    # Создаем кнопку для просмотра информации
    markup = types.InlineKeyboardMarkup()
    btn_show = types.InlineKeyboardButton('Показать мою карточку', callback_data='show_card')
    markup.add(btn_show)
    
    msg = bot.send_message(chat_id, "Ваша карточка успешно создана!\n\n Теперь отправьте мне любое сообщение, чтобы я мог добавить вас в одну из команд !", reply_markup=markup)
    bot.register_next_step_handler(msg, choice_command)

def choice_command(message):
    chat_id = message.chat.id

    markup = types.InlineKeyboardMarkup()
    btn_show_one = types.InlineKeyboardButton('Команда 1', callback_data='join_team_one')
    btn_show_two = types.InlineKeyboardButton('Команда 2', callback_data='join_team_two')
    btn_show_three = types.InlineKeyboardButton('Команда 3', callback_data='join_team_three')
    markup.row(btn_show_one,btn_show_two,btn_show_three)
    # markup.add(btn_add) 

    bot.send_message(chat_id, "Выберите свою команду :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'join_team_one')
def join_team_one(call):
    chat_id = call.message.chat.id
    team_id = 1
    
    cursor.execute('''
    INSERT INTO users_comm (team_id, user_id, full_name, height, weight, age, activities)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (team_id,
          chat_id,
          user_data[chat_id]['full_name'], 
          user_data[chat_id]['height'], 
          user_data[chat_id]['weight'], 
          user_data[chat_id]['age'], 
          user_data[chat_id]['activities']))
    conn.commit()
    bot.send_message(chat_id, "Вы успешно добавлены в команду 1!")

@bot.callback_query_handler(func=lambda call: call.data == 'join_team_two')
def join_team_two(call):
    chat_id = call.message.chat.id
    team_id = 2

    cursor.execute('''
    INSERT INTO users_comm (team_id, user_id, full_name, height, weight, age, activities)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (team_id,
          chat_id,
          user_data[chat_id]['full_name'], 
          user_data[chat_id]['height'], 
          user_data[chat_id]['weight'], 
          user_data[chat_id]['age'], 
          user_data[chat_id]['activities']))
    conn.commit()
    bot.send_message(chat_id, "Вы успешно добавлены в команду 2!")

@bot.callback_query_handler(func=lambda call: call.data == 'join_team_three')
def join_team_three(call):
    chat_id = call.message.chat.id
    team_id = 3

    cursor.execute('''
    INSERT INTO users_comm (team_id, user_id, full_name, height, weight, age, activities)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (team_id,
          chat_id,
          user_data[chat_id]['full_name'], 
          user_data[chat_id]['height'], 
          user_data[chat_id]['weight'], 
          user_data[chat_id]['age'], 
          user_data[chat_id]['activities']))
    conn.commit()
    bot.send_message(chat_id, "Вы успешно добавлены в команду 3!")


# Обработчик команды /myinfo
@bot.message_handler(commands=['myinfo'])
def myinfo(message):
    chat_id = message.chat.id
    cursor.execute('SELECT * FROM users WHERE user_id = ? ORDER BY id DESC LIMIT 1', (chat_id,))
    user = cursor.fetchone()
    
    if user:
        show_card_info(chat_id, user)
    else:
        bot.send_message(chat_id, "У вас нет созданной карточки. Нажмите 'Создать карточку пользователя'.")

# Обработчик callback для кнопки "Показать мою карточку"
@bot.callback_query_handler(func=lambda call: call.data == 'show_card')
def callback_show_card(call):
    chat_id = call.message.chat.id
    cursor.execute('SELECT * FROM users WHERE user_id = ? ORDER BY id DESC LIMIT 1', (chat_id,))
    user = cursor.fetchone()
    
    if user:
        show_card_info(chat_id, user)
    else:
        bot.send_message(chat_id, "У вас нет созданной карточки. Нажмите 'Создать карточку пользователя'.")

def show_card_info(chat_id, user):
    card_info = f"""
📋 Ваша карточка:

ФИО: {user[2]}
Рост: {user[3]} см
Вес: {user[4]} кг
Возраст: {user[5]} лет
Виды активности: {user[6]}
"""
    bot.send_message(chat_id, card_info)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help(message):
    help_text = """

Команды:
/start - Начать работу с ботом
/myinfo - Показать мою карточку
/help - Показать это сообщение

"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['users'])
def myinfo(message):
    chat_id = message.chat.id
    cursor.execute('SELECT * FROM users ')
    users = cursor.fetchall()
    
    if users:
        show_all_users(chat_id,users)
    else:
        bot.send_message(chat_id,"База пуста")

def show_all_users(chat_id,users):
    card_info = ''
    
    for el in users:
       card_info += f"""
📋 Ваша карточка:

ФИО: {el[2]}
Рост: {el[3]} см
Вес: {el[4]} кг
Возраст: {el[5]} лет
Виды активности: {el[6]}
"""
    bot.send_message(chat_id, card_info)
# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()

