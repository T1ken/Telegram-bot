import requests
import json

from decouple import config
from loguru import logger


rapidapi_headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': config('RAPIDAPIKEY')
    }
logger.add("debug.log", format="{time} {message}", level="DEBUG", encoding='utf-8')


def get_photo(
        hotel_id: str,
        max_count: int
) -> list:
    photos_address = []
    error = False
    querystring = {"id": hotel_id}
    try:
        response = requests.request(
            "GET",
            'https://hotels4.p.rapidapi.com/properties/get-hotel-photos',
            headers=rapidapi_headers,
            params=querystring,
            timeout=10
        )
        photo_data = json.loads(response.text)
        photos_address = photo_data["hotelImages"][:max_count]
    except:
        logger.error('На отель не нашлось фото. Предпологаемая причина: Сайт ответил ошибкой Error 404')
        error = True

    if len(photos_address) == 0 and not error:
        logger.error('На отель не нашлось фото. Причина: их нет на сайте hotels.com')

    return photos_address
