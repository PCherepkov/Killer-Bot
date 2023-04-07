FROM python:3
WORKDIR ./
RUN pip install apscheduler
RUN pip install telebot
ENTRYPOINT ["python3", "main.py"]

