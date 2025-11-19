"""日志模块"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(
    name: str = "rt-voicechat",
    level: str = "INFO",
    log_file: str = None,
    console: bool = True,
    max_size: str = "10MB",
    backup_count: int = 3
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        console: 是否输出到控制台
        max_size: 日志文件最大大小
        backup_count: 备份文件数量
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = ColoredFormatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 解析文件大小
        size_map = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        max_bytes = 10 * 1024 * 1024  # 默认 10MB
        
        for unit, multiplier in size_map.items():
            if unit in max_size.upper():
                size_value = float(max_size.upper().replace(unit, ''))
                max_bytes = int(size_value * multiplier)
                break
        
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为None则返回根日志记录器
    
    Returns:
        日志记录器
    """
    if name:
        return logging.getLogger(f"rt-voicechat.{name}")
    return logging.getLogger("rt-voicechat")
