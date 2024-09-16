# avito-fastapi
Тестовое задание для Авито на стажировку для бэкенд разработчиков

Проект написан на FastAPI, с подключением к базе данных Postgres через переменные окружения.

# Запущенный проект на codenrock.com. 
Ссылка ведет на автоматическую документацию docs из fastapi приложения
[avito-fastapi](https://cnrprod1725720661-team-79228-32434.avito2024.codenrock.com/docs)

# Инструкция для запуска FastAPI приложения

## Структура проекта
```plaintext
.
├── bids.py
├── database.py
├── Dockerfile
├── main.py
├── models.py
├── requirements.txt
├── schemas.py
└── tenders.py
```

## Способ 1: Развертывание через Docker

### Предварительные требования:
- Установленный [Docker](https://www.docker.com/get-started).
- База данных должна быть настроена и доступна, а также должны быть заданы переменные окружения для подключения к базе данных. Если переменные окружения не заданы, но существует и запущена база данных, необходимо ввести данные для подключения к ней в файл database.py. Пример таких данных: 

```plaintext
      os.environ["POSTGRES_USERNAME"] = "postgres"
      os.environ["POSTGRES_PASSWORD"] = "1234"
      os.environ["POSTGRES_HOST"] = "localhost"
      os.environ["POSTGRES_PORT"] = "5432"
      os.environ["POSTGRES_DATABASE"] = "postgres"
```

### Шаги для запуска:
1. Скачайте или клонируйте репозиторий:
    ```bash
    git clone https://github.com/IvanC0tleta/avito-fastapi.git
    ```

2. Задайте необходимые переменными окружения для подключения к базе данных или введите их вручную в файл database.py:
    ```plaintext
      os.environ["POSTGRES_USERNAME"] = "postgres"
      os.environ["POSTGRES_PASSWORD"] = "1234"
      os.environ["POSTGRES_HOST"] = "localhost"
      os.environ["POSTGRES_PORT"] = "5432"
      os.environ["POSTGRES_DATABASE"] = "postgres"
    ```

3. Запустите Docker контейнер:
    ```bash
    docker build -t fastapi-app .
    ```

4. Проверьте, что приложение работает, открыв браузер по адресу:
    ```plaintext
    http://localhost:8080
    ```

5. Удобнее всего тестировать приложение через автоматическую документацию fastapi:
    ```plaintext
    http://localhost:8080/docs
    ```

## Способ 2: Развертывание без Docker

### Предварительные требования:
- Установленный [Python 3.10](https://www.python.org/downloads/).
- Установленный [pip](https://pip.pypa.io/en/stable/installation/).
- Настроенная база данных.
- Виртуальное окружение (рекомендуется).

### Шаги для запуска:
1. Скачайте или клонируйте репозиторий::
    ```bash
    git clone https://github.com/IvanC0tleta/avito-fastapi.git
    ```

2. Создайте и активируйте виртуальное окружение:
    - На Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    - На macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4. Задайте необходимые переменными окружения для подключения к базе данных или введите их вручную в файл database.py:
    ```plaintext
      os.environ["POSTGRES_USERNAME"] = "postgres"
      os.environ["POSTGRES_PASSWORD"] = "1234"
      os.environ["POSTGRES_HOST"] = "localhost"
      os.environ["POSTGRES_PORT"] = "5432"
      os.environ["POSTGRES_DATABASE"] = "postgres"
    ```

5. Запустите приложение:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080
    ```

6. Проверьте, что приложение работает по адресу:
    ```plaintext
    http://localhost:8080
    ```
7. Удобнее всего тестировать приложение через автоматическую документацию fastapi:
    ```plaintext
    http://localhost:8080/docs
    ```
