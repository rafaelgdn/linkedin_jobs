import colorlog
import logging

SUCCESS = 25
SKIP = 15


class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

        logging.addLevelName(SUCCESS, "SUCCESS")
        logging.addLevelName(SKIP, "SKIP")

    def success(self, msg, *args, **kwargs):
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)

    def skip(self, msg, *args, **kwargs):
        if self.isEnabledFor(SKIP):
            self._log(SKIP, msg, args, **kwargs)


logging.setLoggerClass(CustomLogger)

logger = colorlog.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = colorlog.StreamHandler()

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "light_black",
        "SUCCESS": "green",
        "SKIP": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={},
    style="%",
)

handler.setFormatter(formatter)
logger.addHandler(handler)

__all__ = ["logger"]
