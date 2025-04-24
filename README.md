# Проект Pythia Parser Mississippy

## Установка и запуск

### 1. Клонирование репозитория

Сначала клонируем репозиторий:

```bash
git clone https://github.com/your-username/pythia-parser.git
cd pythia-parser
```

### 2. Создание виртуального окружения

Создаем виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

Устанавливаем все необходимые библиотеки и зависимости, указанные в `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Запуск приложения

После установки всех зависимостей и настройки переменных окружения, запускаем скрипт `Pythia_parser_MS.py`:

```bash
python Pythia_parser_MS.py
```

Скрипт будет слушать очередь RabbitMQ и обрабатывать входящие сообщения.

## Примечание

- Для работы с RabbitMQ необходимо, чтобы сервер RabbitMQ был доступен по адресу, указанному в `.env` файле.
