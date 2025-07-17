import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    ログ出力（ファイルとコンソール）の設定を行う
    """
    # メインのロガーを取得し、重複してハンドラが追加されるのを防ぐ
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.DEBUG)

    # 1. ファイルハンドラの設定
    file_handler = logging.FileHandler('debug.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 2. コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # ロガーにハンドラを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
