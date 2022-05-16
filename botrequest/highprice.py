import requests
import json

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
        check_in: str,
        check_out: str
) -> list:
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
            querystring = {
                "destinationId": i_hotel['destinationId'],
                "pageNumber": "1",
                "pageSize": "25",
                "checkIn": check_in,
                "checkOut": check_out,
                "adults1": "1",
                "sortOrder": "PRICE_HIGHEST_FIRST",
                "locale": "ru_RU",
                "currency": "RUB",
            }
            headers = rapidapi_headers
            response_1 = requests.request("GET", url, headers=headers, params=querystring)
            try:
                response_1 = json.loads(response_1.text)
                if response_1['result'] != 'ERROR':
                    any_hotel_found = True
                hotels_list = response_1['data']['body']['searchResults']['results']
                hotel_dict = {hotel['name']: {'id': hotel.get('id', '-'), 'name': hotel.get('name', '-'),
                                              'address': hotel.get('address', '-'),
                                              'price': hotel['ratePlan']['price'].get('current')
                                              if hotel.get('ratePlan', None) else '-',
                                              'coordinate': '+'.join(map(str, hotel['coordinate'].values()))}
                              for hotel in hotels_list}
                lst = hotel_dict['distance'].split()
                hotel_dict['distance'] = float(lst[0])
            except:
                continue
            hotels_list.append(hotel_dict)

    final_hotels_list = []
    max_price = -1

    for i_hotel in hotels_list:
        if i_hotel['ratePlan']['price']['exactCurrent'] >= max_price or len(final_hotels_list) < max_hotel_num:
            if i_hotel['ratePlan']['price']['exactCurrent'] > max_price:
                max_price = i_hotel['ratePlan']['price']['exactCurrent']
            final_hotels_list.append(i_hotel)
            if len(final_hotels_list) > max_hotel_num:
                min_price = 99999999999999999999999999
                index = None
                for i_elem in final_hotels_list:
                    if i_elem['ratePlan']['price']['exactCurrent'] < min_price:
                        min_price = i_elem['ratePlan']['price']['exactCurrent']
                        index = final_hotels_list.index(i_elem)
                final_hotels_list.pop(index)

    if len(final_hotels_list) == 0:
        if not any_hotel_found:
            logger.error('Не нашлось отелей. Причина: все результаты запроса к API hotels.com вернули ошибку.')
        else:
            logger.error('Не нашлось отелей. Причина неизвестна.')

    return final_hotels_list
