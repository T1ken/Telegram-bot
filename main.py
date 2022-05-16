import json
from datetime import date, datetime
from typing import Any

import telebot
from decouple import config
from telebot.types import Message, InputMediaPhoto
from loguru import logger
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

import botrequests

client = telebot.TeleBot(config('TOKEN'))
logger.add("debug.log", format="{time} {message}", level="DEBUG", encoding='utf-8')

users_list = []


def create_user(
        user_id: int,
        name: str
):
    user_dict = dict()
    user_dict['id'] = user_id
    user_dict['command'] = name
    user_dict['city'] = ''
    user_dict['max_hotel_num'] = 0
    user_dict['min_price'] = 0
    user_dict['max_price'] = 0
    user_dict['min_distance'] = 0
    user_dict['max_distance'] = 0
    user_dict['checkIn'] = ''
    user_dict['checkOut'] = ''
    users_list.append(user_dict)


def save_history(
        user_id: int,
        name: str
):
    current_data = datetime.now()
    text = "Время вызова: {}:{}:{}\n" \
           "Дата вызова: {}.{}.{}\n" \
           "Вызванная команда: {}\n".format(
            current_data.hour,
            current_data.minute,
            current_data.second,
            current_data.day,
            current_data.hour,
            current_data.year,
            name,)
    with open('history.json', 'r', encoding='utf-8') as file:
        dictionary = json.load(file)
    with open('history.json', 'w', encoding='utf-8') as file:
        try:
            dictionary[user_id] = dictionary[user_id] + text
        except KeyError:
            dictionary[user_id] = text
        json.dump(dictionary, file, ensure_ascii=False)
    logger.debug("Пользователь: {}\n".format(user_id) + text)


@client.message_handler(commands=['start'])
def start(message: Message) -> None:
    client.send_message(
        message.chat.id,
        'Добро пожаловать!\n'
        'Вас приветствует одно из лучших туристических агентств "Too Easy Travel". '
        'Наш telegram-бот поможет вам определиться с отелем всего за пару минут.\n'
        'Чтобы узнать о всех командах нашего бота, воспользуйтесь командой /help'
    )


@client.message_handler(commands=['hello_world'])
def hello_world(message: Message) -> None:
    client.send_message(message.chat.id, 'Hello, world!👋')


@client.message_handler(commands=['lowprice'])
def lowprice(message: Message) -> None:
    save_history(message.from_user.id, '/lowprice')
    create_user(message.from_user.id, 'low_price')
    mesg = client.send_message(message.chat.id, 'Отправьте название города')
    client.register_next_step_handler(mesg, max_hotels_count_request)


@client.message_handler(commands=['highprice'])
def highprice(message: Message) -> None:
    save_history(message.from_user.id, '/highprice')
    create_user(message.from_user.id, 'high_price')
    mesg = client.send_message(message.chat.id, 'Отправьте название города')
    client.register_next_step_handler(mesg, max_hotels_count_request)


@client.message_handler(commands=['bestdeal'])
def bestdeal(message: Message) -> None:
    save_history(message.from_user.id, '/bestdeal')
    create_user(message.from_user.id, 'best_deal')
    mesg = client.send_message(message.chat.id, 'Отправьте название города')
    client.register_next_step_handler(mesg, max_hotels_count_request)


@client.message_handler(commands=['history'])
def history(message: Message) -> None:
    try:
        with open('history.json'.format(message.chat.id), 'r', encoding='utf-8') as file:
            user_history = json.load(file)[message.chat.id]
            if len(user_history) > 4096:
                client.send_message(
                    message.chat.id,
                    'Ваша история поиска слишком большая, и телеграм не справится с ней😥\n'
                    'Вы получите лишь результаты последних 3 запросов.'
                )
                abbreviated_user_history = user_history.split('Время вызова')
                abbreviated_user_history = abbreviated_user_history[len(abbreviated_user_history) - 3:]
                text = ''
                for i_fragment in abbreviated_user_history:
                    text = text + 'Время вызова' + i_fragment
                client.send_message(message.chat.id, text)
            else:
                client.send_message(message.chat.id, user_history, disable_web_page_preview=True)
    except KeyError:
        client.send_message(
            message.chat.id,
            'Ваша история поиска пуста😔\n'
            'Но вы можете исправить это прямо сейчас)'
        )
    logger.debug('Пользователь: {}\nВведённая команда: /history\n'.format(message.chat.id))


@client.message_handler(commands=['help'])
def help_command(message: Message) -> None:
    text = 'Вот все функции, которые умеет наш бот:\n' \
           '/lowprice - выводит топ самых дешёвых отелей\n' \
           '/highprice - выводит топ самых дорогих отелей\n' \
           '/bestdeal - выводит самые подходящие для вас по цене ' \
           'и отдалённости от центра города отели\n' \
           '/history - просмотреть вашу историю запросов'
    client.send_message(message.chat.id, text)
    logger.debug('Пользователь: {}\nВведённая команда: /help\n'.format(message.chat.id))


@client.message_handler(content_types=['text'])
def get_text(message: Message) -> None:
    if message.text.lower() == 'привет':
        client.send_message(message.chat.id, 'Привет!👋')
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))


def max_hotels_count_request(message: Message) -> None:
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))
    for i_user in users_list:
        if message.from_user.id == i_user['id']:
            if message.text.isalpha() is True or ''.join(message.text.split(' ')).isalpha():
                i_user['city'] = message.text
                if i_user['command'] == 'best_deal':
                    mesg = client.send_message(
                        message.chat.id,
                        'Отправьте диапозон цен в рублях(пример: 5000-10000)'
                    )
                    client.register_next_step_handler(mesg, price_range_request)
                else:
                    mesg = client.send_message(
                        message.chat.id,
                        'Отправьте максимальное количество отелей, '
                        'которые надо вывести (отправьте всего 1 цифру, пример: 3)'
                    )
                    client.register_next_step_handler(mesg, check_in_request)
            else:
                mesg = client.send_message(
                    message.chat.id,
                    'Вы отправили сообщение, содержащее не только буквы. '
                    'Значит это не название города. Попробуйте отправить снова'
                )
                client.register_next_step_handler(mesg, max_hotels_count_request)


def price_range_request(message: Message) -> None:
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))
    for i_user in users_list:
        if message.from_user.id == i_user['id']:
            try:
                lst = message.text.split('-')
                i_user['min_price'] = int(lst[0])
                i_user['max_price'] = int(lst[1])
                mesg = client.send_message(
                    message.chat.id,
                    'Отправьте диапозон расстояния от центра города в километрах (пример: 0-10)'
                )
                client.register_next_step_handler(mesg, distance_range_request)
            except:
                mesg = client.send_message(
                    message.chat.id,
                    'Вы отправили сообщения неправильного формата. Попробуйте еще раз'
                )
                logger.error(
                    'Ошибка в функции price_range_request\n'
                    'Сообщение пользователя: {}\nID пользователя: {}'.format(
                        message.text, message.chat.id))
                client.register_next_step_handler(mesg, price_range_request)


def distance_range_request(message: Message) -> None:
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))
    for i_user in users_list:
        if message.from_user.id == i_user['id']:
            try:
                lst = message.text.split('-')
                i_user['min_distance'] = int(lst[0])
                i_user['max_distance'] = int(lst[1])
                i_user['command'] = False
                mesg = client.send_message(
                    message.chat.id,
                    'Отправьте максимальное количество отелей, '
                    'которые надо вывести (отправьте всего 1 цифру, пример: 3)'
                )
                client.register_next_step_handler(mesg, check_in_request)
            except:
                mesg = client.send_message(
                    message.chat.id,
                    'Вы отправили сообщения неправильного формата. Попробуйте еще раз'
                )
                logger.error(
                    'Ошибка в функции distance_range_request\n'
                    'Сообщение пользователя: {}\nID пользователя: {}'.format(
                        message.text, message.chat.id))
                client.register_next_step_handler(mesg, distance_range_request)


def check_in_request(message: Message) -> None:
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))
    for i_user in users_list:
        if message.from_user.id == i_user['id']:
            try:
                i_user['max_hotel_num'] = int(message.text)
                calendar, step = DetailedTelegramCalendar(locale='ru', min_date=date.today()).build()
                client.send_message(message.chat.id, f'Выберите дату заезда ({LSTEP[step]})', reply_markup=calendar)
            except:
                mesg = client.send_message(
                    message.chat.id,
                    'Вы отправили сообщения неправильного формата. Попробуйте еще раз'
                )
                logger.error(
                    'Ошибка в функции check_in_request\n'
                    'Сообщение пользователя: {}\nID пользователя: {}'.format(
                        message.text, message.chat.id))
                client.register_next_step_handler(mesg, check_in_request)


@client.callback_query_handler(func=DetailedTelegramCalendar.func())
def check_out_request(c: Any) -> None:
    result, key, step = DetailedTelegramCalendar(min_date=date.today()).process(c.data)
    if not result and key:
        client.edit_message_text(f"Выберите дату заезда {LSTEP[step]}", c.message.chat.id, c.message.message_id,
                                 reply_markup=key)
    else:
        client.edit_message_text(f"Вы выбрали {result}", c.message.chat.id, c.message.message_id)
        logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(c.message.chat.id, result))
        for i_user in users_list:
            if c.message.chat.id == i_user['id']:
                if i_user['checkIn'] == '':
                    calendar, step = DetailedTelegramCalendar(
                        locale='ru',
                        calendar_id=1,
                        min_date=date.today()
                    ).build()
                    client.send_message(c.message.chat.id, f'Выберите дату выезда', reply_markup=calendar)
                    i_user['checkIn'] = result


@client.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def max_hotels_request(c: Any) -> None:
    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today()).process(c.data)
    if not result and key:
        client.edit_message_text(f"Выберите дату выезда", c.message.chat.id, c.message.message_id,
                                 reply_markup=key)
    else:
        client.edit_message_text(f"Вы выбрали {result}", c.message.chat.id, c.message.message_id)
        logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(c.message.chat.id, result))
        for i_user in users_list:
            if c.message.chat.id == i_user['id']:
                i_user['checkOut'] = result
                mesg = client.send_message(c.message.chat.id, 'Сколько фото отелей отправить (0 если не надо)?')
                client.register_next_step_handler(mesg, get_result)


def get_result(message: Message) -> None:
    logger.debug('Пользователь: {}\nВведённый текст: {}\n'.format(message.chat.id, message.text))
    for i_user in users_list:
        if message.from_user.id == i_user['id']:
            try:
                photo_count = int(message.text)
            except:
                logger.error(
                    'Ошибка в функции get_result\nСообщение пользователя: {}\nID пользователя: {}'.format(
                        message.text, message.chat.id))
                mesg = client.send_message(message.chat.id,
                                           'Данное сообщение не является целым числом. Попробуйте ещё раз')
                client.register_next_step_handler(mesg, get_result)
                break
            client.send_message(message.chat.id, 'Ищем отели...')
            if i_user['command'] == 'low_price':
                hotels_list = botrequests.lowprice.get_result(i_user['city'], i_user['max_hotel_num'],
                                                              i_user['checkIn'], i_user['checkOut'])
            elif i_user['command'] == 'high_price':
                hotels_list = botrequests.highprice.get_result(i_user['city'], i_user['max_hotel_num'],
                                                               i_user['checkIn'], i_user['checkOut'])
            else:
                hotels_list = botrequests.bestdeal.get_result(i_user['city'], i_user['max_hotel_num'],
                                                              i_user['min_price'], i_user['max_price'],
                                                              i_user['min_distance'], i_user['max_distance'],
                                                              i_user['checkIn'], i_user['checkOut'])
            if len(hotels_list) == 0:
                client.send_message(message.chat.id, 'Не нашлось отелей по вашему запросу')

            for i_hotel in hotels_list:
                try:
                    adress = i_hotel['address']['streetAddress']
                except KeyError:
                    adress = '-'
                try:
                    rating = i_hotel['guestReviews']['rating']
                except KeyError:
                    rating = '-'
                if not i_user['command']:
                    price = i_hotel[list(i_hotel.keys())[0]]['price']
                    name = i_hotel[list(i_hotel.keys())[0]]['name']
                    id = i_hotel[list(i_hotel.keys())[0]]['id']
                else:
                    price = str(i_hotel['ratePlan']['price']['exactCurrent']) + 'RUB'
                    name = i_hotel['name']
                    id = i_hotel['id']
                text = "Название отеля: {}\n" \
                       "Адресс отеля: {}\n" \
                       "Рейтнг отеля: {}\n" \
                       "Ссылка на отель: https://ru.hotels.com/{}\n" \
                       "Цена: {}\n".format(name, adress, rating, id, price)
                client.send_message(message.chat.id, text, disable_web_page_preview=True)
                with open('history.json', 'r', encoding='utf-8') as file:
                    dictionary = json.load(file)
                with open('history.json', 'w', encoding='utf-8') as file:
                    dictionary[str(message.chat.id)] = dictionary[str(message.chat.id)] + text + '*' * 30 + '\n'
                    json.dump(dictionary, file, ensure_ascii=False)
                logger.debug("Пользователь: {}\n".format(message.chat.id) + text)
                try:
                    if int(message.text) != 0:
                        photos = botrequests.get_photo.get_photo(i_hotel['id'], int(message.text))
                        if len(photos) != 0:
                            photos_list = []
                            for i_photo in photos:
                                photo_url = i_photo['baseUrl'].split('_{size}')
                                photos_list.append(InputMediaPhoto(''.join(photo_url)))
                            client.send_media_group(message.chat.id, photos_list)
                        else:
                            client.send_message(message.chat.id, 'Для данного отеля не нашлось фото.')
                except:
                    client.send_message(message.chat.id, 'Для данного отеля не нашлось фото.')
            users_list.pop(users_list.index(i_user))


client.polling(none_stop=True, interval=0)
