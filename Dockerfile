FROM python:3
WORKDIR ./
RUN pip install apscheduler
RUN pip install telebot
EXPOSE 8080
ENTRYPOINT ["python3", "main.py"]

