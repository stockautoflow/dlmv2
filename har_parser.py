import json
import logging
import re

logger = logging.getLogger(__name__)

def extract_m3u8_urls(har_path: str) -> list[str]:
    """
    HARファイルから "_9.m3u8" で終わるURLを抽出する

    Args:
        har_path (str): HARファイルのパス

    Returns:
        list[str]: 抽出されたURLのリスト
    """
    logger.info(f"HARファイルからURLを抽出します: {har_path}")
    extracted_urls = []
    
    # URLの正規表現パターン: httpsで始まり、任意の文字列が続き、_9.m3u8で終わる
    url_pattern = re.compile(r"https://.*_9\.m3u8")

    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        if not entries:
            logger.warning("HARファイルにエントリが見つかりませんでした。")
            return []

        for entry in entries:
            url = entry.get('request', {}).get('url', '')
            if url_pattern.match(url):
                logger.debug(f"一致するURLを発見: {url}")
                extracted_urls.append(url)
        
        if extracted_urls:
            logger.info(f"{len(extracted_urls)}件のURLを抽出しました。")
        else:
            logger.warning("指定されたパターンのURLは見つかりませんでした。")

        return extracted_urls

    except FileNotFoundError:
        logger.error(f"HARファイルが見つかりません: {har_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"HARファイルの形式が正しくありません（JSONではありません）: {har_path}")
        return []
    except Exception as e:
        logger.error(f"HARファイルの処理中にエラーが発生しました: {e}", exc_info=True)
        return []