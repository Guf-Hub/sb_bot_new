import logging
import sys


def logging_configurate(level=logging.INFO, simple: bool = False):

    if simple:
        logging.basicConfig(level=level, stream=sys.stdout)
    else:
        file_log = logging.FileHandler("app.log", mode="a", encoding="utf-8")
        console_out = logging.StreamHandler()
        logging.basicConfig(
            level=level,
            handlers=(file_log, console_out),
            format="%(asctime)s [%(levelname)s]: %(module)s:%(funcName)s(%(lineno)d) - %(message)s",
            datefmt="%d/%m/%Y %I:%M:%S %p",

        )
