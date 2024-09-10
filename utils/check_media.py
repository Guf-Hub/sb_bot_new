# -*- coding: utf-8 -*-
__all__ = ["media_create"]

from aiogram.utils.media_group import MediaGroupBuilder

from core.bot import bot

VALID_EXTENSIONS = {
    'photo': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    'video': ['mp4', 'mov', 'avi', 'wmv', 'webm'],
    'audio': ['mp3'],
}


async def _check_file_extension(file_id: str) -> str:
    file_info = await bot.get_file(file_id)
    file_extension = file_info.file_path.split(".")[-1].lower()

    for ext, values in VALID_EXTENSIONS.items():
        if file_extension in values:
            return ext
    return 'document'


async def media_create(args, caption: str = None) -> list:
    media_group = MediaGroupBuilder(caption=caption)

    file_ids = args if isinstance(args, list) else [v for k, v in args.items() if 'file' in str(k) and v]

    if file_ids:
        for file_id in file_ids:
            extension = await _check_file_extension(file_id)
            media_group.add(type=extension, media=file_id)

    return media_group.build()
