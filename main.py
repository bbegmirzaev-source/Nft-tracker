import telebot
import sqlite3
import requests
from telebot import types

# 1. Konfiguratsiya
TOKEN = "8883021472:AAGzOX6NPf2m9iDtS0FimxFM4qoBktmZ_WU"
TONAPI_KEY = "AFN6ZL3Q4AWP55QAAAALXJWSCU7COMV44Y2WY4W2LAOUC4T3DVECLNSV2ORGQPAFSXSSQ7I"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# 2. Baza sozlamalari
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, lang TEXT)')
conn.commit()

# 3. Yordamchi Funksiyalar
def get_language_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    return markup

# 4. Asosiy Handlerlar
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
    url = f"https://tonapi.io/v2/search/accounts?name={query}"
    headers = {'Authorization': f'Bearer {TONAPI_KEY}'}
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get('accounts'):
            acc = response['accounts'][0]
            name = acc.get('name', 'Noma\'lum')
            address = acc.get('address')
            
            # Tugmalar menyusi
            markup = types.InlineKeyboardMarkup()
            btn_info = types.InlineKeyboardButton("📋 To'liq ma'lumot", callback_data=f"price_{address}")
            btn_site = types.InlineKeyboardButton("💎 Getgems'da ko'rish", url=f"https://getgems.io/collection/{address}")
            markup.add(btn_info, btn_site)
            
            bot.send_message(message.chat.id, f"✅ <b>Topildi:</b> {name}", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Kolleksiya topilmadi. Boshqa nom bilan urinib ko'ring.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
def callback_price(call):
    address = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "Ma'lumotlar yuklanmoqda...")
    
    url = f"https://tonapi.io/v2/nfts/collections/{address}"
    headers = {'Authorization': f'Bearer {TONAPI_KEY}'}
    
    try:
        response = requests.get(url, headers=headers).json()
        name = response.get('metadata', {}).get('name', 'Noma\'lum')
        items = response.get('next_item_index', 'Aniqlanmagan')
        
        info = (f"🖼 <b>Kolleksiya:</b> {name}\n"
                f"🔢 <b>NFTlar soni:</b> {items}\n"
                f"🔗 <b>Manzil:</b> <code>{address}</code>")
        
        bot.send_message(call.message.chat.id, info)
    except Exception:
        bot.send_message(call.message.chat.id, "❌ Ma'lumotlarni yuklab bo'lmadi.")

bot.infinity_polling()
