import json
import logging
import re

logger = logging.getLogger(__name__)

def extract_m3u8_url(har_path: str) -> str | None:
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
                return url
        
        logger.warning("指定されたパターンのURLは見つかりませんでした。")
        return None
    except FileNotFoundError:
        logger.error(f"HARファイルが見つかりません: {har_path}")
        return None
    except Exception as e:
        logger.error(f"HARファイルの処理中にエラーが発生しました: {e}", exc_info=True)
        return None