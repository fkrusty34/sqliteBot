import sqlite3
from telebot import types

from config import bot, ver


@bot.message_handler(commands=["start"])
def start(message):
    con = sqlite3.connect("pd.db")
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INT,
        name TEXT,
        rules INT
    )""")

    con.commit()

    id = message.chat.id
    name = message.chat.first_name + (" " + message.chat.last_name if message.chat.last_name is not None else "")

    cur.execute("SELECT id FROM users WHERE id = ?", (id,))
    res = cur.fetchone()

    if res is None:
        cur.execute("INSERT INTO users VALUES (?, ?, 0)", (id, name))
        con.commit()
        bot.send_message(message.chat.id, "Регистрация прошла успешно!")
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы")

    bot.send_message(message.chat.id, "Напишите /help для вывода справки")

    con.close()


@bot.message_handler(commands=["users"])
def users(message):
    con = sqlite3.connect("pd.db")
    cur = con.cursor()

    cur.execute("SELECT rules FROM users WHERE id = ?", (message.chat.id,))
    res = cur.fetchone()

    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("Изменить привилегии", callback_data="change_rules")]
    ])

    if res[0] > 0:
        cur.execute("SELECT * FROM users")
        text = "<b>Пользователи:</b>"\
               "\n(id, name, rules)"

        for i in cur.fetchall():
            text += f"\n(<code>{i[0]}</code>, {i[1]}, {i[2]})"

        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас недостаточно привилегий")

    con.close()


@bot.message_handler(commands=["change_status"])
def change_status(message):
    msg = bot.send_message(message.chat.id, "Введите пароль желаемых привилегий")
    bot.register_next_step_handler(msg, chk_pass)


def chk_pass(message):
    con = sqlite3.connect("data.db")
    cur = con.cursor()

    cur.execute("SELECT rules FROM rules WHERE password = ?", (message.text,))
    res = cur.fetchone()

    con.close()

    con = sqlite3.connect("pd.db")
    cur = con.cursor()

    cur.execute("SELECT rules FROM users WHERE id = ?", (message.chat.id,))

    if res is not None:
        res += cur.fetchone()

    if res is not None and res[0] != res[1]:
        cur.execute("UPDATE users SET rules = ? WHERE id = ?", (res[0], message.chat.id))
        con.commit()
        bot.send_message(message.chat.id, f"Успешно! Проверить /status")
    elif res is not None and res[0] == res[1]:
        bot.send_message(message.chat.id, "Ошибка: у вас уже имеются выбранные привилегии")
    else:
        bot.send_message(message.chat.id, "Ошибка: неверный пароль")

    con.close()


@bot.message_handler(commands=["status"])
def status(message):
    con = sqlite3.connect("pd.db")
    cur = con.cursor()

    cur.execute("SELECT rules FROM users WHERE id = ?", (message.chat.id,))
    res = cur.fetchone()

    con.close()

    con = sqlite3.connect("data.db")
    cur = con.cursor()

    cur.execute("SELECT description FROM rules WHERE rules = ?", (res[0],))
    res += cur.fetchone()

    bot.send_message(message.chat.id, f"{res[0]} ({res[1]})")

    con.close()


@bot.message_handler(commands=["help"])
def helping(message):
    bot.send_message(message.chat.id, f"Версия бота {ver}"
                                      "\nРепозиторий на GitHub: <a href='github.com/fkrusty34/sqliteBot'>link</a>"
                                      "\n<b>Команды:</b>"
                                      "\n/start - старт"
                                      "\n/help - помощь"
                                      "\n/status - ваши привилегии"
                                      "\n/change_status - сменить привилегии"
                                      "\n/users - пользователи", parse_mode="HTML", disable_web_page_preview=True)


@bot.message_handler(commands=["py"])
def py(message):
    bot.send_message(message.chat.id, "<pre><code class='language-python'>print('Hello world!')</code></pre>",
                     parse_mode="HTML")


@bot.message_handler(content_types=["text"])
def not_recognized(message):
    bot.send_message(message.chat.id, "Я понимаю только команды и лишь иногда обычнй текст :( "
                                      "\nесли хочешь что-то сказать, напиши моему хозяину @magkryak", parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "change_rules":
        msg = bot.send_message(call.message.chat.id, "Введите id пользователя и привилегии в формате"
                                                     "\n<code>id rules</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, change_rules)

    bot.answer_callback_query(call.id)


def change_rules(message):
    pars = list(message.text.split())

    con = sqlite3.connect("pd.db")
    cur = con.cursor()

    cur.execute("SELECT id FROM users WHERE id = ?", (pars[0],))
    res = cur.fetchone()

    if res is not None:
        cur.execute("SELECT rules FROM users WHERE id = ?", (message.chat.id,))
        res += cur.fetchone()
    else:
        bot.send_message(message.chat.id, "Ошибка: некорректный id")
        con.close()
        return

    if len(res) == 2 and pars[0].isdigit() and res[0] != int(message.chat.id):
        if pars[1].isdigit() and 0 <= int(pars[1]) <= min(4, res[1]):
            cur.execute("UPDATE users SET rules = ? WHERE id = ?", (pars[1], res[0]))
            con.commit()
            bot.send_message(message.chat.id, "Успешно! /users")
        else:
            bot.send_message(message.chat.id, f"Ошибка: ожидается число в диапазоне от 0 до {min(4, res[1])}")

    else:
        bot.send_message(message.chat.id, "Ошибка: некорректный id")

    con.close()


bot.infinity_polling()
