import argparse
from neo4j import GraphDatabase
import logging
import os
from dotenv import load_dotenv

# Загрузка переменных из файла .env
load_dotenv()

# Настройка подключения к Neo4j
neo4j_url = "bolt://localhost:7687"
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Инициализация клиента Neo4j
driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))


def execute_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record for record in result]


# Возвращает общее количество пользователей
def get_total_users():
    query = "MATCH (u:User) RETURN count(u) AS total_users"
    result = execute_query(query)
    print("Total Users:", result[0]["total_users"])


# Возвращает общее количество групп
def get_total_groups():
    query = "MATCH (g:Group) RETURN count(g) AS total_groups"
    result = execute_query(query)
    print("Total Groups:", result[0]["total_groups"])


# Возвращает топ 5 пользователей по количеству фолловеров
def get_top_5_users_by_followers():
    query = """
    MATCH (u:User)<-[:Follow]-(follower:User)
    RETURN u.id AS user_id, count(follower) AS followers_count
    ORDER BY followers_count DESC
    LIMIT 5
    """
    result = execute_query(query)
    print("Top 5 Users by Followers:")
    for record in result:
        print(f"User ID: {record['user_id']}, Followers Count: {record['followers_count']}")


# Возвращает топ 5 самых популярных групп
def get_top_5_popular_groups():
    query = """
    MATCH (g:Group)<-[:Subscribe]-(u:User)
    RETURN g.id AS group_id, count(u) AS subscribers_count
    ORDER BY subscribers_count DESC
    LIMIT 5
    """
    result = execute_query(query)
    print("Top 5 Popular Groups:")
    for record in result:
        print(f"Group ID: {record['group_id']}, Subscribers Count: {record['subscribers_count']}")


# Возвращает всех пользователей, которые фолловеры друг друга
def get_mutual_followers():
    query = """
    MATCH (u1:User)-[:Follow]->(u2:User), (u2)-[:Follow]->(u1)
    RETURN u1.id AS user1_id, u2.id AS user2_id
    """
    result = execute_query(query)
    print("Mutual Followers:")
    for record in result:
        print(f"User1 ID: {record['user1_id']} is a mutual follower with User2 ID: {record['user2_id']}")


def main():
    parser = argparse.ArgumentParser(description="Neo4j Social Network Queries")
    parser.add_argument('--total_users', action='store_true', help="Get total number of users")
    parser.add_argument('--total_groups', action='store_true', help="Get total number of groups")
    parser.add_argument('--top_users', action='store_true', help="Get top 5 users by number of followers")
    parser.add_argument('--top_groups', action='store_true', help="Get top 5 most popular groups")
    parser.add_argument('--mutual_followers', action='store_true', help="Get all mutual followers")

    args = parser.parse_args()

    if args.total_users:
        get_total_users()
    if args.total_groups:
        get_total_groups()
    if args.top_users:
        get_top_5_users_by_followers()
    if args.top_groups:
        get_top_5_popular_groups()
    if args.mutual_followers:
        get_mutual_followers()


if __name__ == "__main__":
    main()
