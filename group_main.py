#GITHUB: shadxwblade 
from group_setting import show_group_menu, handle_group_actions, is_group_admin, start_rules_setup, start_welcome_setup
import sqlite3
import threading
import telebot
from telebot import types

bot = telebot.TeleBot('TOKEN')
bot_url = "URL"
group_url = "URL"

# ===== БДШКА (НУ ТИПО БД))) БАЗА ДАННЫХ, КРЧ БАЗИРОВАННАЯ БАЗА) =====
db = sqlite3.connect("groups.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS groups (
    chat_id INTEGER PRIMARY KEY,
    title TEXT)""")
db.commit()

# ===== ТАБЛИЦА ПРИВЕТСТВИЙ =====
sql.execute("""
CREATE TABLE IF NOT EXISTS welcome_settings (
    chat_id INTEGER PRIMARY KEY,
    text TEXT,
    photo_id TEXT)""")
db.commit()

# ===== ТАБЛИЦА ПРАВИЛ =====
sql.execute("""
CREATE TABLE IF NOT EXISTS group_rules (
    chat_id INTEGER PRIMARY KEY,
    text TEXT)""")
db.commit()

# >>>>>>>>>>>>>>> СТАРТ ПИЗДЕЦ КАКОЙ ОГРОМНЫЙ <<<<<<<<<<<<<<<

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Добавить в группу', url=bot_url))
    markup.add(types.InlineKeyboardButton('⚙️ Настроить группу', callback_data='groups'))
    markup.row(types.InlineKeyboardButton('💻 О проекте', callback_data='about'), types.InlineKeyboardButton('❓ Помощь', callback_data='help'))
    markup.row(types.InlineKeyboardButton('🔄 Перезапуск', callback_data='restart'), types.InlineKeyboardButton('📌 Функции', callback_data='func'))

    bot.send_message(message.chat.id,
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
        "<b>GROUP HELPER</b>, бот который поможет вам <b>легко и безопасно</b> управлять вашими группами!\n\n"
        "👉 <b>Добавьте меня в группу/супергруппу и сделайте меня Администратором</b>, чтобы я сразу же начал действовать!", parse_mode="HTML", reply_markup=markup)

# >>>>>>>>>>>>>>> КОМАНДЫ ТУТ БЛЯТЬ САМ ЧЕРТ НОГУ СЛОМИТ <<<<<<<<<<<<<<<

@bot.message_handler(commands=['rules'])
def rules(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    sql.execute("SELECT text FROM group_rules WHERE chat_id=?",(chat_id,))
    row = sql.fetchone()

    if row and row[0]:
        bot.send_message(message.chat.id, row[0], parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "📋 Правила для этой группы ещё не настроены.")

@bot.message_handler(func=lambda m: m.from_user.id in __import__("group_setting").rules_states)
def save_rules_text(message):
    from group_setting import rules_states
    user_id = message.from_user.id
    chat_id = rules_states.get(user_id)
    if not chat_id:
        return
    sql.execute("INSERT OR REPLACE INTO group_rules (chat_id, text) VALUES (?, ?)",(chat_id, message.text))
    db.commit()
    rules_states.pop(user_id, None)
    sql.execute("SELECT title FROM groups WHERE chat_id=?", (chat_id,))
    row = sql.fetchone()
    title = row[0] if row else "Неизвестная группа"
    bot.send_message(message.chat.id,f"✅ Правила для группы '{title}' сохранены.\n\n"
                                     "Теперь они доступны по команде /rules")


@bot.message_handler(content_types=['text'])
def save_welcome_text(message):
    from group_setting import welcome_states
    user_id = message.from_user.id
    if user_id not in welcome_states:
        return
    chat_id = welcome_states.pop(user_id)
    sql.execute("INSERT OR REPLACE INTO welcome_settings (chat_id, text, photo_id) VALUES (?, ?, ?)",(chat_id, message.text, None))
    db.commit()
    bot.send_message(message.chat.id, "✅ Текст приветствия сохранён")

@bot.message_handler(content_types=['photo'])
def save_welcome_photo(message):
    from group_setting import welcome_states
    user_id = message.from_user.id
    if user_id not in welcome_states:
        return
    chat_id = welcome_states.pop(user_id)
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    sql.execute("INSERT OR REPLACE INTO welcome_settings (chat_id, text, photo_id) VALUES (?, ?, ?)",(chat_id, caption, photo_id))
    db.commit()
    bot.send_message(message.chat.id, "✅ Приветствие с фото сохранено")

@bot.message_handler(content_types=['new_chat_members'])
def on_new_chat_members(message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        # === ЕСЛИ ДОБАВИЛИ БОТА ===
        if user.id == bot.get_me().id:
            sql.execute("INSERT OR IGNORE INTO groups (chat_id, title) VALUES (?, ?)",(chat_id, message.chat.title))
            db.commit()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='💬 Перейти в ЛС', url=group_url))
            member = bot.get_chat_member(chat_id, bot.get_me().id)
            if member.status in ('administrator', 'creator'):
                bot.send_message(chat_id,"Спасибо, что добавили меня в свою группу в качестве администратора!\n"
                                              "Запустите меня в личном чате для настройки этой группы, не мешая этому чату!",reply_markup=markup)
            else:
                bot.send_message(chat_id,"⚠️ Пожалуйста, выдайте мне админ-права для корректной работы.",reply_markup=markup)

            continue

# === ПРИВЕТСТВИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ ===

        sql.execute("SELECT text, photo_id FROM welcome_settings WHERE chat_id=?",(chat_id,))
        row = sql.fetchone()

        if not row:
            continue
        text, photo_id = row
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

        if text:
            text = text.replace("{user}", mention)

        if photo_id:
            bot.send_photo(chat_id, photo_id, caption=text, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, parse_mode="HTML")

@bot.message_handler(commands=['groups'])
def groups(message):
    bot.send_message(message.chat.id,'<b>Настройки Группы</b>\n'
        '👉 Выберите <b>группу</b>, настройки который вы желаете изменить', parse_mode="HTML")

@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(message.chat.id, '💻<b>О проекте</b>💻\n'
                                      '<b>GROUP HELPER</b> Бот для модерации ваших групп/супергрупп\n'
                                      'Бот разработан на <b>Python</b>\n\n'
                                      'Версия - <b>1.0</b>\n\n'
                                      'Дата <b>релиза</b> - 02.02.2026\n\n'
                                      '<u>Персонал бота</u>\n'
                                      '• <b>ReSP</b> - создатель и разработчик\n\n'
                                      'Буду очень рад если вы добавите своего бота к себе в группу!', parse_mode="HTML")

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '❓<b><u>Помощь</u></b>❓\n\n'
                                      '<b>Команды этого бота</b>\n'
                                      '/start - Запуск бота\n'
                                      '/help - Команды бота\n'
                                      '/about - О проекте\n'
                                      '/groups - Настройка и список ваших групп\n'
                                      '/rules - Правила группы (писать в группе)', parse_mode="HTML")

@bot.message_handler(commands=['func'])
def func(message):
    bot.send_message(message.chat.id, '📌️<b>Функции этого бота</b>\n\n'
                                      '<b>GROUP HELPER</b> для модерации ваших групп/супергрупп\n'
                                      'Данный бот умеет добавлять приветствия, выдавать предупреждения, банить, кикать', parse_mode="HTML")

@bot.message_handler(content_types=['left_chat_member'])
def on_bot_removed(message):
    # вышел не бот? мне похуй
    if message.left_chat_member.id != bot.get_me().id:
        return

    chat_id = message.chat.id

    # удаляем все подчистую
    sql.execute("DELETE FROM groups WHERE chat_id=?", (chat_id,))
    sql.execute("DELETE FROM welcome_settings WHERE chat_id=?", (chat_id,))
    sql.execute("DELETE FROM group_rules WHERE chat_id=?", (chat_id,))
    db.commit()

# >>>>>>>>>>>>>>> CALLBACK (ТИПО ЗВОНОК НАЗАД)0)0)) <<<<<<<<<<<<<<<

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)

    # === ОБРАБОТКА ДЕЙСТВИЙ ГРУППЫ (welcome / rules / cancel) ===

    sql.execute("SELECT chat_id, title FROM groups")
    groups = sql.fetchall()
    group_title_map = {chat_id: title for chat_id, title in groups}

    from group_setting import handle_group_actions
    if handle_group_actions(bot, call, group_title_map):
        return

    if call.data == 'start':
        show_main_menu(call.message, call.from_user.first_name)


    elif call.data == 'restart':
        msg = bot.send_message(call.message.chat.id, "✅ Бот перезапущен")
        threading.Timer(2,lambda message_id=msg.message_id: bot.delete_message(call.message.chat.id, message_id)).start()
        show_main_menu(call.message, call.from_user.first_name)

    elif call.data == 'groups':
        user_id = call.from_user.id
        markup = types.InlineKeyboardMarkup()

        sql.execute("SELECT chat_id, title FROM groups")
        groups = sql.fetchall()

        for chat_id, title in groups:
            try:
                member = bot.get_chat_member(chat_id, user_id)
                if member.status in ("administrator", "creator"):
                    markup.add(
                        types.InlineKeyboardButton(text=title,callback_data=f"group_{chat_id}"))
            except:
                continue

        markup.add(types.InlineKeyboardButton('⬅ Назад', callback_data='start'))

        bot.edit_message_text( chat_id=call.message.chat.id, message_id=call.message.message_id, text='<b>Настройки Группы</b>\n'
                 '👉 Выберите <b>группу</b>, настройки который вы желаете изменить', parse_mode="HTML", reply_markup=markup)


    elif call.data.startswith("group_"):
        chat_id = int(call.data.split("_")[1])
        user_id = call.from_user.id
        if not is_group_admin(bot, chat_id, user_id):
            bot.answer_callback_query(call.id,"⛔ Вы не администратор этой группы", show_alert=True)
            return
        sql.execute("SELECT title FROM groups WHERE chat_id=?", (chat_id,))
        group = sql.fetchone()
        if group:
            group_title = group[0]

            show_group_menu(bot, call, chat_id, group_title)

    elif call.data == 'about':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💻<b>О проекте</b>💻\n'
                                      '<b>GROUP HELPER</b> Бот для модерации ваших групп/супергрупп\n'
                                      'Бот разработан на <b>Python</b>\n\n'
                                      'Версия - <b>1.0</b>\n\n'
                                      'Дата <b>релиза</b> - 02.02.2026\n\n'
                                      '<u>Персонал бота</u>\n'
                                      '• <b>ReSP</b> - создатель и разработчик\n\n'
                                      'Буду очень рад если вы добавите своего бота к себе в группу!', parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅ Назад', callback_data='start')))

    elif call.data == 'help':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=
                                      '❓<b><u>Помощь</u></b>❓\n\n'
                                      '<b>Команды этого бота</b>\n'
                                      '/start - Запуск бота\n'
                                      '/help - Команды бота\n'
                                      '/about - О проекте\n'
                                      '/groups - Настройка и список ваших групп\n'
                                      '/rules - Правила группы (писать в группе)', parse_mode="HTML",
                              reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅ Назад', callback_data='start')))

    elif call.data == 'func':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=
                                    '📌️<b>Функции этого бота</b>\n\n'
                                    '<b>GROUP HELPER</b> создан для модерации ваших групп/супергрупп\n'
                                    'Данный бот умеет добавлять приветствия, выдавать предупреждения, банить, кикать', parse_mode="HTML",
                              reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('⬅ Назад', callback_data='start')))

def show_main_menu(message, first_name):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Добавить в группу', url=bot_url))
    markup.add(types.InlineKeyboardButton('⚙️ Настроить группу', callback_data='groups'))
    markup.row(types.InlineKeyboardButton('💻 О проекте', callback_data='about'), types.InlineKeyboardButton('❓ Помощь', callback_data='help'))
    markup.row(types.InlineKeyboardButton('🔄 Перезапуск', callback_data='restart'), types.InlineKeyboardButton('📌 Функции', callback_data='func'))

    bot.edit_message_text( chat_id=message.chat.id, message_id=message.message_id, text=f"👋 Добро пожаловать, {first_name}!\n\n"
             "<b>GROUP HELPER</b>, бот который поможет вам <b>легко и безопасно</b> управлять вашими группами!\n\n"
             "👉 <b>Добавьте меня в группу/супергруппу и сделайте меня Администратором</b>, чтобы я сразу же начал действовать!", parse_mode="HTML", reply_markup=markup)

# >>>>>>>>>>>>>>> БОТ БЕЗ ЭТОЙ ХУЙНИ НЕ РАБОТАЕТ ЛОЛ <<<<<<<<<<<<<<<

bot.polling(non_stop=True)
