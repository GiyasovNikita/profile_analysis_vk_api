import requests
import logging
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

# Загрузка переменных из файла .env
load_dotenv()

# Настройка подключения к Neo4j
neo4j_url = "bolt://localhost:7687"
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Получение access token из переменной среды
access_token = os.getenv('VK_ACCESS_TOKEN')

# Базовый URL для обращения к API ВКонтакте
VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.131"

# Определяем параметры для работы
user_id_input = '157602944'  # Задайте ID пользователя ВК (замените на нужный)

# Инициализация клиента Neo4j
driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))


# Функция для выполнения запроса к VK API
def vk_api_request(method, params):
    params['access_token'] = access_token
    params['v'] = VK_API_VERSION
    params['lang'] = 'ru'
    response = requests.get(VK_API_URL + method, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            logger.error(f"VK API error: {data['error']['error_msg']}")
            return None
        return data['response']
    else:
        logger.error(f"HTTP error: {response.status_code} - {response.text}")
        return None



def close_driver():
    driver.close()


def get_user_data(user_id):
    params = {
        "user_ids": user_id,
        "fields": "first_name,last_name,sex,home_town,city,screen_name"
    }
    return vk_api_request("users.get", params)


def get_followers(user_id):
    params = {
        "user_id": user_id
    }
    return vk_api_request("users.getFollowers", params)


def get_followers_info(follower_ids):
    params = {
        "user_ids": ",".join(map(str, follower_ids)),
        "fields": "first_name,last_name,sex,home_town,city,screen_name"
    }
    return vk_api_request("users.get", params)


def get_subscriptions(user_id):
    params = {
        "user_id": user_id,
        "extended": 1
    }
    return vk_api_request("users.getSubscriptions", params)


def get_groups_info(group_ids):
    params = {
        "group_ids": ",".join(map(str, group_ids)),
        "fields": "name,screen_name"
    }
    return vk_api_request("groups.getById", params)


def save_user(tx, user):
    city = user.get('city', {}).get('title', '')
    home_town = user.get('home_town', '') or city

    tx.run(
        """
        MERGE (u:User {id: $id})
        SET u.screen_name = $screen_name,
            u.name = $name,
            u.sex = $sex,
            u.home_town = $home_town
        """,
        id=user['id'],
        screen_name=user.get('screen_name', ''),
        name=f"{user.get('first_name', '')} {user.get('last_name', '')}",
        sex=user.get('sex', ''),
        home_town=home_town
    )


def save_group(tx, group):
    tx.run(
        """
        MERGE (g:Group {id: $id})
        SET g.name = $name, g.screen_name = $screen_name
        """,
        id=group['id'],
        name=group.get('name', ''),
        screen_name=group.get('screen_name', '')
    )


def create_relationship(tx, user_id, target_id, rel_type):
    tx.run(
        f"""
        MATCH (u:User {{id: $user_id}})
        MATCH (target {{id: $target_id}})
        MERGE (u)-[:{rel_type}]->(target)
        """,
        user_id=user_id, target_id=target_id
    )
    logger.info(f"Связь {rel_type} создана между {user_id} и {target_id}")


def process_user(user_id, level, max_level, max_users=200):
    queue = [(user_id, level)]
    visited = set()
    processed_count = 0

    while queue:
        current_id, current_level = queue.pop(0)

        if current_id in visited or current_level > max_level:
            continue
        visited.add(current_id)
        processed_count += 1

        # Прерываем, если достигли лимита на количество узлов
        if processed_count > max_users:
            logger.info("Достигнут лимит обработки узлов.")
            break

        user_data = get_user_data(current_id)
        if user_data is None:
            logger.warning(f"Не удалось получить данные для пользователя {current_id}")
            continue
        user_info = user_data[0]

        with driver.session() as session:
            session.execute_write(save_user, user_info)
            logger.info(f"Добавлен пользователь {user_info['id']} на уровне {current_level}")

            # Получаем и сохраняем фолловеров
            followers_data = get_followers(current_id)
            if followers_data:
                follower_ids = followers_data['items']
                followers_info = get_followers_info(follower_ids)
                for follower in followers_info:
                    if follower['id'] not in visited:
                        session.execute_write(save_user, follower)
                        session.execute_write(create_relationship, follower['id'], current_id, "Follow")
                        queue.append((follower['id'], current_level + 1))
                        logger.info(f"Добавлен фолловер {follower['id']} для пользователя {current_id} на уровне {current_level + 1}")

            # Получаем и сохраняем подписки
            subscriptions_data = get_subscriptions(current_id)
            if subscriptions_data and 'items' in subscriptions_data:
                user_group_ids = [sub['id'] for sub in subscriptions_data['items'] if sub.get('type') == 'page']
                if user_group_ids:
                    groups_info = get_groups_info(user_group_ids)
                    for group in groups_info:
                        if group['id'] not in visited:
                            session.execute_write(save_group, group)
                            session.execute_write(create_relationship, current_id, group['id'], "Subscribe")
                            logger.info(f"Добавлена подписка на группу {group['id']} для пользователя {current_id}")

        logger.info(f"Уровень {current_level} обработан для пользователя {current_id}. Переход на уровень {current_level + 1}.\n")

    logger.info("Обработка фолловеров и подписок завершена.")


def main():
    if not access_token:
        logger.error("Токен VK API не задан")
        return

    user_data = get_user_data(user_id_input)
    logger.info(f"Полученные данные пользователя: {user_data}")

    if user_data:
        user_info = user_data[0]
        user_id = user_info['id']
        max_level = 2
        process_user(user_id, 0, max_level)
    else:
        logger.error("Не удалось получить данные пользователя")


    close_driver()


if __name__ == "__main__":
    main()