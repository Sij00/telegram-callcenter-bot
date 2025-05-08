import telebot
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
admin_ids = list(map(int, os.getenv("ADMIN_IDS").split(",")))

# DB setup
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    city TEXT,
    assigned_to INTEGER,
    status TEXT,
    comment TEXT
)
''')
conn.commit()

# Command: start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id in admin_ids:
        bot.reply_to(message, "سلام مدیر! از دستور /upload برای وارد کردن لید استفاده کنید.")
    else:
        bot.reply_to(message, "سلام! با دستور /myleads لیدهای شما نمایش داده میشه.")

# Command: upload excel (فقط برای مدیر)
@bot.message_handler(commands=['upload'])
def ask_file(message):
    if message.from_user.id in admin_ids:
        msg = bot.reply_to(message, "لطفاً فایل اکسل را ارسال کنید.")
        bot.register_next_step_handler(msg, handle_excel_upload)
    else:
        bot.reply_to(message, "شما اجازه دسترسی به این بخش را ندارید.")

# تابع آپلود فایل
def handle_excel_upload(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("leads.xlsx", 'wb') as f:
            f.write(downloaded_file)

        import pandas as pd
        df = pd.read_excel("leads.xlsx")
        for _, row in df.iterrows():
            cursor.execute("INSERT INTO leads (name, phone, city) VALUES (?, ?, ?)",
                           (row['name'], row['phone'], row['city']))
        conn.commit()
        bot.reply_to(message, "لیدها با موفقیت آپلود شدند.")
    else:
        bot.reply_to(message, "فایل معتبر نبود.")

# Command: myleads برای مشاور
@bot.message_handler(commands=['myleads'])
def show_leads(message):
    user_id = message.from_user.id
    cursor.execute("SELECT id, name, phone, city FROM leads WHERE assigned_to = ?", (user_id,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            bot.send_message(user_id, f"#{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    else:
        bot.reply_to(message, "فعلاً لیدی برای شما ثبت نشده.")

bot.polling()
