#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiogram.types import BotCommandScopeChat, BotCommand

commands_staff = [
    BotCommand(command='/start', description='запуск бота (если меню потеряется)'),
    BotCommand(command='/my_id', description='мой id'),
    BotCommand(command='/help', description='справка'),
    BotCommand(command='/cancel', description='отменить действие'),
]

commands_admin = [
    BotCommand(command='/start', description='запуск бота (если меню потеряется)'),
    BotCommand(command='/cancel', description='отменить действие'),
    BotCommand(command='/my_id', description='мой id'),
    BotCommand(command='/help', description='справка'),
    BotCommand(command='/log', description='лог программы'),
    BotCommand(command='/db_sqlite', description='получить bot.db'),
]
