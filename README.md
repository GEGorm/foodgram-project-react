# Foodgram
Foodgram

# Расположение
http://51.250.25.85  
Логин: root  
Пароль: root  

### Об авторе.

Гормулинский Геннадий  
gormulinskiy@gmail.com  
YANDEX Practicum  

### О проекте

Проект Foodgram предоставляет сервис для публикации рецептов пользователями. 
В рецепте возможно указать:
  - состав ингридиентов
  - описание
  - фото блюда
  - время приготовления
  - тэги
Пользователь может подписывать на других пользователей, и следить за их обновлениями.
Также рецепты можно добавлять в избранное, и список покупок из которого можно сформировать общий список необходимых ингридиентов.

### Установка для тестирования api проекта
Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/GEGorm/foodgram-project-react
```

```bash
cd "директория проекта"
```

Cоздать и активировать виртуальное окружение:

```bash
python3 -m venv env
```

```bash
source venv/bin/activate
```

```bash
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```bash
pip install -r backend/foodgram/requirements.txt
```

Выполнить миграции:

```bash
python3 manage.py migrate
```

Запустить проект:

```bash
python3 manage.py runserver
