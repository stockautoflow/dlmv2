import logging
import os
from datetime import datetime

# TRACEレベルを定義 (DEBUGより詳細)
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)
logging.Logger.trace = trace

def setup_logging():
    """
    ログ出力（ファイルとコンソール）の設定を行う
    """
    # メインのロガーを取得し、重複してハンドラが追加されるのを防ぐ
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(TRACE_LEVEL_NUM) # ロガーのレベルをTRACEに設定

    # logディレクトリを作成 (存在しない場合)
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)

    # タイムスタンプ付きのファイル名を生成
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_filename = os.path.join(log_dir, f"log_{timestamp}_.txt")


    # ファイルハンドラの設定 (TRACEレベル以上をファイルに出力)
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(TRACE_LEVEL_NUM)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # コンソールハンドラの設定 (INFOレベル以上をコンソールに出力)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # ロガーにハンドラを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
