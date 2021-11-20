import os
from dotenv import load_dotenv
import logging
import requests
import telegram
import time
import sys

load_dotenv()

CHAT_ID = 206755993
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}
homeworks_dict = {}
error_dict = {}


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s  %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.ERROR
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MissingValueException(Exception):
    """Создаем свое исключения при отсутствии переменных окружения."""


class GetAPIException(Exception):
    """Создаем свое исключение при сбое запроса к API."""


class MissingKeyException(Exception):
    """Создаем свое исключение при отсутствии ожидаемых ключей в ответе API."""


class UndocumentException(Exception):
    """Создаем свое исключение при недокумент. статусе домашней работы."""


PRACTICUM_TOKEN = os.getenv(
    'PRACTICUM_TOKEN', default='AQAAAAAf9UMYAAYckdIQRPTNIUiPtIHQsIBS4Sw'
)
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_TOKEN', default='2045985373:AAF9T9ZtOwCdA0kOzsDmdfgX6CKaskZylks'
)
if TELEGRAM_TOKEN is None or PRACTICUM_TOKEN is None:
    logger.critical('Отсутствуют переменные окружения!')
    raise MissingValueException('Отсутствуют переменные окружения!')


def send_message(bot, message):
    """Отправляем сообщение в телеграмм бот."""
    try:
        bot.send_message(CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')


def get_api_answer(url, current_timestamp):
    """Делаем запрос информации к API Яндекс.Практикум."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(url, headers=headers, params=payload)
        response_json = response.json()
        if response.status_code != 200:
            raise GetAPIException
        logger.debug('Запрос от API получен и первично обработан')
        logger.debug(f'Ответ API {response_json}')
        return response_json
    except Exception:
        if response.status_code != 200:
            raise GetAPIException('Эндпоинт API недоступен')
        else:
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
        last_current_date = response['current_date']
    except KeyError:
        raise MissingKeyException(
            'Отсутствуют ожидаемые ключи в ответе API'
        )
    if homeworks != []:
        if HOMEWORK_STATUSES.get(homeworks[0]['status']) is None:
            raise UndocumentException(
                'Недокументированный статус домашней работы'
            )
        homeworks_dict['last_homework'] = homeworks[0]
        homeworks_dict['last_timestamp'] = last_current_date
        logger.debug(
            'Обновление информации в словаре о последней проверке'
        )
        logger.debug(
            'Домашня работа проверена за время этой итеррации'
        )
        return True
    else:
        logger.debug(
            'Домашня работа не проверена за время этой итеррации'
        )
        return False


def main():
    """Главный исполняемый код."""
    logger.debug('-----------------')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    while True:
        try:
            logger.debug('Начало новой иттерации')
            if homeworks_dict.get('last_timestamp'):
                current_timestamp = homeworks_dict.get('last_timestamp')
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework_status_changed = check_response(response)
            if homework_status_changed:
                last_homework = homeworks_dict.get('last_homework')
                message = parse_status(last_homework)
                send_message(bot, message)
            logger.debug('-----------------')
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            if message != error_dict.get('last_error_message'):
                error_dict['last_error_message'] = message
                send_message(bot, message)
            logger.debug('-----------------')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
# просто тестовый код для работы
# просто код для проверки test2333
