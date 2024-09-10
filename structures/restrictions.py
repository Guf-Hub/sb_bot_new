class Restrictions:
    """Telegram restrictions https://limits.tginfo.me/ru-RU"""
    MESSAGE_LENGTH: int = 4096
    CAPTION_LENGTH: int = 1024
    FILE_PHOTO_SIZE: int = 5242880
    FILE_SIZE: int = 20971520

    @property
    def message_length(self) -> int:
        return self.MESSAGE_LENGTH

    @property
    def caption_length(self) -> int:
        return self.CAPTION_LENGTH

    @property
    def file_photo_size(self) -> int:
        return self.FILE_PHOTO_SIZE

    @property
    def file_size(self) -> int:
        return self.FILE_SIZE
