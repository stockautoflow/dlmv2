import logging
import re
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

VERSION_SUFFIX_MAP = {
    1: "_Lyrics",
    2: "_Vocabulary",
    3: "_Karaoke",
}

SONG_NUMBER_DIR_MAP = {
    "1": "01",
    "2": "02",
    "3": "03",
    "4": "04",
}

def _sanitize_filename(name: str) -> str:
    """ファイル名として使用できない文字を除去する"""
    return re.sub(r'[\\/*?:"<>|]', '', name)

def format_download_tasks(item: Dict[str, Any]) -> list:
    """
    YAMLの1エントリから、ダウンロードに必要なタスク情報のリストを生成する
    """
    download_tasks = []
    
    video_id = item.get('id')
    lesson = item.get('lesson')
    song_number = item.get('song_number')
    title = item.get('title')

    if not all([video_id, lesson, song_number, title]):
        logger.warning(f"ID {video_id} のメタデータが不足しているためスキップします。")
        return []

    # バージョンがある場合
    if 'versions' in item:
        for version_info in item['versions']:
            if version_info.get('status') == 'ERROR':
                continue
            
            ver = version_info.get('ver')
            download_url = version_info.get('url')
            if not download_url:
                continue

            lesson_dir = _sanitize_filename(lesson)
            version_suffix = VERSION_SUFFIX_MAP.get(ver, "")
            root_dir = f"{lesson_dir}{version_suffix}"
            
            song_num_prefix = song_number.split('-')[0]
            number_dir = SONG_NUMBER_DIR_MAP.get(song_num_prefix, song_num_prefix)
            
            dir_path = os.path.join("VIDEO", root_dir, number_dir)

            song_num_suffix = song_number.split('-')[1]
            numeric_suffix_match = re.search(r'\d+', song_num_suffix)
            if not numeric_suffix_match: continue
            numeric_suffix = int(numeric_suffix_match.group())
            
            file_prefix = f"{song_num_prefix}-{numeric_suffix:02d}_"
            sanitized_title = _sanitize_filename(title)
            file_name = f"{file_prefix}{sanitized_title}.mp4"

            download_tasks.append({
                "dir_path": dir_path,
                "file_name": file_name,
                "download_url": download_url,
            })
    # バージョンがない場合
    elif 'url' in item and item.get('status') != 'ERROR':
        download_url = item.get('url')
        if not download_url:
            return []
            
        lesson_dir = _sanitize_filename(lesson)
        song_num_prefix = song_number.split('-')[0]
        number_dir = SONG_NUMBER_DIR_MAP.get(song_num_prefix, song_num_prefix)
        dir_path = os.path.join("VIDEO", lesson_dir, number_dir)

        song_num_suffix = song_number.split('-')[1]
        numeric_suffix_match = re.search(r'\d+', song_num_suffix)
        if not numeric_suffix_match: return []
        numeric_suffix = int(numeric_suffix_match.group())

        file_prefix = f"{song_num_prefix}-{numeric_suffix:02d}_"
        sanitized_title = _sanitize_filename(title)
        file_name = f"{file_prefix}{sanitized_title}.mp4"

        download_tasks.append({
            "dir_path": dir_path,
            "file_name": file_name,
            "download_url": download_url,
        })

    return download_tasks