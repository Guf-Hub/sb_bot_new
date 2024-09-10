#!/usr/bin/env python3
# -*- coding: utf-8 -*-

boss_main_m = (
    '⬇ Персонал',
    '⬇ Отчёты',
    '⬇ Прочее',
    '⬇ Расходы',
    '📌 Справка',
    '🏬 Проекты',
)

boss_report_m = (
    '📸 За сегодня',
    '📸 За вчера',
    '📈 За сегодня',
    '📈 За месяц',
    '✅ Утренний',
    '✅ Вечерний',
    '💰 Выручка за вчера',
    '💵 Остатки сейф',
    '⬆ Выйти',
)

boss_payments_m = (
    '🏠 Отчет дом',
    '🏠 Расход',
    '🏬 Отчет проект',
    # '🏬 Проекты',
    '💸 Кофейни',
    '⬆ Выйти'
)

boss_category_m = ('🛠 Работы', '🧾 Расходы')

boss_payments_category_m = (
    'Запчасти',
    'Работы',
    'Стройматериалы',
    'Такси/доставка',
    'Автоматизация',
    'Прочее',
)

boss_home_works_m = (
    'Демонтаж',
    'Подготовка',
    'Монтаж',
    'Улица',
    'Фасад',
    'Цоколь',
    'Стены, пол',
    'Крыша',
    'Электрика',
    'Сантехника',
    'Сварка',
    'Столярка',
    'Отделка',
    'Мастерская',
    'Подряды',
    'Другое',
)

boss_home_expenses_m = (
    'Материалы',
    'Доставки',
    'Дизайн',
    'Проектировка',
    'Разрешения',
    'Мусор',
    'Быт.техника',
    'Инструмент/Оборудование',
    'Мебель',
    'Другое',
)

boss_projects_works_m = (
    'Демонтаж',
    'Монтаж',
    'Электрика',
    'Сантехника',
    'Отделка',
    'Сварка',
    'Столярка',
    'Декоратор',
    'Подряды',
    'Другое',
)

boss_projects_expenses_m = (
    'Материалы',
    'Доставки',
    'Дизайн',
    'Проектировка',
    'Разрешения',
    'Мусор',
    'Техника',
    'Мебель',
    'Мастерская',
    'Другое',
)

boss_other_m = (
    '📢 Рассылка',
    '♻ Списать',
    '🔄 Коды списаний',
    '☕ Эспрессо',
    '📩 Списания',
    '🆑 Удалить фото',
    # '🔄 Супервайзера',
    '✅ Добавить точку',
    '❌ Удалить точку',
    '⬆ Выйти',
)

boss_staff_m = (
    ('🚹 Добавить', '🚹 Обновить', '🚹 Удалить'),
    ('Кто, где сегодня', 'Кто, где завтра', 'Выходы 7 дней'),
    ('⬆ Выйти',)
)

staff_main_m = (
    '✅ Утренний',
    '✅ Вечерний',
    '📸 За сегодня',
    '📸 За вчера',
    '📈 График неделя',
    '📈 График месяц',
    '♻ Списать',
    '☕ Эспрессо',
    '📌 Справка'
)

grind_type_m = (
    'Настройка',
    'Конец смены',
    '⬆ Выйти'
)

morning_type_m = (
    'До 10',
    'До 12',
    'Настройка',
    '⬆ Выйти'
)

safe_m = (
    'Сошёлся',
    'Излишек(+)',
    'Недостача(-)',
    '❌ Отмена'
)

write_off_reasons = ('Ошибка бариста', 'Порча', 'Реклама')

# должности
company_positions = (
    'Бариста',
    'Ст. бариста',
    'Кассир',
    'Помощник',
    'Стажёр',
    'Повар',
    'Заготовщик',
    'Официант',
    'Супервайзер',
    'Администратор',
    'HR',
    'Бухгалтер',
    'Инспектор',
    'Логист',
    'Руководитель АХО',
    'Собственник',
    'Тест',
)

company_points = (
    {"name": "Балашиха", "address": "Моск. обл., г. Балашиха, ул. Советская, влд. 4Б. Кофейня Sorry Бабушка",
     "latitude": 55.796895, "longitude": 37.93474, "alias": "b"},
    {"name": "Ногинск", "address": "Моск. обл., г. Ногинск, ул. 3-го Интернационала, д.67. Кофейня Sorry Бабушка",
     "latitude": 55.855136, "longitude": 38.439721, "alias": "n"},
    {"name": "Электросталь", "address": "Моск. обл., г. Электросталь, проспект Ленина, д.45. Кофейня Sorry Бабушка",
     "latitude": 55.7862, "longitude": 38.444371, "alias": "s"},
    {"name": "Тест", "address": None, "latitude": 55.568979, "longitude": 38.235518, "alias": "t"},
    {"name": "Железнодорожный",
     "address": "Моск. обл., г. Балашиха, мкр. Железнодорожный, ул. Новая, д. 16, пом. II. Кофейня Sorry Бабушка",
     "latitude": 55.74806, "longitude": 38.01561, "alias": "z"},
    {"name": "Офис", "address": None, "alias": "o"},
    {"name": "Ногинск 2", "address": "Моск. обл., г. Ногинск, ул. 3-го Интернационала, д.52. Кофейня Sorry Бабушка",
     "alias": "n2"},
)
