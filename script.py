import requests
import json
from dotenv import load_dotenv
import os

# Загрузка переменных из файла .env
load_dotenv()

# Получение access token из переменной среды
access_token = os.getenv('VK_ACCESS_TOKEN')

# Базовый URL для обращения к API ВКонтакте
VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.131"

# Определяем параметры для работы
user_id = '157602944'  # Задайте ID пользователя ВК (замените на нужный)
output_file = 'output.json'  # Укажите название файла JSON для сохранения данных


# Функция для выполнения запроса к VK API
def vk_api_request(method, params):
    params['access_token'] = access_token
    params['v'] = VK_API_VERSION
    params['lang'] = 'ru'
    response = requests.get(VK_API_URL + method, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            raise Exception(f"VK API error: {data['error']['error_msg']}")
        return data['response']
    else:
        raise Exception(f"HTTP error: {response.status_code}")


# Функция для сохранения данных в JSON
def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {output_file}")


# Функция для получения информации о пользователе, фолловерах, подписках
def get_vk_data(user_id):
    # Получаем информацию о пользователе
    if not user_id.isdigit():
        user_info = vk_api_request('users.get', {'user_ids': user_id})
        user_id = user_info[0]['id']
    else:
        user_info = vk_api_request('users.get', {'user_ids': user_id})
        user_info = user_info[0]

    # Получение подписчиков
    followers = vk_api_request('users.getFollowers', {'user_id': user_id})['items']

    # Получение подписок
    subscriptions = vk_api_request('users.getSubscriptions', {'user_id': user_id, 'extended': 1, 'count': 200})['items']

    data = {
        'user_info': user_info,
        'followers': followers,
        'subscriptions': subscriptions
    }
    return data


def main():
    try:
        data = get_vk_data(user_id)
        save_to_json(data, output_file)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
