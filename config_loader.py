import json
import logging
import os
from dataclasses import dataclass

# 設定を保持するためのデータクラス
@dataclass
class Config:
    login_url: str
    video_url_base: str
    video_range_start: int
    video_range_end: int
    har_directory: str
    retry_count: int
    video_play_duration: int
    timeout_navigation: int
    timeout_visible: int
    timeout_click: int
    username: str
    password: str

def load_config() -> Config | None:
    """
    config.jsonとcredentials.jsonを読み込み、設定を格納したデータクラスを返す
    """
    logger = logging.getLogger(__name__)
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        with open('credentials.json', 'r', encoding='utf-8') as f:
            credentials_data = json.load(f)
        logger.info("設定ファイルを正常に読み込みました。")

        # harファイルの出力先ディレクトリを作成
        har_dir = config_data.get('output_har_directory', 'har')
        os.makedirs(har_dir, exist_ok=True)

        # タイムアウト設定のデフォルト値
        timeout_settings = config_data.get('timeout_ms', {})
        video_range = config_data.get('video_range', {})
        
        # Configオブジェクトを作成して返す
        return Config(
            login_url=config_data.get('login_url'),
            video_url_base=config_data.get('video_url_base'),
            video_range_start=video_range.get('start', 1),
            video_range_end=video_range.get('end', 1),
            har_directory=har_dir,
            retry_count=config_data.get('retry_count', 2),
            video_play_duration=config_data.get('wait_options', {}).get('video_play_duration_sec', 60),
            timeout_navigation=timeout_settings.get('navigation', 20000),
            timeout_visible=timeout_settings.get('element_visible', 15000),
            timeout_click=timeout_settings.get('element_click', 10000),
            username=credentials_data.get('username'),
            password=credentials_data.get('password')
        )

    except FileNotFoundError as e:
        logger.error(f"設定ファイルが見つかりません: {e.filename}")
        return None
    except json.JSONDecodeError:
        logger.error("設定ファイルの形式が正しくありません（JSONではありません）。")
        return None
    except Exception as e:
        logger.error(f"設定の読み込み中にエラーが発生しました: {e}")
        return None
