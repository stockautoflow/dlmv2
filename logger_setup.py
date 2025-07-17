import logging
import os
from datetime import datetime

def setup_logging():
    """
    ログ出力（ファイルとコンソール）の設定を行う
    """
    # メインのロガーを取得し、重複してハンドラが追加されるのを防ぐ
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.DEBUG)

    # logディレクトリを作成 (存在しない場合)
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)

    # タイムスタンプ付きのファイル名を生成
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_filename = os.path.join(log_dir, f"log_{timestamp}_.txt")


    # ファイルハンドラの設定
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # ロガーにハンドラを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)