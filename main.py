import telebot
import sqlite3
import requests
from telebot import types

# Konfiguratsiya
TOKEN = "8883021472:AAGzOX6NPf2m9iDtS0FimxFM4qoBktmZ_WU"
TONAPI_KEY = "AFN6ZL3Q4AWP55QAAAALXJWSCU7COMV44Y2WY4W2LAOUC4T3DVECLNSV2ORGQPAFSXSSQ7I"
ADMIN_ID = 7801965871

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Baza sozlamalari
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, lang TEXT)')
conn.commit()

# Yordamchi Funksiyalar
def get_language_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    return markup

# Asosiy Handlerlar
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "👋 <b>TON NFT Tracker</b> botiga xush kelibsiz!\n\nIltimos, tilni tanlang:", reply_markup=get_language_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_lang(call):
    lang = call.data.split("_")[1]
    cursor.execute('UPDATE users SET lang=? WHERE id=?', (lang, call.message.chat.id))
    conn.commit()
    bot.edit_message_text(text=f"✅ Til tanlandi: {lang.upper()}.\n\nEndi menga kolleksiya nomini yozing (masalan: <b>TON Diamonds</b>):", 
                          chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda message: not message.text.startswith("/"))
def search_by_name(message):
    query = message.text.strip()
    bot.send_message(message.chat.id, "🔍 Qidirilmoqda...")
    
    url = f"https://tonapi.io/v2/search/accounts?name={query}"
    headers = {'Authorization': f'Bearer {TONAPI_KEY}'}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'accounts' in data and len(data['accounts']) > 0:
            acc = data['accounts'][0]
            name = acc.get('name', 'Noma\'lum')
            address = acc.get('address', '')
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 To'liq ma'lumot", callback_data=f"price_{address}"))
            markup.add(types.InlineKeyboardButton("💎 Getgems'da ko'rish", url=f"https://getgems.io/collection/{address}"))
            
            bot.send_message(message.chat.id, f"✅ <b>Topildi:</b> {name}\n🔗 <b>Manzil:</b> <code>{address}</code>", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Kolleksiya topilmadi. Boshqa nom bilan urinib ko'ring.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
def callback_price(call):
    address = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "Ma'lumotlar yuklanmoqda...")
    
    url = f"https://tonapi.io/v2/nfts/collections/{address}"
    headers = {'Authorization': f'Bearer {TONAPI_KEY}'}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'metadata' in data:
            name = data['metadata'].get('name', 'Noma\'lum')
            items = data.get('next_item_index', 'Aniqlanmagan')
            info = f"🖼 <b>Kolleksiya:</b> {name}\n🔢 <b>NFTlar soni:</b> {items}\n🔗 <b>Manzil:</b> <code>{address}</code>"
            bot.send_message(call.message.chat.id, info)
        else:
            bot.send_message(call.message.chat.id, "❌ Bu manzil bo'yicha kolleksiya ma'lumotlari topilmadi.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ma'lumotlarni yuklab bo'lmadi: {str(e)}")

bot.infinity_polling()
