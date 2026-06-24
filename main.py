import telebot
import sqlite3

TOKEN = "8883021472:AAGzOX6NPf2m9iDtS0FimxFM4qoBktmZ_WU"
ADMIN_ID = 7801965871 # O'z ID raqamingizni kiriting
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Baza yaratish
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "👋 <b>TON NFT Tracker</b> botiga xush kelibsiz!\n\nMen sizga TON tarmog'idagi NFT narxlarini kuzatishga yordam beraman.")

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"👥 Jami foydalanuvchilar: {count}")

@bot.message_handler(commands=['reklama'])
def reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    for user in users:
        try: bot.send_message(user[0], message.text)
        except: pass
    bot.reply_to(message, "✅ Reklama yuborildi.")

bot.infinity_polling()
