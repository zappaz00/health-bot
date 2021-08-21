import datetime
import telebot
import os
import logging
from telebot import types
from datetime import datetime
from random import randint
import sqlite3

db_name = 'Health.db'

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('health.log', 'w', 'utf-8')
handler.setFormatter(logging.Formatter('%(name)s %(message)s'))
root_logger.addHandler(handler)

token = os.getenv("HEALTH_TOKEN")
bot = telebot.TeleBot(token)


def exception_catcher(base_function):
    def new_function(*args,
                     **kwargs):  # This allows you to decorate functions without worrying about what arguments they take
        try:
            return base_function(*args, **kwargs)  # base_function is whatever function this decorator is applied to
        except Exception as e:
            date_time = datetime.now()
            date_str = date_time.strftime("%m/%d/%Y %H:%M:%S")
            err_msg = date_str + ': ' + base_function.__name__ + ' => ' + str(e)
            print(err_msg)
            root_logger.error(err_msg)

    return new_function


@exception_catcher
def init_db():
    db_conn = sqlite3.connect(db_name)
    cur = db_conn.cursor()
    # Create tables
    cur.execute('''PRAGMA busy_timeout = 10000''')
    cur.execute('''PRAGMA foreign_keys = OFF''')

    cur.execute('''CREATE TABLE IF NOT EXISTS activity
                (user_id integer NOT NULL, date text, time text, action_id REFERENCES action_types(action_id), proof_id 
                REFERENCES proof_types(proof_id), chat_id integer,
                UNIQUE(user_id,date) )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_achieves
                (user_id integer NOT NULL, achieve_id REFERENCES achieves(achieve_id),
                UNIQUE(user_id, achieve_id))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_levels
                (user_id integer PRIMARY KEY, level integer)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS achieves
                (achieve_id integer PRIMARY KEY, name text)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS levels
                (level integer PRIMARY KEY, name text)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS action_types
                (action_id integer PRIMARY KEY, name text)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS proof_types
                (proof_id integer PRIMARY KEY, name text)''')

    cur.execute('''INSERT OR IGNORE INTO action_types(action_id, name) VALUES ('0', 'task')''')
    cur.execute('''INSERT OR IGNORE INTO action_types(action_id, name) VALUES ('1', 'pass')''')
    cur.execute('''INSERT OR IGNORE INTO action_types(action_id, name) VALUES ('2', 'force major')''')

    cur.execute('''INSERT OR IGNORE INTO proof_types(proof_id, name) VALUES ('0', 'photo')''')
    cur.execute('''INSERT OR IGNORE INTO proof_types(proof_id, name) VALUES ('1', 'video')''')

    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('0', 'Ранняя пташка')''')
    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('1', 'Дневная бабочка')''')
    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('2', 'Поздняя пташка')''')
    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('3', 'Ночная бабочка')''')
    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('4', 'Фотоохотник')''')
    cur.execute('''INSERT OR IGNORE INTO achieves(achieve_id, name) VALUES ('5', 'Сам себе режиссёр')''')

    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('0',  'Киберспортмен')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('1',  'Зелёный')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('2',  'Подтянутый')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('3',  'Фитоняш')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('4',  'Стальный мышцы')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('5',  'Мощный')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('6',  'Опытный боец')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('7',  'Победитель по жизни')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('8',  'Мастер')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('9',  'Гуру')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('10', 'Тибетский монах')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('11', 'Легендарный')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('12', 'Бесконечность не предел')''')
    cur.execute('''INSERT OR IGNORE INTO levels(level, name) VALUES ('13', 'Спортивный маньяк')''')

    root_logger.info('DB initialized')

    cur.execute('''PRAGMA foreign_keys = ON''')

    db_conn.commit()
    db_conn.close()


@exception_catcher
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, f'Я твой личный помощник. Приятно познакомиться, {message.from_user.first_name}. '
                          f'Для ознакомления с функционалом выполни /help')


@exception_catcher
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, '/start - начать\n'
                          '/pass - пропустить\n'
                          '/stat - запросить свою статистику\n'
                          '/gift - узнать, кому дарить подарочек\n\n'
                          'Чтобы сдать упражнение загрузи фото или видео с подписью "check"')


@exception_catcher
@bot.message_handler(content_types=['photo', 'video'])
def send_check(message):
    bot.send_chat_action(message.chat.id, 'typing')
    get_media_messages(message)


@exception_catcher
@bot.message_handler(commands=['pass'])
def send_pass(message):
    reply_markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton('Лениво/забыл', callback_data='procrastinate')
    itembtn2 = types.InlineKeyboardButton('Форс-Мажор', callback_data='force_major')
    reply_markup.row(itembtn1, itembtn2)

    bot.reply_to(message, 'Что случилось?', reply_markup=reply_markup)


@exception_catcher
@bot.message_handler(commands=['gift'])
def send_gift(message):
    bot.send_chat_action(message.chat.id, 'typing')

    db_conn = sqlite3.connect(db_name)
    cur_thread = db_conn.cursor()
    cur_thread.execute(f'''SELECT DISTINCT user_id FROM activity WHERE user_id!={message.from_user.id} 
                       AND chat_id={message.chat.id}''')
    users_gift = cur_thread.fetchall()

    if users_gift is None or len(users_gift) == 0:
        bot.reply_to(message, 'Некому дарить подарочек(')
        return

    user_gift_id = randint(0, len(users_gift) - 1)
    user_gift_id = users_gift[user_gift_id][0]

    db_conn.commit()
    db_conn.close()

    chat_member = bot.get_chat_member(message.chat.id, user_gift_id)
    bot.reply_to(message, f'Подарочек нужно подарить {chat_member.user.first_name} ({chat_member.user.username}) :)')


@exception_catcher
@bot.callback_query_handler(func=lambda call: True)
def pass_button(call):
    if call is None:
        return

    bot.send_chat_action(call.message.chat.id, 'typing')

    date_time = datetime.fromtimestamp(call.message.date)
    date_str = date_time.strftime("%m/%d/%Y")
    time_str = date_time.strftime("%H:%M:%S")
    db_conn = sqlite3.connect(db_name)
    cur_thread = db_conn.cursor()

    if call.data == "procrastinate":
        cur_thread.execute(f'''SELECT action_id FROM action_types WHERE name='pass' LIMIT 1''')
        action_id = cur_thread.fetchone()
    else:
        cur_thread.execute(f'''SELECT action_id FROM action_types WHERE name='force major' LIMIT 1''')
        action_id = cur_thread.fetchone()

    if action_id is not None and len(action_id) == 1:
        try:
            cur_thread.execute(
                f'''INSERT INTO activity VALUES ({call.from_user.id},'{date_str}','{time_str}',{action_id[0]},
                NULL,{call.message.chat.id})''')

            if call.data == "procrastinate":
                bot.send_message(call.message.chat.id, f'О нет! {call.from_user.first_name} покупает подарочек!'
                                                       f'Используй /gift, чтоб узнать кому дарить')
            else:
                bot.send_message(call.message.chat.id,
                                 f'У Пети болит, у Маши болит, а у {call.from_user.first_name} не болит!')
        except sqlite3.IntegrityError:
            root_logger.error('Record already added')

    db_conn.commit()
    db_conn.close()

    bot.delete_message(call.message.chat.id, call.message.id)


@exception_catcher
@bot.message_handler(commands=['stat'])
def send_stat(message):
    bot.send_chat_action(message.chat.id, 'typing')

    db_conn = sqlite3.connect(db_name)
    cur_thread = db_conn.cursor()
    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={message.from_user.id} AND chat_id={message.chat.id}''')
    user_stat = cur_thread.fetchall()
    if len(user_stat) == 0:
        bot.reply_to(message, 'Чтобы увидеть статистику загрузи свою первую тренировку!')
        return

    cur_thread.execute(f'''SELECT * FROM action_types''')
    action_types = cur_thread.fetchall()

    actions_count = {}
    for record in user_stat:
        if len(record) < 6 or record[3] is None:
            continue

        if actions_count.get(record[3]) is None:
            actions_count[record[3]] = 0

        actions_count[record[3]] += 1

    pass_count = 0
    task_count = 0
    force_major_count = 0
    for action_type in action_types:
        if actions_count.get(action_type[0]) is not None:
            if action_type[1] == 'task':
                task_count = actions_count[action_type[0]]
            elif action_type[1] == 'pass':
                pass_count = actions_count[action_type[0]]
            elif action_type[1] == 'force major':
                force_major_count = actions_count[action_type[0]]

    cur_thread.execute(f'''SELECT level FROM user_levels WHERE user_id={message.from_user.id}''')
    level_curr = cur_thread.fetchone()

    message_str = f'''Кол-во занятий: {task_count},\n
    Кол-во пропусков: {pass_count},\n
    Кол-во форс-мажоров: {force_major_count}'''

    if level_curr is not None and len(level_curr) != 0:
        cur_thread.execute(f'''SELECT name FROM levels WHERE level={level_curr[0]}''')
        level_name = cur_thread.fetchone()
        message_str = message_str + '\n' + f'Твой уровень: {level_curr[0]}'
        if level_name is not None and len(level_name) != 0:
            message_str = message_str + f' ({level_name[0]})'

    db_conn.commit()
    db_conn.close()

    bot.reply_to(message, message_str)


@exception_catcher
def give_achieve(user_id, chat_id, cur_thread):
    # выясним какое достижение можно выдать
    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={user_id} AND action_id=0 AND chat_id={chat_id};''')
    tasks = cur_thread.fetchall()
    level_step = 30  # month
    calc_level = int(len(tasks) / level_step)

    if len(tasks) == 0:
        return ''

    cur_thread.execute(f'''SELECT name FROM levels WHERE level={calc_level}''')
    level_name = cur_thread.fetchone()

    cur_thread.execute(f'''SELECT level FROM user_levels WHERE user_id={user_id}''')
    level_curr = cur_thread.fetchone()
    cur_thread.execute(f'''INSERT OR REPLACE INTO user_levels VALUES ({user_id},'{calc_level}')''')

    achieve_str = ''
    if level_curr is None or (len(level_curr) > 0 and level_curr[0] != calc_level):
        if level_name is None:
            achieve_str = f'Уровень {calc_level}\n'
        elif len(level_name) > 0:
            achieve_str = f'Уровень {calc_level} : {level_name[0]}\n'

    achieve_counts = [0, 0, 0, 0, 0, 0]

    for task in tasks:
        if task is None or len(task) < 6:
            continue

        if '04:00:00' < task[2] <= '11:00:00':
            achieve_counts[0] += 1
        elif '11:00:00' < task[2] <= '15:00:00':
            achieve_counts[1] += 1
        elif '15:00:00' < task[2] <= '23:00:00':
            achieve_counts[2] += 1
        elif '23:00:00' < task[2] <= '04:00:00':
            achieve_counts[3] += 1

        if task[4] == 0:
            achieve_counts[4] += 1
        elif task[4] == 1:
            achieve_counts[5] += 1

    for achieve_ctr in range(len(achieve_counts)):
        if achieve_counts[achieve_ctr] == 20:
            try:
                cur_thread.execute(f'''INSERT OR REPLACE INTO user_achieves VALUES ({user_id},'{achieve_ctr}')''')
                cur_thread.execute(f'''SELECT name FROM achieves WHERE achieve_id={achieve_ctr}''')
                achieve_name = cur_thread.fetchone()
                if achieve_name is not None and len(achieve_name) > 0:
                    achieve_str += f'Достижение: {achieve_name[0]}\n'

            except sqlite3.IntegrityError:
                root_logger.error('Achieve already exists!')

    return achieve_str


@exception_catcher
def get_media_messages(message):
    if message.caption.lower() != 'check':
        return

    bot.send_chat_action(message.chat.id, 'typing')
    if message.photo is None and message.video is None:
        bot.reply_to(message, 'Загрузи фото/видео')
    else:
        db_conn = sqlite3.connect(db_name)
        cur_thread = db_conn.cursor()
        date_time = datetime.fromtimestamp(message.date)
        date_str = date_time.strftime("%m/%d/%Y")
        time_str = date_time.strftime("%H:%M:%S")
        cur_thread.execute(f'''SELECT action_id FROM action_types WHERE name='task' LIMIT 1''')
        action_id = cur_thread.fetchone()

        proof_name = ''
        if message.photo is not None:
            proof_name = 'photo'
        elif message.video is not None:
            proof_name = 'video'
        cur_thread.execute(f'''SELECT proof_id FROM proof_types WHERE name='{proof_name}' LIMIT 1''')
        proof_id = cur_thread.fetchone()

        if proof_id is not None and len(proof_id) == 1 and action_id is not None and len(action_id) == 1:
            try:
                cur_thread.execute(
                    f'''INSERT INTO activity VALUES ({message.from_user.id},'{date_str}','{time_str}',{action_id[0]},
                    {proof_id[0]},{message.chat.id})''')
            except sqlite3.IntegrityError:
                root_logger.error('Record already added')
                db_conn.commit()
                db_conn.close()
                return

        bot.reply_to(message, f'Умничка, {message.from_user.first_name}, засчитано!')
        achieve_name = give_achieve(message.from_user.id, message.chat.id, cur_thread)
        if achieve_name is not None and len(achieve_name) > 0:
            bot.reply_to(message, f'{message.from_user.first_name}, лэвэл ап! Так держать!')
            bot.reply_to(message, f'{achieve_name}')

            sticker_filenames = os.listdir('stickers')
            sticker_number = randint(0, len(sticker_filenames) - 1)
            sticker = open('stickers/' + sticker_filenames[sticker_number], 'rb')
            bot.send_sticker(message.chat.id, sticker, message.id)

        db_conn.commit()
        db_conn.close()


init_db()
bot.polling(none_stop=True)
