"""
日志系统模块

提供统一的日志记录功能，支持文件和控制台输出
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name='contest-eval', log_file='logs/app.log'):
    """
    设置日志系统
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径
    
    Returns:
        logger: 配置好的日志器
    """
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 文件处理器 - 轮转日志文件
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 全局日志实例
logger = setup_logger()


def get_logger(module_name=None):
    """
    获取日志实例
    
    Args:
        module_name: 模块名称（可选）
    
    Returns:
        logger: 日志实例
    """
    if module_name:
        return logging.getLogger(f'contest-eval.{module_name}')
    return logger
