from defin import *

password = "aaa"


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
    if len(message.text.split()) < 3:
        msg = Bot.bot.send_message(message.from_user.id, "Неверный формат. Попробуйте ещё раз")
        Bot.bot.register_next_step_handler(msg, set_info)
        return
    args = message.text.split()
    name, surname, course = args[0], args[1], args[2]
    Bot.players[message.from_user.id].info.name = name
    Bot.players[message.from_user.id].info.surname = surname
    Bot.players[message.from_user.id].info.course = course
    markup = telebot.types.ReplyKeyboardMarkup(True)
    markup.row('Профиль')
    markup.row('Жертва')
    markup.row('Ввести код убитого')
    Bot.bot.send_message(message.from_user.id, "Регистрация пройдена успешно", reply_markup=markup)
    with open("players", "wb") as p_bin:
        pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
def set_code(message):
    Bot.players[message.from_user.id].code = message.text
    if message.text is None:
        msg = Bot.bot.send_message(message.from_user.id, "Код не принят. Введите текстовый код")
        Bot.bot.register_next_step_handler(msg, set_code)
        return
    msg = Bot.bot.send_message(message.from_user.id, "Код принят. Теперь введите имя, фамилию и номер курса через пробел")
    Bot.bot.register_next_step_handler(msg, set_info)
@Bot.bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data.split()
    player = Bot.get(data[1])
    if data[0] == '1':
        if player.verified == 1 and player.photo > int(data[2]):
            Bot.bot.answer_callback_query(call.id, "Это фото уже отклонено")
            return
        if player.verified == 2:
            Bot.bot.answer_callback_query(call.id, "У игрока уже есть одобренное фото")
            return
        Bot.players[player.id].verified = 2
        msg = Bot.bot.send_message(player.id, "Фото успешно прошло проверку. Теперь придумайте свой уникальный код и отправьте его", reply_markup=None)
        Bot.bot.register_next_step_handler(msg, set_code)
    elif data[0] == '0':
        if player.verified == 1 and player.photo > int(data[2]):
            Bot.bot.answer_callback_query(call.id, "Это фото уже отклонено")
            return
        if player.verified == 2:
            Bot.bot.answer_callback_query(call.id, "У игрока уже есть одобренное фото")
            return
        Bot.players[player.id].verified = 1
        Bot.players[player.id].photo += 1
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Регистрация')
        msg = Bot.bot.send_message(player.id, "Фото не прошло проверку. Отправьте другое", reply_markup=markup)
        Bot.bot.register_next_step_handler(msg, register)


def register(message):
    user = message.from_user
    if message.text == password:
        Bot.admins[user.id] = Admin(user.first_name, user.username, user.id)
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Список игроков')
        markup.row('Профиль игрока')
        markup.row('Цепочка')
        Bot.bot.send_message(message.from_user.id, 'Вход выполнен', reply_markup=markup)
        with open("admins", "wb") as a_bin:
            pickle.dump(Bot.admins, a_bin, protocol=pickle.HIGHEST_PROTOCOL)
    elif isinstance(message.photo, list):
        photo_id = message.photo[-1].file_id
        photo_info = Bot.bot.get_file(photo_id)
        photo_path = photo_info.file_path
        photo = Bot.bot.download_file(photo_path)
        f = open("photos/" + user.username + '.jpg', 'wb')
        f.write(photo)
        f.close()
        try:
            print(Bot.players[user.id])
        except:
            pass
        if Bot.players.get(user.id) is None:
            Bot.players[user.id] = Player(user.first_name, user.username, user.id)
        print(Bot.admins)
        for admin in Bot.admins:
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            accept = telebot.types.InlineKeyboardButton('✔', callback_data='1 ' + user.username + ' ' + str(Bot.players[user.id].photo))
            decline = telebot.types.InlineKeyboardButton('❌', callback_data='0 ' + user.username + ' ' + str(Bot.players[user.id].photo))
            keyboard.add(accept, decline)
            try:
                with open("photos/" + user.username + '.jpg', 'rb') as f:
                    Bot.bot.send_photo(admin, f, reply_markup=keyboard, caption='@' + user.username)
            except Exception as e:
                print('error:' + str(e.args))
                print('cause:', admin, 'on user', user.username)
        Bot.bot.reply_to(message, 'Фото отправлено на проверку')
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
    correct = (message.text == Bot.get(Bot.chain[user.username]).code)
    Bot.players[user.id].tries += 1 - correct
    if correct:
        Bot.kill(Bot.get(Bot.players[user.id].victim).id)
        with open('chain', 'wb') as c_bin:
            pickle.dump(Bot.chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
        sc_store(Bot.scheduler)
        with open('players', 'wb') as p_bin:
            pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
        markup = telebot.types.ReplyKeyboardMarkup(True)
        markup.row('Профиль')
        markup.row('Жертва')
        markup.row('Ввести код убитого')
        with open("photos/" + Bot.players[user.id].victim + '.jpg', 'rb') as photo:
            info = str(Bot.get(Bot.players[user.id].victim).info)
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


@Bot.bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user = message.from_user
    if message.text == "Регистрация":
        if user.id in Bot.players and Bot.players[user.id].verified == 2:
            Bot.bot.send_message(message.from_user.id, "Вы уже зарегестрированы")
            return
        Bot.bot.send_message(message.from_user.id, "Отправьте фото")
        Bot.bot.register_next_step_handler(message, register)
    if user.id in Bot.admins and message.text == "Начать":
        Bot.chain = shuffle(list(Bot.players.values()))
        for p in Bot.chain:
            player = Bot.get(p)
            player.victim = Bot.chain[p]
            markup = telebot.types.ReplyKeyboardMarkup(True)
            markup.row('Профиль')
            markup.row('Жертва')
            markup.row('Ввести код убитого')
            with open("photos/" + player.victim + '.jpg', 'rb') as photo:
                info = str(Bot.get(player.victim).info)
                Bot.bot.send_photo(player.id, photo, caption=f'Игра началась. Вот ваша первая жертва:*\n{info}*', reply_markup=markup, parse_mode='Markdown')
        for player in Bot.players.values():
            Bot.scheduler.add_job(Bot.kill, 'interval', days=2, args=[player.id], id=player.tag)
        Bot.scheduler.start()
        with open('players', 'wb') as p_bin:
            pickle.dump(Bot.players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
        with open('chain', 'wb') as c_bin:
            pickle.dump(Bot.chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
        sc_store(Bot.scheduler)
    if user.id in Bot.players and Bot.players[user.id].verified == 2 and message.text == "Ввести код убитого":
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        Bot.bot.send_message(message.from_user.id, "Вводите")
        Bot.bot.register_next_step_handler(message, enter_code)
    if user.id in Bot.players and message.text == "Жертва":
        if len(Bot.chain) == 0:
            Bot.bot.send_message(message.from_user.id, "Игра ещё не началась")
            return
        player = Bot.players[user.id]
        with open("photos/" + player.victim + '.jpg', 'rb') as photo:
            info = str(Bot.get(player.victim).info)
            Bot.bot.send_photo(player.id, photo, caption=f'Вот ваша жертва:\n{info}', parse_mode='Markdown')
    if user.id in Bot.players and message.text == "Профиль":
        if Bot.players[user.id].verified != 2:
            Bot.bot.send_message(user.id, 'Вы ещё не зарегистрированы')
            return
        with open("photos/" + user.username + ".jpg", "rb") as photo:
            info = f"*{Bot.players[user.id].info}*"
            if Bot.players[user.id].code is not None:
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
            Bot.bot.send_photo(user.id, photo, caption=info, parse_mode='Markdown')
    if user.id in Bot.admins and message.text == "Список игроков":
        Bot.admins[user.id].check_players()
    if user.id in Bot.admins and message.text == "Профиль игрока":
        msg = Bot.bot.send_message(message.from_user.id, "Введите юзернейм игрока (без символа '@')")
        Bot.bot.register_next_step_handler(msg, give_name)
    if user.id in Bot.admins and len(Bot.chain) > 0 and message.text == "Цепочка":
        res = ""
        i = 0
        L = list(Bot.chain.keys())
        n = len(L)
        while i < n - 1:
            res += L[i] + " -> "
            i += 1
        res += L[n - 1]
        Bot.bot.send_message(user.id, res)


if __name__ == '__main__':
    Bot()