import logging

import colorlog

logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)

# 创建彩色日志处理器
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s[%(levelname)s] - %(message)s (%(pathname)s:%(lineno)d)',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))

logger.addHandler(handler)