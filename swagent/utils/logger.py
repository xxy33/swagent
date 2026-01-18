"""
日志系统模块
负责配置和管理日志输出
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class Logger:
    """日志管理类"""

    _loggers = {}

    @classmethod
    def get_logger(cls, name: str = "swagent", config: Optional[dict] = None) -> logging.Logger:
        """
        获取logger实例

        Args:
            name: logger名称
            config: 日志配置字典

        Returns:
            logging.Logger实例
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)

        # 避免重复添加handler
        if logger.handlers:
            cls._loggers[name] = logger
            return logger

        # 加载配置
        if config is None:
            from swagent.utils.config import get_config
            config = get_config().get('logging', {})

        # 设置日志级别
        level_name = config.get('level', 'INFO')
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)

        # 日志格式
        log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')

        # 控制台输出
        console_config = config.get('console', {})
        if console_config.get('enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            # 彩色日志
            if COLORLOG_AVAILABLE and console_config.get('colored', True):
                color_format = '%(log_color)s' + log_format
                formatter = colorlog.ColoredFormatter(
                    color_format,
                    datefmt=date_format,
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            else:
                formatter = logging.Formatter(log_format, datefmt=date_format)

            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 文件输出
        file_config = config.get('file', {})
        if file_config.get('enabled', False):
            log_path = file_config.get('path', './logs/swagent.log')
            log_file = Path(log_path)

            # 创建日志目录
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # 解析文件大小
            max_bytes = cls._parse_size(file_config.get('max_size', '10MB'))
            backup_count = file_config.get('backup_count', 5)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=file_config.get('encoding', 'utf-8')
            )
            file_handler.setLevel(level)

            file_formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # 避免日志向上传播
        logger.propagate = False

        cls._loggers[name] = logger
        return logger

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """
        解析大小字符串

        Args:
            size_str: 如 "10MB", "1GB"

        Returns:
            字节数
        """
        size_str = size_str.strip().upper()
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
        }

        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    value = float(size_str[:-len(unit)])
                    return int(value * multiplier)
                except ValueError:
                    pass

        # 默认按字节处理
        try:
            return int(size_str)
        except ValueError:
            return 10 * 1024 * 1024  # 默认10MB


def setup_logger(name: str = "swagent", config: Optional[dict] = None) -> logging.Logger:
    """
    设置logger

    Args:
        name: logger名称
        config: 日志配置

    Returns:
        logging.Logger实例
    """
    return Logger.get_logger(name, config)


def get_logger(name: str = "swagent") -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称

    Returns:
        logging.Logger实例
    """
    return Logger.get_logger(name)
