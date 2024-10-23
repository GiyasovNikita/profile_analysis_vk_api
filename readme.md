# VK User Data Collector

## Описание
Простое консольное приложение на Python, которое использует API ВКонтакте для получения информации о пользователе, его фолловерах и подписках, и сохраняет данные в JSON-файл.

## Установка и запуск

### Шаг 1: Установите зависимости
Перед использованием скрипта необходимо установить зависимости:

1. Установите Python 3.x, если он ещё не установлен.
2. Установите необходимые библиотеки:
   ```bash
   pip install requests python-dotenv
   ```
### Шаг 2: Получите Access Token для VK API
Зарегистрируйте приложение ВКонтакте через VK Developer для получения токена доступа.
После создания приложения получите access token, который необходимо сохранить в переменной среды.
### Шаг 3: Настройте .env файл
Создайте файл .env в корневом каталоге проекта и добавьте в него ваш VK API token:

```env
VK_ACCESS_TOKEN=ваш_токен_доступа
```
### Шаг 4: Запуск программы
Убедитесь, что все зависимости установлены и токен сохранён в .env файле.
Запустите скрипт:
```bash
python script.py
```
По умолчанию скрипт использует ID пользователя 157602944 и сохраняет результат в файл output.json.

### Изменение параметров
Чтобы изменить ID пользователя, отредактируйте переменную user_id в коде скрипта.
Чтобы изменить путь сохранения JSON-файла, отредактируйте переменную output_file в коде.
## Результат
Результаты работы программы будут сохранены в указанном файле в формате JSON с отступами и поддержкой кириллического текста. Пример содержимого файла:

```json
{
    "user_info": {
        "id": 157602944,
        "first_name": "Иван",
        "last_name": "Иванов"
    },
    "followers": [...],
    "subscriptions": [...]
}
```
## Описание функций
vk_api_request: Выполняет запрос к API ВКонтакте с передачей необходимых параметров и токена доступа.
save_to_json: Сохраняет данные в указанный JSON файл.
get_vk_data: Получает информацию о пользователе, его фолловерах и подписках через методы API ВКонтакте.