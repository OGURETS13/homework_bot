import logging
import os
import requests
import sys
import time
from http import HTTPStatus

from dotenv import load_dotenv
from telegram import Bot
import telegram

from exceptions import EndpointException


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в телеграм чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except telegram.error.TelegramError as error:
        logger.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(current_timestamp):
    """Делаем запрос и получаем ответ от api яндекса."""
    timestamp = (current_timestamp or int(time.time()))
    params = {'from_date': timestamp}

    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params)

    if response.status_code != HTTPStatus.OK:
        logger.error('Эндпоинт недоступен')
        raise EndpointException
    else:
        return response.json()


def check_response(response):
    """Проверяем ответ API на корректность, возвращаем список работ."""
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            'Тип объекта homeworks не соответствует ожидаемому (list)'
        )
    return homeworks


def parse_status(homework):
    """Извлекаем из информации о домашней работе её статус."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем что все токены присвоены."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные '
                        'окружения во время запуска бота')
        return

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:

            response = get_api_answer(current_timestamp)

            current_timestamp = int(time.time())

            homeworks = check_response(response)

            homework = homeworks[0]

            message = parse_status(homework)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
