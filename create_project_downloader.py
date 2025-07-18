import os

# ==============================================================================
# ダウンローダープロジェクトのファイル構造と内容を定義
# ==============================================================================
project_files = {
    # --- メインスクリプト ---
    "downloader/download_videos.py": """
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
""",

    # --- ダウンローダーモジュール ---
    "downloader/downloader.py": """
import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)

def is_ytdlp_installed():
    \"\"\"yt-dlpが利用可能か確認する\"\"\"
    return shutil.which("yt-dlp") is not None

def download_video(download_url: str, full_output_path: str) -> bool:
    \"\"\"
    yt-dlpを使用して動画をダウンロードする
    \"\"\"
    if not is_ytdlp_installed():
        logger.critical("yt-dlpが見つかりません。実行ファイルをダウンロードし、PATHを通してください。")
        return False

    logger.info(f"ダウンロードを開始します: {download_url}")
    
    command = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--allow-unplayable-formats",
        "-o", full_output_path,
        download_url
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logger.info(f"ダウンロード成功: {full_output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ダウンロード失敗: {full_output_path}")
        logger.error(f"yt-dlpエラー: {e.stderr.strip()}")
        return False
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        return False
""",

    # --- パス・ファイル名生成モジュール ---
    "downloader/path_formatter.py": """
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
    \"\"\"ファイル名として使用できない文字を除去する\"\"\"
    return re.sub(r'[\\\\/*?:"<>|]', '', name)

def format_download_tasks(item: Dict[str, Any]) -> list:
    \"\"\"
    YAMLの1エントリから、ダウンロードに必要なタスク情報のリストを生成する
    \"\"\"
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
            numeric_suffix_match = re.search(r'\\d+', song_num_suffix)
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
        numeric_suffix_match = re.search(r'\\d+', song_num_suffix)
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
""",

    # --- ユーティリティ ---
    "downloader/utils/logger_setup.py": """
import logging
import os
from datetime import datetime

def setup_logging():
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.INFO)

    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_filename = os.path.join(log_dir, f"download_log_{timestamp}.txt")

    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
""",

    # --- 依存ライブラリ ---
    "downloader/requirements.txt": """
pyyaml
yt-dlp
""",

    # --- 説明書 ---
    "downloader/README.md": """
# 動画ダウンロードスクリプト

## 概要
このスクリプトは、`urls_XXX.yaml`ファイルを入力として、動画をダウンロードし、指定された命名規則で保存します。

## 前提条件
- Python 3.8以上
- `yt-dlp`がインストールされ、PATHが通っていること。

## セットアップ
1. ターミナルで`downloader`ディレクトリに移動します。
   ```bash
   cd downloader
   ```
2. 必要なライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```

## 実行方法
1. `downloader`ディレクトリの親ディレクトリに、処理対象の`urls_XXX.yaml`ファイル（例: `urls/urls_YYYY-MM-DD-HHMMSS.yaml`）があることを確認します。
2. ターミナルで`downloader`ディレクトリに移動し、以下のコマンドを実行します。
   ```bash
   python download_videos.py ../urls/urls_YYYY-MM-DD-HHMMSS.yaml
   ```
   ※ `../urls/urls_YYYY-MM-DD-HHMMSS.yaml` の部分は、実際のファイルパスに置き換えてください。

## 出力
- ダウンロードされた動画は、`downloader/VIDEO/`ディレクトリ内に、`SingAlong_Lyrics/01/`のような形式で保存されます。
- 実行ログは`downloader/log/`ディレクトリに保存されます。
"""
}

# ==============================================================================
# プロジェクト生成のメインロジック
# ==============================================================================
def create_project():
    """
    project_filesディクショナリに基づいてプロジェクトのディレクトリとファイルを生成する
    """
    print("動画ダウンローダープロジェクトの生成を開始します...")

    for file_path, content in project_files.items():
        # ディレクトリパスを取得
        dir_name = os.path.dirname(file_path)

        # ディレクトリが存在しない場合は作成
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"  - ディレクトリを作成しました: {dir_name}/")

        # ファイルを作成して内容を書き込む
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # contentの先頭の不要な改行やインデントを削除
                f.write(content.strip())
            print(f"  - ファイルを作成しました: {file_path}")
        except IOError as e:
            print(f"  - エラー: {file_path} の作成に失敗しました。 {e}")

    print("\\nプロジェクトの生成が完了しました。")
    print("次に、以下の手順でダウンロードを開始してください:")
    print("1. cd downloader")
    print("2. pip install -r requirements.txt")
    print("3. python download_videos.py ../urls/your_yaml_file.yaml")
    print("   (your_yaml_file.yaml は実際のファイル名に置き換えてください)")

if __name__ == "__main__":
    create_project()
