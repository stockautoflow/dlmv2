import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)

def is_ytdlp_installed():
    """yt-dlpが利用可能か確認する"""
    return shutil.which("yt-dlp") is not None

def download_video(download_url: str, full_output_path: str) -> bool:
    """
    yt-dlpを使用して動画をダウンロードする
    """
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