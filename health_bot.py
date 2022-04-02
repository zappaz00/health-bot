import datetime
import telebot
import os
import logging
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone
from random import randint
import psycopg2
import atexit

DATABASE_URL = os.getenv('DATABASE_URL')

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('health.log', 'w', 'utf-8')
handler.setFormatter(logging.Formatter('%(name)s %(message)s'))
root_logger.addHandler(handler)

token = os.getenv("HEALTH_TOKEN")
bot = telebot.TeleBot(token)


class DbEngine:
    def __init__(self):
        self.db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.db_conn.autocommit = True
        atexit.register(self.cleanup)

    def reconnect(self):
        try:
            cur = self.db_conn.cursor()
            cur.execute('SELECT 1')
        except psycopg2.OperationalError:
            self.db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.db_conn.autocommit = True

    def get_cursor(self):
        self.reconnect()  # проверим живо ли соединение
        return self.db_conn.cursor()

    def cleanup(self):
        self.db_conn.close()


db_engine = DbEngine()


def exception_catcher(base_function):
    def new_function(*args,
                     **kwargs):  # This allows you to decorate functions without worrying about what arguments they take
        try:
            return base_function(*args, **kwargs)  # base_function is whatever function this decorator is applied to
        except Exception as e:
            date_time = datetime.now(timezone('Europe/Moscow'))
            date_str = date_time.strftime("%m/%d/%Y %H:%M:%S")
            err_msg = date_str + ': ' + base_function.__name__ + ' => ' + str(e)
            print(err_msg)
            root_logger.error(err_msg)

    return new_function


@exception_catcher
def init_db():
    cur = db_engine.get_cursor()
    # Create tables

    cur.execute('''CREATE TABLE IF NOT EXISTS user_levels
                (user_id bigint PRIMARY KEY, level integer, firstname text, username text);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_states
                (user_id bigint PRIMARY KEY, state integer, task_type text);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS achieves
                (achieve_id integer PRIMARY KEY, name text);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS levels
                (level integer PRIMARY KEY, name text);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS ratings
                (user_id bigint PRIMARY KEY, rating REAL);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS action_types
                (action_id integer PRIMARY KEY, name text);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS proof_types
                (proof_id integer PRIMARY KEY, name text);''')

    cur.execute('''INSERT INTO action_types(action_id, name) VALUES ('0', 'task') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO action_types(action_id, name) VALUES ('1', 'pass') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO action_types(action_id, name) VALUES ('2', 'force major') ON CONFLICT DO NOTHING;''')

    cur.execute('''INSERT INTO proof_types(proof_id, name) VALUES ('0', 'photo') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO proof_types(proof_id, name) VALUES ('1', 'video') ON CONFLICT DO NOTHING;''')

    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('0', 'Ранняя пташка') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('1', 'Дневная бабочка') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('2', 'Поздняя пташка') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('3', 'Ночная бабочка') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('4', 'Фотоохотник') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO achieves(achieve_id, name) VALUES ('5', 'Сам себе режиссёр') ON CONFLICT DO NOTHING;''')

    cur.execute('''INSERT INTO levels(level, name) VALUES ('0',  'Киберспортмен') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('1',  'Зелёный') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('2',  'Подтянутый') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('3',  'Фитоняш') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('4',  'Стальный мышцы') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('5',  'Мощный') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('6',  'Опытный боец') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('7',  'Победитель по жизни') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('8',  'Мастер') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('9',  'Гуру') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('10', 'Тибетский монах') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('11', 'Легендарный') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('12', 'Бесконечность не предел') ON CONFLICT DO NOTHING;''')
    cur.execute('''INSERT INTO levels(level, name) VALUES ('13', 'Спортивный маньяк') ON CONFLICT DO NOTHING;''')

    cur.execute('''CREATE TABLE IF NOT EXISTS activity
                (user_id bigint NOT NULL, date text, time text, action_id integer REFERENCES action_types(action_id), 
                proof_id integer REFERENCES proof_types(proof_id), chat_id bigint,
                UNIQUE(user_id,date) );''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_achieves
                (user_id bigint NOT NULL, achieve_id integer REFERENCES achieves(achieve_id),
                UNIQUE(user_id, achieve_id));''')

    root_logger.info('DB initialized')


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
    bot.reply_to(message, '/check - сдать тренировку\n' 
                          '/debt - отработать долг за вчера\n'
                          '/gift - узнать, кому дарить подарочек\n'
                          '/plan - получить задание\n'
                          '/start - начать\n'
                          '/stat - запросить свою статистику')


@exception_catcher
@bot.message_handler(commands=['check'])
def send_check(message):
    bot.send_chat_action(message.chat.id, 'typing')

    date_time = datetime.fromtimestamp(message.date, timezone('Europe/Moscow'))
    date_str = date_time.strftime("%m/%d/%Y")

    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={message.from_user.id} AND date='{date_str}';''')
    exist_activity = cur_thread.fetchone()
    if exist_activity is not None and len(exist_activity) != 0:
        bot.reply_to(message, 'Запись о твоей активности уже есть :)')
    else:
        cur_thread.execute(f'''INSERT INTO user_states VALUES ({message.from_user.id}, 1, 'check') 
                               ON CONFLICT (user_id) DO UPDATE SET 
                               state = EXCLUDED.state,
                               task_type = EXCLUDED.task_type;''')
        bot.reply_to(message, 'Просто загрузи фото или видео :)')


@exception_catcher
@bot.message_handler(commands=['debt'])
def send_debt(message):
    bot.send_chat_action(message.chat.id, 'typing')

    date_time = datetime.fromtimestamp(message.date, timezone('Europe/Moscow')) - timedelta(days=1)
    date_str = date_time.strftime("%m/%d/%Y")

    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={message.from_user.id} AND date='{date_str}';''')
    exist_activity = cur_thread.fetchone()
    if exist_activity is not None and len(exist_activity) != 0:
        bot.reply_to(message, 'Запись о твоей активности уже есть :)')
    else:
        cur_thread.execute(f'''INSERT INTO user_states VALUES ({message.from_user.id}, 1, 'debt') 
                               ON CONFLICT (user_id) DO UPDATE SET 
                               state = EXCLUDED.state,
                               task_type = EXCLUDED.task_type;''')
        bot.reply_to(message, 'Просто загрузи фото или видео :)')


@exception_catcher
def change_rating(user_id, change_val):
    filter_val = 0.01
    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT rating FROM ratings WHERE user_id={user_id};''')
    curr_rating = cur_thread.fetchone()
    if len(curr_rating) == 0:
        curr_rating = (1-filter_val) * 100 + filter_val * change_val
    else:
        curr_rating = (1-filter_val) * curr_rating[0] + filter_val * change_val

    curr_rating = min(max(curr_rating, 0), 100)
    cur_thread.execute(f'''INSERT INTO ratings VALUES ({user_id}, {curr_rating}) 
                           ON CONFLICT (user_id) DO UPDATE SET 
                           rating = EXCLUDED.rating;''')

    return curr_rating


@exception_catcher
@bot.message_handler(commands=['plan'])
def send_plan(message):
    bot.send_chat_action(message.chat.id, 'typing')
    gif_filenames = os.listdir('training')
    gif_perm = np.random.permutation(len(gif_filenames))
    for i in range(3):
        gif_file = open('training/' + gif_filenames[gif_perm[i]], 'rb')
        bot.send_animation(message.chat.id, gif_file, message.id)


@exception_catcher
@bot.message_handler(commands=['gift'])
def send_gift(message):
    bot.send_chat_action(message.chat.id, 'typing')

    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT DISTINCT user_id FROM activity WHERE user_id!={message.from_user.id} 
                       AND chat_id={message.chat.id}''')
    users_gift = cur_thread.fetchall()

    if users_gift is None or len(users_gift) == 0:
        bot.reply_to(message, 'Некому дарить подарочек(')
        return

    user_gift_id = randint(0, len(users_gift) - 1)
    user_gift_id = users_gift[user_gift_id][0]

    chat_member = bot.get_chat_member(message.chat.id, user_gift_id)
    bot.reply_to(message, f'Подарочек нужно подарить {chat_member.user.first_name} ({chat_member.user.username}) :)')


@exception_catcher
@bot.message_handler(commands=['stat'])
def send_stat(message):
    bot.send_chat_action(message.chat.id, 'typing')

    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={message.from_user.id} 
                                                    AND chat_id={message.chat.id} 
                                                    AND action_id=0''')
    user_stat = cur_thread.fetchall()
    if len(user_stat) == 0:
        bot.reply_to(message, 'Чтобы увидеть статистику загрузи свою первую тренировку!')
        return

    first_train = user_stat[0]
    last_train = user_stat[-1]

    if len(first_train) < 6 or len(last_train) < 6:
        return

    if first_train[1] is None or last_train[1] is None:
        return

    datetime_first = datetime.strptime(first_train[1], '%m/%d/%Y')
    datetime_last = datetime.strptime(last_train[1], '%m/%d/%Y')
    datetime_interval = int(str(datetime_last - datetime_first).split()[0])

    task_count = len(user_stat)
    pass_count = max(datetime_interval - task_count, 0)

    cur_thread.execute(f'''SELECT level FROM user_levels WHERE user_id={message.from_user.id}''')
    level_curr = cur_thread.fetchone()

    message_str = ''
    message_str = message_str + f'Кол-во занятий:      {task_count},\n'
    message_str = message_str + f'Кол-во пропусков:    {pass_count}'

    rating_curr = change_rating(message.from_user.id, 0) #чтоб избежать отсутствия рейтинга
    message_str = message_str + '\n' + f'Твой рейтинг: {rating_curr}'

    if level_curr is not None and len(level_curr) != 0:
        cur_thread.execute(f'''SELECT name FROM levels WHERE level={level_curr[0]}''')
        level_name = cur_thread.fetchone()
        message_str = message_str + '\n' + f'Твой уровень: {level_curr[0]}'
        if level_name is not None and len(level_name) != 0:
            message_str = message_str + f' ({level_name[0]})'

    cur_thread.execute(f'''SELECT name FROM user_achieves INNER JOIN achieves 
                        ON user_achieves.achieve_id=achieves.achieve_id AND user_id={message.from_user.id}''')
    user_achieves = cur_thread.fetchall()

    for user_achieve in user_achieves:
        message_str = message_str + '\n' + f'Есть достижение: {user_achieve[0]}'

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

    chat_member = bot.get_chat_member(chat_id, user_id)

    cur_thread.execute(f'''SELECT name FROM levels WHERE level={calc_level}''')
    level_name = cur_thread.fetchone()

    cur_thread.execute(f'''SELECT level FROM user_levels WHERE user_id={user_id}''')
    level_curr = cur_thread.fetchone()
    cur_thread.execute(f'''INSERT INTO user_levels VALUES ({user_id}, {calc_level}) 
                       ON CONFLICT (user_id) DO UPDATE SET 
                       level = EXCLUDED.level, 
                       firstname = '{chat_member.user.first_name}', 
                       username = '{chat_member.user.username}';''')

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
        if achieve_counts[achieve_ctr] >= 20:
            cur_thread.execute(f'''SELECT * FROM user_achieves WHERE user_id={user_id} AND achieve_id={achieve_ctr}''')
            achieve_existed = cur_thread.fetchone()
            if achieve_existed is not None:
                continue

            try:
                cur_thread.execute(f'''INSERT INTO user_achieves VALUES ({user_id},'{achieve_ctr}') 
                                   ON CONFLICT DO NOTHING''')
                cur_thread.execute(f'''SELECT name FROM achieves WHERE achieve_id={achieve_ctr}''')
                achieve_name = cur_thread.fetchone()
                if achieve_name is not None and len(achieve_name) > 0:
                    achieve_str += f'Достижение: {achieve_name[0]}\n'

            except psycopg2.IntegrityError:
                root_logger.error('Achieve already exists!')

    return achieve_str


@exception_catcher
@bot.message_handler(content_types=['photo', 'video'])
def get_media_messages(message):

    cur_thread = db_engine.get_cursor()
    cur_thread.execute(f'''SELECT * FROM user_states WHERE user_id={message.from_user.id};''')
    user_state = cur_thread.fetchone()

    if user_state is None or (len(user_state) != 0 and user_state[1] != 1):
        return

    cur_thread.execute(f'''SELECT * FROM activity WHERE user_id={message.from_user.id} 
                                                    AND chat_id={message.chat.id} 
                                                    ORDER BY date DESC LIMIT 1''')

    user_last_activity = cur_thread.fetchone()
    date_time_last = datetime.strptime(user_last_activity[1], "%m/%d/%Y")
    date_time_req = datetime.fromtimestamp(message.date, timezone('Europe/Moscow')) - timedelta(days=1)

    cur_thread.execute(f'''INSERT INTO user_states VALUES ({message.from_user.id}, 0) 
                           ON CONFLICT (user_id) DO UPDATE SET 
                           state = EXCLUDED.state,
                           task_type = EXCLUDED.task_type;''')

    bot.send_chat_action(message.chat.id, 'typing')
    if message.photo is None and message.video is None:
        bot.reply_to(message, 'Неправильный формат, попробуй ещё раз :)')
        return
    else:
        cur_thread = db_engine.get_cursor()
        date_time = datetime.fromtimestamp(message.date, timezone('Europe/Moscow'))

        if user_state[2] == 'debt':
            date_time = date_time - timedelta(days=1)

        date_time_req = date_time - timedelta(days=1)

        date_str = date_time.strftime("%m/%d/%Y")
        time_str = date_time.strftime("%H:%M:%S")

        proof_name = ''
        if message.photo is not None:
            proof_name = 'photo'
        elif message.video is not None:
            proof_name = 'video'
        cur_thread.execute(f'''SELECT proof_id FROM proof_types WHERE name='{proof_name}' LIMIT 1''')
        proof_id = cur_thread.fetchone()

        if proof_id is not None and len(proof_id) == 1:
            try:
                cur_thread.execute(
                    f'''INSERT INTO activity VALUES ({message.from_user.id},'{date_str}','{time_str}',{0},
                    {proof_id[0]},{message.chat.id})''')
            except psycopg2.IntegrityError:
                root_logger.error('Record already added')
                return

        bot.reply_to(message, f'Умничка, {message.from_user.first_name}, засчитано!')
        change_rating(message.from_user.id, +1)

        achieve_name = give_achieve(message.from_user.id, message.chat.id, cur_thread)
        if achieve_name is not None and len(achieve_name) > 0:
            bot.reply_to(message, f'{message.from_user.first_name}, лэвэл ап! Так держать!')
            bot.reply_to(message, f'{achieve_name}')

            sticker_filenames = os.listdir('stickers')
            sticker_number = randint(0, len(sticker_filenames) - 1)
            sticker = open('stickers/' + sticker_filenames[sticker_number], 'rb')
            bot.send_sticker(message.chat.id, sticker, message.id)

    if date_time_last != date_time_req:
        bot.reply_to(message, 'Похоже ты пропустил занятие, друг мой)) Подари подарок!)')
        send_gift(message)
        change_rating(-1)


init_db()
bot.polling(none_stop=True)
