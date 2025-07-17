import time
import logging
from playwright.sync_api import sync_playwright

from logger_setup import setup_logging
from config_loader import load_config
from login_actions import perform_login
from video_actions import play_video

def main():
    """
    全体の処理を管理するメイン関数
    """
    # --- ログと設定の初期化 ---
    setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config()
    if not config:
        return

    # --- ブラウザの起動と設定 ---
    browser = None
    context = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context(record_har_path=config.har_path)
            page = context.new_page()
            logger.info("ブラウザを起動し、ネットワークログの記録を開始しました。")

            # --- ログイン処理 ---
            perform_login(page, config)

            # --- 動画ページへの遷移と再生 ---
            play_video(page, config)

            logger.info(f"動画を{config.video_play_duration}秒間再生します。")
            time.sleep(config.video_play_duration)

            logger.info("動画の再生とログ記録を終了します。")

    except Exception as e:
        logger.error(f"処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
    finally:
        # --- 終了処理 ---
        if context:
            context.close()
            logger.info(f"ネットワークログを {config.har_path} に保存しました。")
        if browser:
            browser.close()
            logger.info("ブラウザを閉じて処理を終了しました。")

if __name__ == "__main__":
    main()
