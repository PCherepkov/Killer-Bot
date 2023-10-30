import os
import pickle
import random

import telebot.types

from defin import *

password = "here was password"


@Bot.bot.message_handler(commands=['start'])
def start(message):
    from_user = message.from_user
    if len(Bot.chain) > 0:
        Bot.bot.send_message(from_user.id, "Регистрация закрыта. Игра уже идёт")
        return
    if from_user.username is None:
        Bot.bot.send_message(from_user.id, "Пожалуйста, установите юзернейм и нажмите /start ещё раз")
        return
    if Bot.get(from_user.username) is not None:
        return
    print(from_user.username)
    if Bot.contains(from_user.username):
        return
    markup = telebot.types.ReplyKeyboardMarkup(True)
    markup.row('Регистрация')
    Bot.bot.send_message(message.from_user.id, "Привет, " + from_user.first_name + "!", reply_markup=markup)


def set_info(message):
    user = message.from_user
    if len(Bot.chain) > 0:
        Bot.bot.send_message(user.id, "Игра уже началась. Вы не успели зарегистрироваться.")
        return
    if message.text is None:
        msg = Bot.bot.send_message(message.from_user.id, "Неверный формат. Попробуйте ещё раз\n(_пример: Пётр Черепков 1 курс_)", parse_mode='markdown')
        Bot.bot.register_next_step_handler(msg, set_info)
        return
    args = message.text.split()
    if message.text == password:
        Bot.admins[user.id] = Admin(user.first_name, user.username, user.id)
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Список игроков')
        markup.row('Профиль игрока')
        markup.row('Цепочка')
        Bot.bot.send_message(message.from_user.id, 'Вход выполнен', reply_markup=markup)
        with open("admins", "wb") as a_bin:
            pickle.dump(Bot.admins, a_bin, protocol=pickle.HIGHEST_PROTOCOL)
        return
    if len(args) < 3 or not args[2].isnumeric() or int(args[2]) > 6 or int(args[2]) < 1:
        msg = Bot.bot.send_message(message.from_user.id, "Неверный формат. Попробуйте ещё раз\n(_пример: Пётр Черепков 1 курс_)", parse_mode='markdown')
        Bot.bot.register_next_step_handler(msg, set_info)
        return
    name, surname, course = args[0], args[1], str(int(args[2]))
    if user.id not in Bot.players.keys():
        Bot.players[user.id] = Player(user.first_name, user.username, user.id)
    Bot.players[user.id].info.name = name
    Bot.players[user.id].info.surname = surname
    Bot.players[user.id].info.course = course
    msg = Bot.bot.send_message(user.id, "Теперь отправьте своё фото.\nПараметры фотографии:\n• во всех смыслах четкая\n• на фото только Вы \n• лицо крупно и в анфас, не закрыто руками/волосами \n• Вы узнаваемы \n• адекватное выражение лица")
    Bot.bot.register_next_step_handler(msg, register)
def set_code(message):
    user = message.from_user
    if len(Bot.chain) > 0:
        Bot.bot.send_message(user.id, "Игра уже началась. Вы не успели зарегистрироваться.")
        return
    Bot.players[message.from_user.id].code = message.text
    if message.text is None:
        msg = Bot.bot.send_message(message.from_user.id, "Код не принят. Введите текстовый код")
        Bot.bot.register_next_step_handler(msg, set_code)
        return
    markup = telebot.types.ReplyKeyboardMarkup(True)
    markup.row('Профиль')
    Bot.bot.send_message(message.from_user.id, "Регистрация пройдена успешно", reply_markup=markup)
    Bot.players[message.from_user.id].verified = 2
    with open("players", "wb") as p_bin:
        pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
@Bot.bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data.split()
    player = Bot.get(data[1])
    if player is None or len(Bot.chain) > 0:
        # отправляешь, если player is None... Такая ты молодец, конечно
        Bot.bot.send_message(player.id, "Игра уже началась. Вы не успели зарегистрироваться.")
        return
    if data[0] == '1':
        if player.verified == 1 and player.photo > int(data[2]):
            Bot.bot.answer_callback_query(call.id, "Эта анкета уже отклонена")
            return
        if player.verified == 2:
            Bot.bot.answer_callback_query(call.id, "У игрока уже есть одобренная анкета")
            return
        msg = Bot.bot.send_message(player.id, "Анкета успешно прошла проверку. Теперь придумайте свой уникальный код и отправьте его", reply_markup=None)
        Bot.bot.register_next_step_handler(msg, set_code)
    elif data[0] == '0':
        if player.verified == 1 and player.photo > int(data[2]):
            Bot.bot.answer_callback_query(call.id, "Эта анкета уже отклонена")
            return
        if player.verified == 2:
            Bot.bot.answer_callback_query(call.id, "У игрока уже есть одобренная анкета")
            return
        Bot.players[player.id].verified = 1
        Bot.players[player.id].photo += 1
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Регистрация')
        msg = Bot.bot.send_message(player.id, "Анкета не прошла модерацию. Пройдите регистрацию заново", reply_markup=markup)


def register(message):
    user = message.from_user
    if isinstance(message.photo, list):
        photo_id = message.photo[-1].file_id
        photo_info = Bot.bot.get_file(photo_id)
        photo_path = photo_info.file_path
        photo = Bot.bot.download_file(photo_path)
        f = open("photos/" + user.username + '.jpg', 'wb')
        f.write(photo)
        f.close()
        for admin in Bot.admins:
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            accept = telebot.types.InlineKeyboardButton('✔', callback_data='1 ' + user.username + ' ' + str(Bot.players[user.id].photo))
            decline = telebot.types.InlineKeyboardButton('❌', callback_data='0 ' + user.username + ' ' + str(Bot.players[user.id].photo))
            keyboard.add(accept, decline)
            try:
                with open("photos/" + user.username + '.jpg', 'rb') as f:
                    Bot.bot.send_photo(admin, f, reply_markup=keyboard, caption=f'@{user.username}\n{Bot.players[user.id].info}')
            except Exception as e:
                print('error:' + str(e.args))
                print('cause:', admin, 'on user', user.username)
        Bot.bot.reply_to(message, 'Анкета отправлена на проверку')
        Bot.players[message.from_user.id].verified = 0
    else:
        msg = Bot.bot.send_message(user.id, "С фото что-то не так. Отправьте другое")
        Bot.bot.register_next_step_handler(msg, register)


def give_name(message):
    player = Bot.get(message.text)
    if player is None or player.id in Bot.admins:
        Bot.bot.send_message(message.from_user.id, "Нет игрока с таким юзернеймом")
        return
    Bot.admins[message.from_user.id].check_player(id=player.id)


def enter_code(message):
    user = message.from_user
    correct = (message.text == Bot.get(Bot[user.id].victim).code)
    Bot.players[user.id].tries += 1 - correct
    if correct:
        Bot.kill(Bot.get(Bot.players[user.id].victim).id)
        if len(Bot.chain) < 2:
            return
        with open('chain', 'wb') as c_bin:
            pickle.dump(Bot.chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
        sc_store(Bot.scheduler)
        with open('players', 'wb') as p_bin:
            pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Профиль')
        markup.row('Жертва')
        markup.row('Написать убийце')
        markup.row('Написать жертве')
        markup.row('Ввести код убитого')
        with open("photos/" + Bot.players[user.id].victim + '.jpg', 'rb') as photo:
            info = str(Bot.get(Bot.players[user.id].victim).info).replace('_', '\\_')
            Bot.bot.send_photo(user.id, photo, caption=f'Игрок убит. Вот новая жертва\n*{info}*', reply_markup=markup, parse_mode= 'Markdown')
    else:
        if Bot.players[user.id].tries == 3:
            Bot.kill(user.id)
            with open('chain', 'wb') as c_bin:
                pickle.dump(Bot.chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
            sc_store(Bot.scheduler)
            with open('players', 'wb') as p_bin:
                pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
        elif Bot.players[user.id].tries == 2:
            Bot.bot.send_message(user.id, "Код введён неверно. Осталась последняя попытка (нажмите кнопку ещё раз)")
        else:
            Bot.bot.send_message(user.id, "Код введён неверно. Осталось 2 попытки (нажмите кнопку ещё раз)")
    with open("players", "wb") as p_bin:
        pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)


def tell_media(sender: int, recipient: int, relation: str, marked: bool):
    media = Bot.players[sender].media
    photo = media['photo'] # list(map(telebot.types.InputMediaPhoto, media['photo']))
    audio = media['audio'] # list(map(telebot.types.InputMediaAudio, media['audio']))
    video = media['video'] # list(map(telebot.types.InputMediaVideo, media['video']))
    dcmnt = media['document'] # list(map(telebot.types.InputMediaDocument, media['document']))

    # media_group = photo + audio + video + dcmnt
    # if len(media_group) == 0:
    #     return
    try:
        if not marked:
            Bot.bot.send_message(recipient, f"Новое сообщение от {relation}")
        for p in photo:
            Bot.bot.send_photo(recipient, p)
        for a in audio:
            Bot.bot.send_audio(recipient, a)
        for v in video:
            Bot.bot.send_video(recipient, v)
        for d in dcmnt:
            Bot.bot.send_document(recipient, d)
    except Exception as e:
        print("EXCEPTION:", e)
        Bot.bot.send_message(sender, "Сообщение не было доставлено")
    Bot.players[sender].clear_media()


def tell(message, args: list):
    id, sender, cnt = args[0], args[1], args[2]
    if message is None:
        print(len(Bot.players[args[3]].media['photo']))
        tell_media(args[3], id, f"{sender.lower()[:-1]}ы", False)
        return
    elif cnt == 2:
        tell_media(message.from_user.id, id, f"{sender.lower()[:-1]}ы", False)
        return
    if isinstance(message.photo, list):
        Bot.players[message.from_user.id].media['photo'].append(Bot.bot.download_file(Bot.bot.get_file(message.photo[-1].file_id).file_path))
    if message.audio is not None:
        Bot.players[message.from_user.id].media['audio'].append(Bot.bot.download_file(Bot.bot.get_file(message.audio.file_id).file_path))
    if message.document is not None:
        Bot.players[message.from_user.id].media['document'].append(Bot.bot.download_file(Bot.bot.get_file(message.document.file_id).file_path))
    if message.video is not None:
        Bot.players[message.from_user.id].media['video'].append(Bot.bot.download_file(Bot.bot.get_file(message.video.file_id).file_path))
    if message.text is not None:
        text = sender + ' пишет:\n_\"' + message.text.replace('_', '\\_') + '\"_'
        Bot.bot.send_message(id, text, parse_mode='markdown')
    if message.sticker is not None:
        sticker = Bot.bot.download_file(Bot.bot.get_file(message.sticker.file_id).file_path)
        Bot.bot.send_message(id, f"Стикер от {sender.lower()[:-1]}ы")
        Bot.bot.send_sticker(id, sticker)

    if message.media_group_id is not None:
        Bot.bot.send_message(message.from_user.id, "Не более одного медиафайла за раз.\n_(нажмите кнопку ещё раз)_", parse_mode='markdown')
        return
        # Bot.bot.register_next_step_handler(message, tell, args=[id, sender, cnt + 1])
        # Bot.scheduler.add_job(id=f"tell {id}", func=tell, trigger='date',
        #                         run_date=datetime.now() + timedelta(seconds=3),
        #                         args=[None, [id, sender, -1, message.from_user.id]])
        # Bot.bot.send_message(message.from_user.id, "Можно отправлять только текст. _(нажмите кнопку ещё раз)_", parse_mode='markdown')
        # return
    Bot.bot.send_message(message.from_user.id, "Сообщение отправлено")
    if message.media_group_id is None:
        tell_media(message.from_user.id, id, f"{sender.lower()[:-1]}ы", message.text is not None)
        if cnt > 0:
            Bot.scheduler.remove_job(f"tell {id}")


@Bot.bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user = message.from_user

    bot_user = Bot.get(user.username)
    if bot_user is not None and bot_user.id <= 0:
        bot_user = Bot.players.pop(bot_user.id)
        bot_user.id = user.id
        Bot.players[user.id] = bot_user
        Bot.scheduler.modify_job(user.username, "default", args=[user.id])

    """
    if user.id in Bot.players and Bot.get(user.username) is None:
        for killer in Bot.players.values():
            pass
    """

    if user.id in Bot.players and Bot.players[user.id].verified == 0:
        Bot.bot.send_message(message.from_user.id, "Дождитесь проверки анкеты")
        return
    if message.text == "Регистрация":
        if user.id in Bot.players and Bot.players[user.id].verified == 2:
            Bot.bot.send_message(message.from_user.id, "Вы уже зарегестрированы")
            return
        Bot.bot.send_message(message.from_user.id,
                                   "Введите имя, фамилию и номер курса через пробел\n_(первому и второму курсу магистратуры соотвествуют 5 и 6 курсы)_",
                                   parse_mode="markdown")
        Bot.bot.register_next_step_handler(message, set_info)
        return
    if user.id in Bot.admins and message.text == "Начать":
        for player in list(Bot.players.keys()):
            if Bot.players[player].verified != 2:
                Bot.players.pop(player)
        Bot.chain = shuffle(list(Bot.players.values()))
        for p in Bot.chain:
            player = Bot.get(p)
            player.victim = Bot.chain[p]
            markup = telebot.types.ReplyKeyboardMarkup(True)
            markup.row('Профиль')
            markup.row('Жертва')
            markup.row('Написать убийце')
            markup.row('Написать жертве')
            markup.row('Ввести код убитого')
            with open("photos/" + player.victim + '.jpg', 'rb') as photo:
                info = str(Bot.get(player.victim).info).replace('_', '\\_')
                Bot.bot.send_photo(player.id, photo, caption=f'Игра началась. Вот ваша первая жертва:*\n{info}*', reply_markup=markup, parse_mode='Markdown')
        for player in Bot.players.values():
            Bot.scheduler.add_job(Bot.kill, 'interval', days=2, args=[player.id], id=player.tag)
        Bot.scheduler.start()
        with open('players', 'wb') as p_bin:
            pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
        with open('chain', 'wb') as c_bin:
            pickle.dump(Bot.chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
        sc_store(Bot.scheduler)
        for admin in Bot.admins:
            Bot.bot.send_message(admin, "Игра началась")
        return
    if user.id in Bot.players and Bot.players[user.id].verified == 2 and message.text == "Ввести код убитого":
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        Bot.bot.send_message(message.from_user.id, "Вводите")
        Bot.bot.register_next_step_handler(message, enter_code)
        return
    if user.id in Bot.players and Bot.players[user.id].verified == 2 and message.text == "Жертва":
        if Bot.scheduler.get_job(job_id=user.username) is None:
            Bot.bot.send_message(message.from_user.id, "Вы мертвы.")
            return
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        player = Bot.players[user.id]
        with open("photos/" + player.victim + '.jpg', 'rb') as photo:
            info = str(Bot.get(player.victim).info).replace('_', '\\_')
            Bot.bot.send_photo(player.id, photo, caption=f'Вот ваша жертва:\n*{info}*', parse_mode='Markdown')
        return
    if user.id in Bot.players and message.text == "Профиль":
        if Bot.players[user.id].verified != 2:
            Bot.bot.send_message(user.id, 'Вы ещё не зарегистрированы')
            return
        with open("photos/" + user.username + ".jpg", "rb") as photo:
            info = f"*{Bot.players[user.id].info}*"
            info += "\nКод: " + Bot.players[user.id].code
            if (job := Bot.scheduler.get_job(job_id=user.username)) is not None:
                info += f"\nСтатус: в игре"
                td = job.next_run_time.replace(tzinfo=None) - datetime.now()
                s = td.seconds
                d = td.days
                h, r = divmod(s, 3600)
                m, s = divmod(r, 60)
                info += f"\nВремя до смерти: {h + d * 24}:{m}:{int(s)}"
            elif len(Bot.chain) > 0:
                info += f"\nСтатус: вне игры"
            else:
                info += f"\nСтатус: участник"
            Bot.bot.send_photo(user.id, photo, caption=info.replace('_', '\\_'), parse_mode='Markdown')
        return
    if user.id in Bot.players and Bot.players[user.id].verified == 2 and message.text == "Написать убийце":
        if Bot.scheduler.get_job(job_id=user.username) is None:
            Bot.bot.send_message(message.from_user.id, "Вы мертвы.")
            return
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        msg = Bot.bot.send_message(message.from_user.id, "Что мне передать убийце?")
        for p in Bot.players:
            if Bot.players[p].victim == user.username and Bot.scheduler.get_job(job_id=Bot.players[p].tag) is not None:
                Bot.bot.register_next_step_handler(msg, tell, args=[p, 'Жертва', 0])
                return
    if user.id in Bot.players and Bot.players[user.id].verified == 2 and message.text == "Написать жертве":
        if Bot.scheduler.get_job(job_id=user.username) is None:
            Bot.bot.send_message(message.from_user.id, "Вы мертвы.")
            return
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        msg = Bot.bot.send_message(message.from_user.id, "Что мне передать жертве?")
        Bot.bot.register_next_step_handler(msg, tell, args=[Bot.get(Bot.players[user.id].victim).id, 'Убийца', 0])
        return
    if user.id in Bot.admins and message.text == "Список игроков":
        Bot.admins[user.id].check_players()
        return
    if user.id in Bot.admins and message.text == "Профиль игрока":
        msg = Bot.bot.send_message(message.from_user.id, "Введите юзернейм игрока (без символа '@')")
        Bot.bot.register_next_step_handler(msg, give_name)
        return
    if user.id in Bot.admins and message.text == "Цепочка":
        if len(Bot.chain) == 0:
            Bot.bot.send_message(user.id, "Игра ещё не началась")
            return
        res = ""
        i = 0
        L = list(Bot.chain.keys())
        n = len(L)
        p = L[0]
        print(Bot.chain)
        while i < n:
            res += p + " -> " + Bot.get(p).victim + "\n"
            print(res)
            p = Bot.get(p).victim
            i += 1
        print("всего:", len(Bot.players))
        print("осталось:", i)
        Bot.bot.send_message(user.id, res)
        return


if __name__ == '__main__':
    new = (input("Dou you want to start a new game? (y/n)") == "y")
    if new:
        if os.path.isfile("admins"):
            os.remove("admins")
        if os.path.isfile("players"):
            os.remove("players")
        if os.path.isfile("upd"):
            os.remove("upd")
        if os.path.isfile("scheduler"):
            os.remove("scheduler")
        if os.path.isfile("chain"):
            os.remove("chain")
    Bot()
