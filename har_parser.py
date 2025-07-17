import json
import logging
import re
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

def extract_m3u8_urls(har_path: str) -> List[str]:
    """
    HARファイルから "_9.m3u8" で終わるURLを抽出する
    """
    logger.info(f"HARファイルからURLを抽出します: {har_path}")
    extracted_urls = []
    url_pattern = re.compile(r"https://.*_9\.m3u8")

    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        if not entries:
            logger.warning(f"HARファイルにエントリが見つかりませんでした: {har_path}")
            return []

        for entry in entries:
            url = entry.get('request', {}).get('url', '')
            if url_pattern.match(url) and url not in extracted_urls:
                logger.debug(f"一致するURLを発見: {url}")
                extracted_urls.append(url)
        
        if not extracted_urls:
            logger.warning("指定されたパターンのURLは見つかりませんでした。")

        return extracted_urls

    except FileNotFoundError:
        logger.error(f"HARファイルが見つかりません: {har_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"HARファイルの形式が正しくありません: {har_path}")
        return []
    except Exception as e:
        logger.error(f"HARファイルの処理中にエラーが発生しました: {e}", exc_info=True)
        return []

def save_extracted_urls(
    all_urls: Dict[int, List[str]],
    output_path: str,
    video_range_start: int,
    video_range_end: int
):
    """
    抽出したすべてのURLをテキストファイルに保存する
    URLが見つからなかったIDにはERRORと表示する
    """
    logger.info(f"抽出したURLをファイルに保存します: {output_path}")
    try:
        # 出力先ディレクトリが存在しない場合に作成
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("--- 抽出されたURL一覧 ---\n\n")
            # configで指定された範囲のすべてのIDをループする
            for video_id in range(video_range_start, video_range_end + 1):
                f.write(f"▼ Video ID: {video_id}\n")
                # IDに対応するURLリストを取得。なければNone
                urls = all_urls.get(video_id)
                if urls:
                    # URLがあれば書き出す
                    for url in urls:
                        f.write(f"{url}\n")
                else:
                    # ★★★ 修正点: URLがなければERRORと書き出す ★★★
                    f.write("ERROR\n")
                f.write("\n")
        logger.info("URLのファイルへの保存が完了しました。")
    except Exception as e:
        logger.error(f"URLのファイル保存中にエラーが発生しました: {e}", exc_info=True)
