import argparse
import logging
import os
import yaml
from typing import List, Dict, Any

from utils.logger_setup import setup_logging
from path_formatter import format_download_tasks
from downloader import download_video

def main(yaml_path: str):
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"YAMLファイルを読み込みます: {yaml_path}")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"指定されたYAMLファイルが見つかりません: {yaml_path}")
        return
    except Exception as e:
        logger.error(f"YAMLファイルの読み込み中にエラーが発生しました: {e}")
        return

    success_count = 0
    skip_count = 0
    fail_count = 0
    
    download_queue: List[Dict[str, Any]] = []
    for item in data:
        if item.get('status') == 'ERROR' and 'versions' not in item:
            logger.warning(f"ID {item.get('id')} はエラーのためスキップします。")
            skip_count += 1
            continue
        
        tasks = format_download_tasks(item)
        download_queue.extend(tasks)

    total_tasks = len(download_queue)
    logger.info(f"ダウンロード対象の動画は {total_tasks} 件です。")

    for i, task in enumerate(download_queue):
        dir_path = task["dir_path"]
        file_name = task["file_name"]
        download_url = task["download_url"]
        
        full_path = os.path.join(dir_path, file_name)
        
        logger.info(f"--- 処理中 ({i+1}/{total_tasks}) ---")
        logger.info(f"動画URL: {download_url}")
        logger.info(f"保存先: {full_path}")

        if os.path.exists(full_path):
            logger.warning("ファイルが既に存在するため、スキップします。")
            skip_count += 1
            continue

        os.makedirs(dir_path, exist_ok=True)
        
        if download_video(download_url, full_path):
            success_count += 1
        else:
            fail_count += 1
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except OSError as e:
                    logger.error(f"失敗したファイルの削除に失敗しました: {e}")

    logger.info("--- 全ての処理が完了しました ---")
    logger.info(f"成功: {success_count} 件")
    logger.info(f"失敗: {fail_count} 件")
    logger.info(f"スキップ (エラー/既存): {skip_count} 件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YAMLファイルから動画をダウンロードします。")
    parser.add_argument("yaml_file", help="入力するurls_XXX.yamlファイルのパス")
    args = parser.parse_args()
    
    main(args.yaml_file)