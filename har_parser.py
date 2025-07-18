import json
import logging
import re
import os
from typing import Dict, List, Any
import yaml

logger = logging.getLogger(__name__)

def extract_m3u8_url(har_path: str) -> str | None:
    """
    HARファイルから "_9.m3u8" で終わるURLを抽出し、最初の1件を返す
    """
    logger.info(f"HARファイルからURLを抽出します: {har_path}")
    url_pattern = re.compile(r"https://.*_9\.m3u8")

    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        if not entries:
            logger.warning(f"HARファイルにエントリが見つかりませんでした: {har_path}")
            return None

        for entry in entries:
            url = entry.get('request', {}).get('url', '')
            if url_pattern.match(url):
                logger.debug(f"一致するURLを発見: {url}")
                return url # 最初の1件が見つかったらすぐに返す
        
        logger.warning("指定されたパターンのURLは見つかりませんでした。")
        return None

    except FileNotFoundError:
        logger.error(f"HARファイルが見つかりません: {har_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"HARファイルの形式が正しくありません: {har_path}")
        return None
    except Exception as e:
        logger.error(f"HARファイルの処理中にエラーが発生しました: {e}", exc_info=True)
        return None

def save_extracted_urls(
    all_urls: Dict[int, Dict[Any, str]],
    output_path: str,
    rules: List[Dict[str, Any]]
):
    """
    抽出したすべてのURLを設計書通りのYAML形式で保存する
    """
    logger.info(f"抽出したURLをYAMLファイルに保存します: {output_path}")
    
    output_data = []
    
    processed_ids = set()

    for rule in rules:
        id_range = rule.get('id_range', {})
        start_id = id_range.get('start')
        end_id = id_range.get('end')
        versions = rule.get('versions', [])

        if start_id is None or end_id is None:
            continue

        for video_id in range(start_id, end_id + 1):
            if video_id in processed_ids:
                continue
            processed_ids.add(video_id)

            video_results = all_urls.get(video_id, {})
            
            # バージョン指定がないルールの場合 (versions: [null])
            if versions == [None]:
                url = video_results.get(None)
                if url:
                    output_data.append({'id': video_id, 'url': url})
                else:
                    output_data.append({'id': video_id, 'status': 'ERROR'})
            # バージョン指定があるルールの場合
            else:
                version_list = []
                for ver in versions:
                    url = video_results.get(ver)
                    if url:
                        version_list.append({'ver': ver, 'url': url})
                    else:
                        version_list.append({'ver': ver, 'status': 'ERROR'})
                output_data.append({'id': video_id, 'versions': version_list})

    try:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
        logger.info("URLのYAMLファイルへの保存が完了しました。")
    except Exception as e:
        logger.error(f"URLのファイル保存中にエラーが発生しました: {e}", exc_info=True)
