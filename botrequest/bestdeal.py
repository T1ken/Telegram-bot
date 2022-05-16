import requests
import json
from typing import Any

from decouple import config
from loguru import logger


rapidapi_headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': config('RAPIDAPIKEY')
    }
logger.add("debug.log", format="{time} {message}", level="DEBUG", encoding='utf-8')


def get_result(
        city: str,
        max_hotel_num: int,
        min_price: int,
        max_price: int,
        min_distance: int,
        max_distance: int,
        check_in: str,
        check_out: str
) -> Any:
    hotels_list = []
    any_hotel_found = False
    url = "https://hotels4.p.rapidapi.com/locations/search"
    querystring = {"query": city, "locale": "ru_RU"}
    headers = rapidapi_headers
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)

    for i_elem in response['suggestions']:
        for i_hotel in i_elem['entities']:
            hotel_dict = dict()

            hotel_dict['id'] = i_hotel['destinationId']
            url = "https://hotels4.p.rapidapi.com/properties/list"
            querystring = {"destinationId": i_hotel['destinationId'], "pageNumber": "1", "pageSize": "25",
                           "checkIn": check_in,
                           "checkOut": check_out, "adults1": "1", "sortOrder": "PRICE", "locale": "ru_RU",
                           "currency": "RUB"}
            response_1 = requests.request("GET", url, headers=headers, params=querystring)
            try:
                response_1 = json.loads(response_1.text)
                if response_1['result'] != 'ERROR':
                    if response_1['result'] != 'ERROR':
                        any_hotel_found = True
                list_result = response_1['data']['body']['searchResults']['results']
                hotel_dict = {hotel['name']: {'id': hotel.get('id', '-'), 'name': hotel.get('name', '-'),
                                              'address': hotel.get('address', '-'),
                                              'distance': hotel['landmarks'][0]['distance'],
                                              'price': hotel['ratePlan']['price'].get('current')
                                              if hotel.get('ratePlan', None) else '-',
                                              'coordinate': '+'.join(map(str, hotel['coordinate'].values()))}
                              for hotel in list_result}
            except:
                continue
            hotels_list.append(hotel_dict)

    final_hotels_list = []

    for i_hotel in hotels_list:
        if i_hotel[list(i_hotel.keys())[0]]['price'] != '-':
            i_hotel_price = float('.'.join(i_hotel[list(i_hotel.keys())[0]]['price'].split(' R')[0].split(',')))
            i_hotel_distance = float('.'.join(i_hotel[list(i_hotel.keys())[0]]['distance'].split(' к')[0].split(',')))
            if min_price <= i_hotel_price <= max_price and min_distance <= i_hotel_distance <= max_distance:
                final_hotels_list.append(i_hotel)
                if len(final_hotels_list) == max_hotel_num:
                    break

    if len(final_hotels_list) == 0:
        if not any_hotel_found:
            logger.error('Не нашлось отелей. Причина: все результаты запроса к API hotels.com вернули ошибку.')
        else:
            logger.error('Не нашлось отелей. '
                         'Причина: все найденные результаты не удовлетворяют условиям, введёнными пользователем.')

    return final_hotels_list
