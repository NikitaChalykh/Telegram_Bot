# Описание

Telegram-бот, работающий с API сервиса Практикум.Домашка и отправляющий сообщение о статусе проверки последней домашней работы студенту в чат бота. В проекте применяется логирование, обработка исключений при доступе к внешним сетевым ресурсам, конфиденциальные данные хранятся в пространстве переменных окружения. Бот размещен и работает на сервере Heroku.

# Установка

1. Клонировать репозиторий и перейти в него в командной строке:
```
git clone 'https://github.com/NikitaChalykh/Telegram_Homework_Bot.git'
```
```
cd Telegram_Homework_Bot
```
2. Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
```
source env/bin/activate
```
3. Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
4. Выполнить миграции:
```
python3 manage.py makemigrations
```
```
python3 manage.py migrate
```
5. Запустить проект:
```
python3 manage.py runserver
```
