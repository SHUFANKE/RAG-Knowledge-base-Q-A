import logging
import sys

def setup_logger():
    """配置工业级控制台结构化日志"""
    logger = logging.getLogger("rag_service")
    logger.setLevel(logging.INFO)

    #避免热重载时重复添加Handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [RAG-Core] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()