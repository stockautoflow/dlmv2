import logging
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

from logger_setup import setup_logging
from config_loader import load_config
from login_actions import perform_login
from video_actions import play_video
from metadata_parser import extract_metadata
from har_parser import extract_m3u8_url, save_extracted_urls

def main():
    """
    全体の処理を管理するメイン関数
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config()
    if not config:
        return

    all_results = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        
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
        
        for rule in config.video_processing_rules:
            id_range = rule.get('id_range', {})
            start_id, end_id = id_range.get('start'), id_range.get('end')
            versions = rule.get('versions', [])

            if start_id is None or end_id is None: continue

            for video_id in range(start_id, end_id + 1):
                if video_id not in all_results:
                    all_results[video_id] = {"metadata": None, "versions": {}}

                for version in versions:
                    for attempt in range(config.retry_count + 1):
                        context = None
                        ver_str = f"ver_{version}" if version is not None else "ver_none"
                        har_path = os.path.join(config.har_directory, f"video_{video_id}_{ver_str}.har")
                        
                        try:
                            logger.info(f"--- Video ID: {video_id} (Ver: {version or 'N/A'}) の処理を開始 (試行: {attempt + 1}/{config.retry_count + 1}) ---")
                            
                            context = browser.new_context(storage_state=storage_state, record_har_path=har_path, user_agent=user_agent)
                            loop_page = context.new_page()

                            video_url = f"{config.video_url_base}{video_id}/"
                            if version is not None:
                                video_url += f"?ver={version}"
                            
                            # ページにアクセスし、メタデータを抽出（IDごとに初回のみ）
                            loop_page.goto(video_url, wait_until='domcontentloaded')
                            if all_results[video_id]["metadata"] is None:
                                metadata = extract_metadata(loop_page)
                                if not metadata:
                                    raise ValueError("メタデータの抽出に失敗しました。")
                                all_results[video_id]["metadata"] = metadata

                            play_video(loop_page, video_url, config)
                            
                            context.close()
                            context = None
                            logger.info(f"Video ID {video_id} Ver:{version or 'N/A'} (試行 {attempt + 1}) のコンテキストを閉じ、HARを保存しました: {har_path}")

                            url = extract_m3u8_url(har_path)
                            if not url:
                                raise ValueError("指定されたパターンのURLが見つかりませんでした。")

                            all_results[video_id]["versions"][version] = url
                            logger.info(f"Video ID: {video_id} Ver:{version or 'N/A'} の処理に成功しました。")
                            break

                        except Exception as e:
                            logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} の処理中にエラー (試行 {attempt + 1}): {e}")
                            if attempt < config.retry_count:
                                logger.info("リトライします...")
                                time.sleep(3)
                            else:
                                logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} のリトライ上限に達しました。")
                        finally:
                            if context:
                                context.close()

        output_dir = "urls"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_filename = f"urls_{timestamp}.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        save_extracted_urls(all_results, output_path, config.video_processing_rules)

        browser.close()
        logger.info("全ての処理が完了しました。ブラウザを閉じます。")

if __name__ == "__main__":
    main()