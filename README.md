https://github.com/luchanos/luchanos_oxford_university
https://docs.docker.com/desktop/install/linux-install/

```bash
docker-compose -f docker-compose-local.yaml up -d
```

```bash
docker ps
```

### Список установленных программ диск С Windows

```bash
 wmic product get name > installed_programs.txt
```

### PIP

```bash
pip freeze > requirements.txt
```

### Poetry

[Команды](https://python-poetry.org/docs/basic-usage/)

### First, let’s create our new project, let’s call it poetry-demo

```bash
poetry new <PROJECT NAME>
```

### Инициализация уже существующего проекта

```bash
poetry init
```

### Установка версий

Мы запрашиваем _pendulum_ пакет с ограничением версии ^2.1.

Это означает любую версию, большую или равную 2.1.0, но меньше 3.0.0 (>=2.1.0 <3.0.0).

```bash
poetry add <PACEGE NAME>
```

### Запустить скрипт

```bash
poetry run python <SCRIPT NAME>.py
```

### Активация виртуальной среды

```bash
poetry shell
```

### Установка зависимостей

Чтобы установить определенные зависимости для вашего проекта, просто запустите install команду.

```bash
poetry poetry install
```

### Установка только зависимостей

По умолчанию текущий проект устанавливается в редактируемом режиме.

Если вы хотите установить только зависимости, запустите install команду с --no-rootфлагом:

```bash
poetry install --no-root
```

### Обновление зависимостей до последних версий

```bash
poetry update
```
### В requirements.txt

```bash
poetry export --without-hashes --without dev --format=requirements.txt > requirements.txt
```

## Git

[Команды](https://www.atlassian.com/ru/git/glossary#commands)

Инициализировать новый репозиторий Git

```bash
git init
```

Проверить статус (показывает состояния файлов в рабочем каталоге и индексе: какие файлы изменены, но не добавлены в
индекс; какие ожидают коммита в индексе)

```bash
git status
```

Создать README.md

```bash
git add README.md
```

Добавить файлы (добавляет содержимое рабочего каталога в индекс (staging area) для последующего коммита)

```bash
git add .
```

Отменить изменения

```bash
git reset
```

Удаление файлов из индекса и рабочей копии (похожа на git add с тем лишь исключением, что она удаляет, а не добавляет
файлы для следующего коммита)

```bash
git rm
```

Удаление файлов из индекса и рабочей копии

```bash
git rm --cached <file_name>
```

Удаление мусора из рабочего каталога

```bash
git clean
```

Сделать коммит

```bash
git commit -m "first commit"
```

Опубликовать

```bash
git push -u origin main
```

Копировать существующий репозитория Git

```bash
git clone <name>
```

Настройки параметров конфигурации в инсталляции Git

```bash
git config
```

Изучить предыдущие версии проекта

```bash
git log
```

Create a new repository on the command line

```bash
echo "# wbserf" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/Guf-Hub/sb_bot_new.git
git push -u origin main
```

Push an existing repository from the command line

```bash
git remote add origin https://github.com/Guf-Hub/git
git branch -M main
git push -u origin main
```

## Установить время на сервере

```bash
sudo timedatectl set-timezone Europe/Moscow
```

## Проверить установку

```bash
timedatectl
```

## Django

```bash
python -m pip install Django
```

```bash
django-admin --version
```

Creating a project

```bash
django-admin startproject <name>
```

The development server

```bash
python manage.py runserver
```
