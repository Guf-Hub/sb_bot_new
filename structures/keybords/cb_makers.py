from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def create_inline_kb(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def create_inline_url_kb(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()


def create_inline_mix_kb(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))

    return keyboard.adjust(*sizes).as_markup()


def create_kb(btns: list | tuple,
              sizes: tuple[int] = (2,),
              input_field_placeholder='Выбери нужное 👇',
              **kwargs
              ) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(*(KeyboardButton(text=text) for text in btns))
    builder.adjust(*sizes)
    return builder.as_markup(
        **kwargs,
        input_field_placeholder=input_field_placeholder,
        resize_keyboard=True,
        one_time_keyboard=True,
    )
