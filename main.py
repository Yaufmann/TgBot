import telebot
from telebot import types
import webbrowser
import sqlite3


bot = telebot.TeleBot('7704891499:AAE8fLE75VJXDaPzFmc6fRxFFlUmSQlNi3I')

name = None
age = None
height = None
weight = None

@bot.message_handler(commands=['start'])
def start(message) :
   conn = sqlite3.connect('mainDB.sql')
   cursor = conn.cursor()

   cursor.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(70), age int, height int, weight int, activities varchar(250))')
   conn.commit()
   cursor.close()
   conn.close()

   markup = types.InlineKeyboardMarkup()
   btn1 = types.InlineKeyboardButton('Создать карточку игрока', callback_data='create')
   markup.row(btn1)
   bot.send_message(message.chat.id, f'<b>Добро пожаловать в чат-бот {message.from_user.first_name} !</b>\n\n Для просмотра информации введите - /info\n\n Для изменения данных в карточке введите - /update\n\n Для просомтра всех команд введите - /teams\n\n Для помощи по боту - /help',parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)   
def callback_message(callback):
   if callback.data == 'create':
      bot.send_message(callback.message.chat.id, "Начало регистрации. Введите свое ФИО :")
      bot.register_next_step_handler(callback.message, user_name)

def user_name(message):
   global name
   name = message.text.strip()
   bot.send_message(message.chat.id, "Введите свой возраст :")
   bot.register_next_step_handler(message, user_age)

def user_age(message):
   global age
   age = message.text.strip()
   bot.send_message(message.chat.id, "Введите свой рост :")
   bot.register_next_step_handler(message, user_height)

def user_height(message):
   global height
   height = message.text.strip()
   bot.send_message(message.chat.id, "Введите свой вес :")
   bot.register_next_step_handler(message, user_weight)

def user_weight(message):
   global weight
   weight = message.text.strip()
   bot.send_message(message.chat.id, "Введите свои активности :")
   bot.register_next_step_handler(message, user_activities)

def user_activities(message):
   activities = message.text.strip()

   conn = sqlite3.connect('mainDB.sql')
   cursor = conn.cursor()

   cursor.execute(f"INSERT INTO users (name, age, height, weight, activities) VALUES ('%s', '%s', '%s', '%s', '%s')" % (name, age, height, weight, activities))
   conn.commit()

   user_id = message.from_user.id

   markup = types.InlineKeyboardMarkup()
   markup.add(types.InlineKeyboardButton('Открыть свою карточку', callback_data='open_card'))
   
   bot.send_message(message.chat.id, "<b>Пользователь зарегистрирован!</b>", parse_mode='html', reply_markup=markup)

   cursor.close()
   conn.close()

@bot.callback_query_handler(func=lambda call: call.data == 'open_card')
def open_card(call):
      bot.answer_callback_query(call.id)

      user_id = call.from_user.id

      conn = sqlite3.connect('mainDB.sql')
      cursor = conn.cursor()

      cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
      user_data = cursor.fetchone()

      if user_data:
         info = f"""
         📌 <b>Ваша карточка</b> 📌
            
         👤 Имя: {user_data[1]}
         🎂 Возраст: {user_data[2]}
         📏 Рост: {user_data[3]}
         ⚖️ Вес: {user_data[4]}
         🏃 Активности: {user_data[5]}
            """
         bot.send_message(call.message.chat.id, info, parse_mode='HTML')

      cursor.close()
      conn.close()


@bot.message_handler(commands=['menu'])
def menu(message) :
   markup = types.ReplyKeyboardMarkup()
   btn1 = types.KeyboardButton('Просмотреть свою карточку')
   markup.row(btn1)
   btn2 = types.KeyboardButton('Добавить данные')
   btn3 = types.KeyboardButton('Посмотреть всеx пользователей')
   markup.row(btn2,btn3)
   bot.send_message(message.chat.id, 'Меню выбора действий' , reply_markup=markup)
   bot.register_next_step_handler(message, on_click)

def on_click(message): 
   if message.text == 'Просмотреть свою карточку':
      user_id = message.from_user.id

      conn = sqlite3.connect('mainDB.sql')
      cursor = conn.cursor()

      cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
      
      users = cursor.fetchall()

      # info = ''
      # for el in users:
      #    info+= f'{el[1]}\n\n Возраст: {el[2]}\n\n Рост: {el[3]}\n\n Вес: {el[4]}\n\n Активности: {el[5]}\n\n'
      
      if users:
         info = f"""
         Имя: {users[1]}
         Возраст: {users[2]}
         Рост: {users[3]}
         Вес: {users[4]}
         Активности: {users[5]}
         """
         bot.send_message(message.chat.id, info)

      cursor.close()
      conn.close()

      # bot.send_message(message.chat.id, users)

   if message.text == 'Добавить данные':
      bot.send_message(message.chat.id, 'Добавить данные')

   if message.text == 'Посмотреть всеx пользователей':

      conn = sqlite3.connect('mainDB.sql')
      cursor = conn.cursor()

      cursor.execute('SELECT * FROM users')
      users = cursor.fetchall()

      info = ''
      for el in users:
         info+= f'{el[1]}\n\n Возраст: {el[2]}\n\n Рост: {el[3]}\n\n Вес: {el[4]}\n\n Активности: {el[5]}\n\n'
      
      cursor.close()
      conn.close()
   
      bot.send_message(message.chat.id, info)
   

@bot.message_handler(commands=['site'])
def site(message) :
   bot.send_message(message.chat.id, '<b>Перенаправляю на сайт </b>', parse_mode='html')
   webbrowser.open('https://minudo.ru/')


@bot.message_handler(commands=['help'])
def main(message) :
   bot.send_message(message.chat.id, '<b>Чем я могу помочь ?</b>', parse_mode='html')

@bot.message_handler()
def info(m):
   if m.text.lower() == 'привет':
      bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name} {m.from_user.last_name}')
   elif m.text.lower() == 'id':
      bot.reply_to(m, f'Твой идентефикатор: {m.from_user.id}')

@bot.message_handler(content_types=['photo'])
def get_photo(message) :
   markup = types.InlineKeyboardMarkup()
   btn1 = types.InlineKeyboardButton('Перейти на сайт', url='https://minudo.ru/')
   markup.row(btn1)
   btn2 = types.InlineKeyboardButton('Удалить фото', callback_data='delete')
   btn3 = types.InlineKeyboardButton('Изменить текст', callback_data='edit')
   markup.row(btn2,btn3)
   bot.reply_to(message, "Это ваше фото", reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)   
def callback_message(callback):
   if callback.data == 'delete':
      bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
   elif callback == 'edit':
      bot.edit_message_text('Edit text',callback.message.chat.id, callback.message.message_id)


bot.polling(none_stop=True)