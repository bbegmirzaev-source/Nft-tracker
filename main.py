import telebot
import sqlite3
import requests
from telebot import types

# 1. Konfiguratsiya
TOKEN = "8883021472:AAGzOX6NPf2m9iDtS0FimxFM4qoBktmZ_WU"
TONAPI_KEY = "AFN6ZL3Q4AWP55QAAAALXJWSCU7COMV44Y2WY4W2LAOUC4T3DVECLNSV2ORGQPAFSXSSQ7I"
ADMIN_ID = 7801965871 

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 2. Baza sozlamalari
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, lang TEXT)')
conn.commit()

# 3. Yordamchi funksiyalar
def get_language_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    return markup

def get_nft_info(address):
    url = f"https://tonapi.io/v2/nfts/collections/{address}"
    headers = {'Authorization': f'Bearer {TONAPI_KEY}'}
    try:
        response = requests.get(url, headers=headers).json()
        name = response.get('metadata', {}).get('name', 'Noma\'lum')
        items_count = response.get('next_item_index', 'Aniqlanmadi')
        return f"🖼 <b>Kolleksiya:</b> {name}\n🔢 <b>NFTlar soni:</b> {items_count}"
    except:
        return None

# 4. Bot buyruqlari
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "👋 <b>Professional TON NFT Tracker</b>\n\nIltimos, tilni tanlang / Пожалуйста, выберите язык:", reply_markup=get_language_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_lang(call):
    lang = call.data.split("_")[1]
    cursor.execute('UPDATE users SET lang=? WHERE id=?', (lang, call.message.chat.id))
    conn.commit()
    bot.edit_message_text(text="✅ Til tanlandi. Endi NFT kolleksiya manzilini (EQ...) yuboring.", 
                          chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda message: message.text.startswith("EQ"))
def nft_search(message):
    bot.reply_to(message, "🔍 Qidirilmoqda...")
    info = get_nft_info(message.text.strip())
    if info:
        bot.send_message(message.chat.id, info)
    else:
        bot.send_message(message.chat.id, "❌ Ma'lumot topilmadi. Manzilni tekshiring.")

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"👥 Jami foydalanuvchilar: {count}")

bot.infinity_polling()
