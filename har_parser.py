import json
import logging
import re
import os
from typing import Dict, List
import yaml

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
    抽出したすべてのURLをYAML形式でテキストファイルに保存する
    URLが見つからなかったIDにはERRORと表示する
    """
    logger.info(f"抽出したURLをYAMLファイルに保存します: {output_path}")
    
    # YAMLに出力するためのデータ構造を作成
    output_data = []
    for video_id in range(video_range_start, video_range_end + 1):
        urls = all_urls.get(video_id)
        if urls:
            output_data.append({'id': video_id, 'urls': urls})
        else:
            output_data.append({'id': video_id, 'status': 'ERROR'})
            
    try:
        # 出力先ディレクトリが存在しない場合に作成
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # YAML形式でファイルに書き出す
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
        logger.info("URLのYAMLファイルへの保存が完了しました。")
    except Exception as e:
        logger.error(f"URLのファイル保存中にエラーが発生しました: {e}", exc_info=True)
