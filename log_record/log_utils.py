# -*- coding: utf-8 -*-
# @Author: Bi Ying
# @Date:   2023-05-15 01:26:36
# @Last Modified by:   Bi Ying
# @Last Modified time: 2023-05-15 11:21:39
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from functools import wraps

# 获取程序根目录的绝对路径
ROOT_DIR = Path(__file__).parent.parent
LOG_DIR = ROOT_DIR / "log"

# 创建日志目录
LOG_DIR.mkdir(exist_ok=True)

class YunyingLogger:
    def __init__(self):
        self.logger = logging.getLogger("yunying")
        self.logger.setLevel(logging.DEBUG)
        
        # 日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(serial)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 文件处理器
        log_file = LOG_DIR / "yunying.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            str(log_file),
            when="D",
            interval=1,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _log(self, level, serial, message):
        """统一的日志记录方法"""
        extra = {'serial': serial}
        self.logger.log(level, message, extra={'serial': serial})

    def info(self, serial, message):
        """记录 INFO 级别日志"""
        self._log(logging.INFO, serial, message)

    def error(self, serial, message):
        """记录 ERROR 级别日志"""
        self._log(logging.ERROR, serial, message)

    def debug(self, serial, message):
        """记录 DEBUG 级别日志"""
        self._log(logging.DEBUG, serial, message)

    def warning(self, serial, message):
        """记录 WARNING 级别日志"""
        self._log(logging.WARNING, serial, message)

# 创建全局logger实例
yunying_logger = YunyingLogger()
