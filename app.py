import logging
import sys
import os

# プロジェクトのルートをシステムパスに追加
# これにより、'src'パッケージ内のモジュールを正しくインポートできる
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.task_processor import TaskProcessor
from src.utils.logger_setup import setup_logging

def main():
    """
    アプリケーションを初期化し、タスクプロセッサを実行する
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("アプリケーションを開始します。")

    try:
        processor = TaskProcessor()
        processor.run()
    except Exception as e:
        logger.critical(f"予期せぬクリティカルなエラーで処理が中断されました: {e}", exc_info=True)
    finally:
        logger.info("アプリケーションを終了します。")

if __name__ == "__main__":
    main()