FROM python:3.11.0
WORKDIR ./
COPY . .
RUN pip install apscheduler
RUN pip install telebot
CMD ["python3", "main.py"]
EXPOSE 80/tcp

