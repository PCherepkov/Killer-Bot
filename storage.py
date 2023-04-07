from pytz import utc
from datetime import datetime, timedelta
import pickle
import sys
# apscheduler
from apscheduler.schedulers.background import BackgroundScheduler


# a function to store all the jobs
def sc_store(s):
    jobs = s.get_jobs()
    jobs_times = dict()
    for i in range(len(jobs)):
        jobs_times[jobs[i].id] = (jobs[i].next_run_time.replace(tzinfo=None) - datetime.now(), jobs[i].func)
    with open("scheduler", "wb") as s_bin:
        pickle.dump(jobs_times, s_bin, protocol=pickle.HIGHEST_PROTOCOL)
    with open("upd", "wb") as upd:
        pickle.dump(datetime.now(), upd, protocol=pickle.HIGHEST_PROTOCOL)
    return


# a function to load all the jobs from a file
# DO NOT USE!!!
def sc_load(path):
    sc = BackgroundScheduler()
    with open("scheduler", "rb") as s_bin:
        jobs_times = pickle.load(s_bin)
    print(jobs_times)
    for j in jobs_times:
        print(j, end=' ')
        sc.add_job(jobs_times[j][1], 'interval', days=2, start_date=datetime.now() + jobs_times[j][0], id=j)
    return sc


# temp funcs
def add_one():
    global cnt
    cnt += 1


def time():
    print("It's", datetime.now())


def pcnt():
    print(cnt)


if __name__ == '__main__' and sys.argv[1] == 'store':
    cnt = 0
    scheduler = BackgroundScheduler()
    scheduler.add_job(time, 'interval', seconds=1.5, id='1')
    scheduler.add_job(add_one, 'interval', seconds=1, id='2')
    scheduler.add_job(pcnt, 'interval', seconds=2, id='3')
    scheduler.start()
    sc_store(scheduler)
    while True:
        pass

if __name__ == '__main__' and sys.argv[1] == 'load':
    cnt = 0
    scheduler = sc_load("scheduler")
    scheduler.start()
    while True:
        pass
