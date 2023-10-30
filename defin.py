from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import telebot
from shuffle import shuffle
import pickle
from storage import sc_store, sc_load

token = "here was token"


class RegInfo:
    def __init__(self, s="", n="", c=0):
        self.surname = s
        self.name = n
        self.course = c

    def __str__(self):
        return f"{self.surname} {self.name}, {self.course} курс"

    def __repr__(self):
        return self.__str__()


class User:
    def __init__(self, name="", tag="", id=0):
        # data
        self.name = name
        self.id = id
        self.tag = tag

    def __str__(self):
        return self.tag

    def __repr__(self):
        return f"Юзернейм: {self.tag}\nID: {self.id}\n"


class Player(User):
    def __init__(self, name="", tag="", id=0):
        super().__init__(name, tag, id)
        self.victim = None
        self.verified = -1  # -1 - didn't initiate registration, 0 - no photo, 1 - bad photo, 2 - verified
        self.tries = 0
        self.code = "code"
        self.photo = 0
        self.kills = 0
        self.best_time = timedelta(days=3)  # more than 2 days
        self.info = RegInfo()
        self.media = {"photo": [], "audio": [], "video": [], "document": [], "voice": []}

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        info = super().__repr__()
        job = Bot.scheduler.get_job(job_id=self.tag)
        info += f"Жертва: {self.victim}\nКод: {self.code}"
        try:
            td = job.next_run_time.replace(tzinfo=None) - datetime.now()
            info += f"\nУбийства: {self.kills}"
            if self.kills > 0:
                s = self.best_time.seconds
                d = self.best_time.days
                h, r = divmod(s, 3600)
                m, s = divmod(r, 60)
                info += f"\nЛучшее время убийства: {h + d * 24}:{m}:{int(s)}"
            s = td.seconds
            d = td.days
            h, r = divmod(s, 3600)
            m, s = divmod(r, 60)
            info += f"\nВремя до смерти: {h + d * 24}:{m}:{int(s)}"
        except:
            pass
        return info

    def clear_media(self):
        self.media = {"photo": [], "audio": [], "video": [], "document": []}


class Admin(User):
    def __init__(self, name="", tag="", id=0):
        super().__init__(name, tag, id)

    def check_player(self, tag='', id=0):
        if id in Bot.players:
            with open("photos/" + Bot.players[id].tag + ".jpg", "rb") as photo:
                info = f"*{Bot.players[id].info}*\n" + (Bot.players[id]).__repr__().replace('_', '\\_')
                Bot.bot.send_photo(self.id, photo, caption=info, parse_mode='Markdown')
        elif (p := Bot.get(tag)) is not None:
            with open("photos/" + tag + ".jpg", "rb") as photo:
                info = f"*{p.info}*\n" + p.__repr__().replace('_', '\\_')
                Bot.bot.send_photo(self.id, photo, caption=info, parse_mode='Markdown')
        return

    def check_players(self):
        res = str(list(map(str, Bot.players.values())))[1:-1]
        if res == "":
            res = "Игроков нет"
        Bot.bot.send_message(self.id, res)


class Bot:
    bot = telebot.TeleBot(token)
    admins = dict()   # {id: Admin}
    players = dict()  # {id: Player}
    chain = dict()    # {tag: tag}
    scheduler = BackgroundScheduler()
    state = 0  # 0 - game not started yet, 1 - is active, 2 - game's ended

    def __init__(self):
        try:
            a_bin = open("admins", "rb")
            p_bin = open("players", "rb")

            Bot.admins = pickle.load(a_bin)
            Bot.players = pickle.load(p_bin)

            print("admins: ", Bot.admins)
            print("players:", Bot.players)

            a_bin.close()
            p_bin.close()
        except:
            pass
        try:
            c_bin = open("chain", "rb")
            Bot.chain = pickle.load(c_bin)
            Bot.scheduler = BackgroundScheduler()
            with open("scheduler", "rb") as s_bin:
                jobs_times = pickle.load(s_bin)
            with open("upd", "rb") as upd:
                date = pickle.load(upd)
            print(jobs_times)
            for j in jobs_times:
                print(j, end=' ')
                # if Bot.get(j).kills == 0 and False:
                #    rd = jobs_times[j][0] + date + timedelta(hours=4, minutes=25)
                rd = jobs_times[j][0] + date  # + timedelta(hours=30)
                Bot.scheduler.add_job(id=j, func=jobs_times[j][1], trigger='date', run_date=rd,
                                      args=[Bot.get(j).id])
                print(jobs_times[j][0])
            Bot.scheduler.start()
            print("chain:  ", Bot.chain)
            print("scheduler:", Bot.scheduler)
            c_bin.close()
        except:
            pass
        # Bot.bot.polling(none_stop=True, interval=0)
        Bot.bot.infinity_polling(timeout=10, long_polling_timeout=5)

    @staticmethod
    def get(name: str):
        for user in Bot.admins.values():
            if user.name == name or user.tag == name:
                return user
        for user in Bot.players.values():
            if user.name == name or user.tag == name:
                return user
        return None

    @staticmethod
    def contains(name: str):
        return False if Bot.get(name) is None else True

    @staticmethod
    def kill(id: int):
        dead = Bot.players[id]
        if dead is None:
            return
        with open('dead.mp4', 'rb') as vid:
            Bot.bot.send_video(id, vid, caption="Вы мертвы. Игра для вас окончена ☠", reply_markup=None)
        for p in Bot.chain:
            player = Bot.get(p)
            if player.victim == dead.tag:
                Bot.players[player.id].victim = dead.victim
                Bot.players[player.id].kills += 1
                ttk = timedelta(days=2) - (Bot.scheduler.get_job(player.tag).next_run_time.replace(tzinfo=None) - datetime.now())
                Bot.players[player.id].best_time = min(Bot.players[player.id].best_time, ttk)
                Bot.chain[player.tag] = dead.victim
                Bot.chain.pop(dead.tag)
                Bot.scheduler.get_job(player.tag).reschedule('interval', days=2)
                break
        Bot.scheduler.remove_job(dead.tag)
        if len(Bot.chain) < 2:
            for p in Bot.chain:
                gif = open("congrats.gif", "rb")
                Bot.bot.send_video(Bot.get(p).id, gif, caption="Игра окончена. Вы победили!")
                gif.close()
            for a in Bot.admins:
                Bot.bot.send_message(a, "Игра окончена.")
            record = "username | best time | number of kills\n"
            for p in Bot.players:
                record += f"{Bot.players[p].tag}: {Bot.players[p].best_time} | {Bot.players[p].kills}\n"
            with open("stats.txt", "w") as stats:
                stats.write(record)
            Bot.bot.stop_polling()
