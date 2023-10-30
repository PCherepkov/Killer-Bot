from defin import *
from time import sleep


def get(name: str):
    for user in Players.values():
        if user.name == name or user.tag == name:
            return user
    return None


def job_fun(id: int):
    print(id, "finished")


def show_stats():
    record = "username | best time | number of kills\n"
    for p in Players:
        record += f"{Players[p].tag}: {Players[p].best_time} | {Players[p].kills}\n"
    print(record)


def add_player(info: list):
    # 1 chain
    # 2 self.killer.victim
    global Players, Chain

    if len(info) < 3:
        print("error!")
        return

    data = {"tag": info[0], "victim": info[1], "code": info[2]}
    player = Player()
    player.victim = data['victim']
    player.verified = 2
    player.tag = data['tag']
    player.id = ID
    player.code = data['code']
    reg = input("name surname course: ").split()
    player.info.name = reg[0]
    player.info.surname = reg[1]
    player.info.course = int(reg[2])

    Scheduler.add_job(Bot.kill, 'interval', days=2, args=[player.id], id=player.tag)
    Scheduler.modify_job(player.tag, "default", args=[1984])
    Scheduler.reschedule_job(player.tag, "default", )

    killer_tag = input("killer tag: ")
    killer = get(killer_tag)
    Players[killer.id].victim = player.tag

    Players[ID] = player
    Chain[killer_tag] = player.tag
    Chain[player.tag] = player.victim
    return


def delete_player(tag: str):
    global Chain, Players

    killer = False
    player = False
    for user_id in Players:
        if Players[user_id].victim == tag:
            killer = Players[user_id]
        if Players[user_id].tag == tag:
            player = Players[user_id]
    if not killer or not player:
        print("wrong tag!")
        return None
    Chain[killer.tag] = player.victim
    Chain.pop(player.tag)
    Players[killer.id].victim = player.victim
    Players.pop(player.id)
    Scheduler.remove_job(player.tag)
    return player


def change_player(tag: str):
    global Chain, Players

    prop = input("1. tag\n 2. else\n")
    if prop == "1":
        new_tag = input("new tag: ")
        killer = False
        player = False
        for user_id in Players:
            if Players[user_id].victim == tag:
                killer = Players[user_id]
            if Players[user_id].tag == tag:
                player = Players[user_id]
        if not killer or not player:
            print("wrong tag!")
            return None
        Chain[killer.tag] = new_tag
        Chain[new_tag] = player.victim
        Chain.pop(player.tag)
        Players[killer.id].victim = new_tag
        Players[player.id].tag = new_tag
        Scheduler.start()
        job = Scheduler.get_job(tag)
        Scheduler.add_job(Bot.kill, 'interval', days=2, args=[player.id], id=player.tag)
        Scheduler.shutdown()
    return


if __name__ == '__main__':
    try:
        a_bin = open("admins", "rb")
        p_bin = open("players", "rb")

        Admins = pickle.load(a_bin)
        Players = pickle.load(p_bin)

        print("admins: ", Admins)
        print("players:", Players)

        a_bin.close()
        p_bin.close()
    except:
        print("admins or players are missing")
        exit()

    if True:
        c_bin = open("chain", "rb")
        Chain = pickle.load(c_bin)
        Scheduler = BackgroundScheduler()
        with open("scheduler", "rb") as s_bin:
            jobs_times = pickle.load(s_bin)
        with open("upd", "rb") as upd:
            date = pickle.load(upd)
        print(jobs_times)
        for j in jobs_times:
            print(j, end=' ')
            rd = jobs_times[j][0] + date
            Scheduler.add_job(id=j, func=jobs_times[j][1], trigger='date', run_date=rd,
                                  args=[get(j).id])
            print(jobs_times[j][0])
        print("chain:  ", Chain)
        print("scheduler:", Scheduler)
        c_bin.close()
    #except:
    #    print("scheduler or upd missing")
    #exit()

    ID = -1
    Scheduler.start()
    print("'help' for all commands")
    cmd = input()
    while cmd != "exit":
        if cmd == "add":
            print("user_name, victim, code to ADD: ")
            add_player(input().split())
            ID -= 1
        elif cmd == "change":
            print("user_name to CHANGE: ")
            change_player(input())
        elif cmd == "delete":
            print("user_name to DELETE: ")
            delete_player(input())
        elif cmd == "read":
            print("user_name to READ")
            tag = input()
            print(get(tag))
        elif cmd == "show":
            print("players:", Players)
            print("chain:", Chain)
        elif cmd == "stats":
            show_stats()
        elif cmd == "help":
            print("add, change, delete, read, show, stats")
        elif cmd == "" or cmd == "\n":
            pass
        else:
            print("unknown command ('exit' to exit)")
        cmd = input()
    with open('chain', 'wb') as c_bin:
        pickle.dump(Chain, c_bin, protocol=pickle.HIGHEST_PROTOCOL)
    sc_store(Scheduler)
    Scheduler.shutdown()
    with open('players', 'wb') as p_bin:
        pickle.dump(Players, p_bin, protocol=pickle.HIGHEST_PROTOCOL)
