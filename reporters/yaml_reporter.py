import logging
import os
import yaml
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def save_results(
    all_results: Dict[int, Dict[str, Any]],
    output_path: str,
    rules: List[Dict[str, Any]]
):
    logger.info(f"抽出した結果をYAMLファイルに保存します: {output_path}")
    
    output_data = []
    processed_ids = set()

    for rule in rules:
        id_range = rule.get('id_range', {})
        start_id, end_id = id_range.get('start'), id_range.get('end')
        versions = rule.get('versions', [])

        if start_id is None or end_id is None: continue

        for video_id in range(start_id, end_id + 1):
            if video_id in processed_ids: continue
            processed_ids.add(video_id)

            result = all_results.get(video_id)
            if not result or not result.get("metadata"):
                output_data.append({'id': video_id, 'status': 'ERROR'})
                continue

            metadata = result["metadata"]
            base_info = {
                'id': video_id,
                'lesson': metadata.lesson,
                'song_number': metadata.song_number,
                'title': metadata.title
            }
            
            version_urls = result.get("versions", {})
            
            if versions == [None]:
                url = version_urls.get(None)
                if url: base_info['url'] = url
                else: base_info['status'] = 'ERROR'
                output_data.append(base_info)
            else:
                version_list = []
                for ver in versions:
                    url = version_urls.get(ver)
                    if url: version_list.append({'ver': ver, 'url': url})
                    else: version_list.append({'ver': ver, 'status': 'ERROR'})
                base_info['versions'] = version_list
                output_data.append(base_info)

    try:
        output_dir = os.path.dirname(output_path)
        if output_dir: os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
        logger.info("YAMLファイルへの保存が完了しました。")
    except Exception as e:
        logger.error(f"URLのファイル保存中にエラーが発生しました: {e}", exc_info=True)