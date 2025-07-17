import logging
from playwright.sync_api import sync_playwright

from logger_setup import setup_logging
from config_loader import load_config
from login_actions import perform_login
from video_actions import play_video
from har_parser import extract_m3u8_urls

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
    with sync_playwright() as playwright:
        browser = None
        context = None
        try:
            # PCにインストール済みのChromeを起動する
            browser = playwright.chromium.launch(channel="chrome", headless=False)
            
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
            
            context = browser.new_context(
                record_har_path=config.har_path,
                user_agent=user_agent
            )
            
            page = context.new_page()
            logger.info("ブラウザを起動し、ネットワークログの記録を開始しました。")

            # --- ログイン処理 ---
            perform_login(page, config)

            # --- 動画ページへの遷移と再生 ---
            play_video(page, config)

        except Exception as e:
            logger.error(f"処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
        finally:
            # --- 終了処理 ---
            if context:
                context.close()
                logger.info(f"ネットワークログを {config.har_path} に保存しました。")
                
                # HARファイルからURLを抽出し、表示する
                urls = extract_m3u8_urls(config.har_path)
                if urls:
                    print("\n--- 抽出されたURL ---")
                    for url in urls:
                        print(url)
                    print("---------------------\n")

            if browser:
                browser.close()
                logger.info("ブラウザを閉じて処理を終了しました。")

if __name__ == "__main__":
    main()