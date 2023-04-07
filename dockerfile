FROM python:3
WORKDIR ./
RUN pip install apscheduler
RUN telebot
ENTRYPOINT ["python3", "main.py"]

