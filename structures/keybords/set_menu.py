#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from typing import List

from aiogram import Dispatcher
from aiogram.types import BotCommandScopeChat, BotCommand
from aiogram.exceptions import TelegramAPIError

commands_staff = [
    BotCommand(command='/start', description='запуск бота'),
    BotCommand(command='/my_id', description='твой id'),
    BotCommand(command='/help', description='справка'),
    BotCommand(command='/cancel', description='отменить действие')]

commands_admin = [
    BotCommand(command='/start', description='запуск бота (если меню потеряется)'),
    BotCommand(command='/cancel', description='отменить действие'),
    BotCommand(command='/my_id', description='мой id'),
    BotCommand(command='/help', description='справка'),
    BotCommand(command='/log', description='лог программы'),
    BotCommand(command='/db', description='получить bot.db')]


async def set_commands_menu(dp: Dispatcher,
                            staff_commands: List[BotCommand] = None,
                            admin_ids: List[int] = None,
                            admin_commands: List[BotCommand] = None):
    """Установка меню команд для бота"""
    from database.db import db
    for user_id in set(x[0] for x in db.get_active()):
        try:
            await dp.bot.delete_my_commands(scope=BotCommandScopeChat(user_id))
        except ChatNotFound as e:
            logging.error(f"Удаление меню команд {user_id}: {e}")

    if staff_commands:
        await dp.bot.set_my_commands(commands=staff_commands)

    if admin_ids:
        for admin_id in admin_ids:
            try:
                await dp.bot.set_my_commands(
                    commands=admin_commands,
                    scope=BotCommandScopeChat(admin_id)
                )
            except ChatNotFound as e:
                logging.error(f"Установка команд для администратора {admin_id}: {e}")
