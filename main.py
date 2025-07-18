import logging
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from logger_setup import setup_logging
from config_loader import load_config
from login_actions import perform_login
from video_actions import play_video
from har_parser import extract_m3u8_urls, save_extracted_urls

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

    all_extracted_urls = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        
        # --- ログイン処理と認証情報の保存 ---
        logger.info("--- ログイン処理と認証情報保存を開始 ---")
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
        temp_context = browser.new_context(user_agent=user_agent)
        temp_page = temp_context.new_page()
        perform_login(temp_page, config)
        
        storage_state = temp_context.storage_state()
        logger.info("認証情報を取得しました。")
        temp_context.close()
        
        # --- 動画のループ処理 ---
        for video_id in range(config.video_range_start, config.video_range_end + 1):
            
            # リトライ処理
            for attempt in range(config.retry_count + 1): # 初回実行 + リトライ回数
                context = None
                har_path = os.path.join(config.har_directory, f"video_{video_id}.har")
                
                try:
                    logger.info(f"--- Video ID: {video_id} の処理を開始 (試行: {attempt + 1}/{config.retry_count + 1}) ---")
                    
                    context = browser.new_context(
                        storage_state=storage_state,
                        record_har_path=har_path,
                        user_agent=user_agent
                    )
                    loop_page = context.new_page()

                    video_url = f"{config.video_url_base}{video_id}/"
                    play_video(loop_page, video_url, config)
                    
                    # コンテキストを閉じてHARファイルへの書き込みを完了させる
                    context.close()
                    context = None # 二重クローズを防止
                    logger.info(f"Video ID {video_id} (試行 {attempt + 1}) のコンテキストを閉じ、HARファイルを保存しました: {har_path}")

                    # HAR解析とURLの有無チェックをtryブロック内に移動
                    urls = extract_m3u8_urls(har_path)
                    if not urls:
                        # URLが見つからない場合はエラーを発生させてリトライさせる
                        raise ValueError("指定されたパターンのURLが見つかりませんでした。")

                    # 成功した場合、結果を保存してリトライを終了
                    all_extracted_urls[video_id] = urls
                    logger.info(f"Video ID: {video_id} の処理に成功しました。")
                    break

                except Exception as e:
                    # ログにはエラーの詳細を残すが、スタックトレースは冗長なので省略
                    logger.error(f"Video ID {video_id} の処理中にエラー (試行 {attempt + 1}): {e}")
                    if attempt < config.retry_count:
                        logger.info("リトライします...")
                        time.sleep(3) # リトライ前に3秒待機
                    else:
                        logger.error(f"Video ID {video_id} のリトライ上限に達しました。")
                finally:
                    # tryブロックでエラーが発生した場合に備え、コンテキストを確実に閉じる
                    if context:
                        context.close()

        # --- 終了処理 ---
        output_dir = "urls"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_filename = f"urls_{timestamp}.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        save_extracted_urls(
            all_extracted_urls,
            output_path,
            config.video_range_start,
            config.video_range_end
        )

        if not all_extracted_urls:
            logger.info("対象のURLは一件も見つかりませんでした。")

        browser.close()
        logger.info("全ての処理が完了しました。ブラウザを閉じます。")


if __name__ == "__main__":
    main()
