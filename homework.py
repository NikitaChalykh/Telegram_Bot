import os
from dotenv import load_dotenv
import logging
import requests
import telegram
import datetime as dt
import time
import sys


class MissingValueException(Exception):
    """Создаем свое исключения при отсутствии переменных окружения."""


class GetAPIException(Exception):
    """Создаем свое исключение при сбое запроса к API."""


class MissingKeyException(Exception):
    """Создаем свое исключение при отсутствии ожидаемых ключей в ответе API."""


class UndocumentException(Exception):
    """Создаем свое исключение при недокумент. статусе домашней работы."""


load_dotenv()
PRACTICUM_TOKEN = os.getenv(
    'PRACTICUM_TOKEN', default='AQAAAAAf9UMYAAYckdIQRPTNIUiPtIHQsIBS4Sw'
)
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_TOKEN', default='2045985373:AAF9T9ZtOwCdA0kOzsDmdfgX6CKaskZylks'
)
if TELEGRAM_TOKEN is None or PRACTICUM_TOKEN is None:
    logging.critical('Отсутствуют переменные окружения!')
    raise MissingValueException('Отсутствуют переменные окружения!')
CHAT_ID = 206755993
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

logging.basicConfig(
    format='%(asctime)s  %(levelname)s  %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.INFO
)

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# словарь для сохранения актуальной информации по изменениям статуса проверки
# и для сохранения времени последнего ответа по изменениям статуса проверки
# последней домашней работы от API
homeworks_dict = {}
# словарь для сохранения последней ошибки для предотвращения спама
# при отправке однотипных ысообщений в телеграмм
error_dict = {}


def send_message(bot, message):
    """Отправляем сообщение в телеграмм бот."""
    try:
        bot.send_message(CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except Exception:
        logging.exception('Сбой при отправке сообщения')


def get_api_answer(url, current_timestamp):
    """Делаем запрос информации к API Яндекс.Практикум."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(url, headers=headers, params=payload)
        response_json = response.json()
        if response.status_code != 200:
            logging.exception('Эндпоинт API недоступен')
            message = 'Сбой в работе программы: Эндпоинт API недоступен'
            raise GetAPIException('Эндпоинт API недоступен')
            if message != error_dict.get('last_error_message'):
                error_dict['last_error_message'] = message
                send_message(bot, message)
        return response_json
    except Exception:
        logging.exception('Сбой при запросе к эндпоинту API')
        message = 'Сбой в работе программы: Сбой при запросе к эндпоинту API'
        if message != error_dict.get('last_error_message'):
            error_dict['last_error_message'] = message
            send_message(bot, message)
        raise GetAPIException('Сбой при запросе к эндпоинту API')


def parse_status(homework):
    """Проверяем статус запрошенной информации от API."""
    homework_status = homework['status']
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Проверяем наличие запрошенной информации от API."""
    try:
        homeworks = response['homeworks']
        homeworks_dict['last_timestamp'] = response['current_date']
        if homeworks:
            if HOMEWORK_STATUSES.get(homeworks[0]['status']) is None:
                logging.exception('Недокументированный статус домашней работы')
                message = (
                    'Сбой в работе программы:'
                    'Недокументированный статус домашней работы'
                )
                if message != error_dict.get('last_error_message'):
                    error_dict['last_error_message'] = message
                    send_message(bot, message)
                raise UndocumentException(
                    'Недокументированный статус домашней работы'
                )
            # сохраняем в словарь актуальную информацию по изменениям статуса
            # проверки последней домашней работы от API
            homeworks_dict['last_homework'] = homeworks[0]
            # сохраняем в словарь время последнего ответа
            # от API с информацией по изменениям статуса
            # проверки домашней работы
            return True
        else:
            return False
    except KeyError:
        logging.exception('Отсутствуют ожидаемые ключи в ответе API')
        message = (
            'Сбой в работе программы:'
            'Отсутствуют ожидаемые ключи в ответе API'
        )
        if message != error_dict.get('last_error_message'):
            error_dict['last_error_message'] = message
            send_message(bot, message)
        raise MissingKeyException(
            'Отсутствуют ожидаемые ключи в ответе API'
        )


def main():
    """Главный исполняемый код."""
    # при первом запуске бота устанавливаем временную метку запроса к API
    # на 24 часа назад от текущего времени для получения уже ранее
    # измененного статуса проверки домашней работы,
    # если бот был запущен позже проверки
    current_time = dt.datetime.now() - dt.timedelta(hours=24)
    current_timestamp = current_time.timestamp()
    while True:
        try:
            # при работе бесконечного цикла устанавливаем
            # временную метку запроса к API из словаря timestamps_dict -
            # время последнего ответа от API с информациекй по изменениям
            # татуса проверки домашней работы
            if homeworks_dict.get('last_timestamp'):
                current_timestamp = homeworks_dict.get('last_timestamp')
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework_status_changed = check_response(response)
            if homework_status_changed:
                # получаем из словаря homeworks_dict сохраненную
                # актуальную информации по изменениям статуса проверки
                # последней домашней работы от API
                last_homework = homeworks_dict.get('last_homework')
                message = parse_status(last_homework)
                # отправляем результат проверки в телеграмм
                send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != error_dict.get('last_error_message'):
                error_dict['last_error_message'] = message
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
