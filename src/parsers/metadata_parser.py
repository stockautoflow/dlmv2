import logging
from playwright.sync_api import Page
from src.utils.config_loader import VideoMetadata

logger = logging.getLogger(__name__)

def extract_metadata(page: Page) -> VideoMetadata | None:
    try:
        logger.debug("メタデータの抽出を開始します。")
        
        lesson = page.locator('p.pageHeader02_lesson').inner_text(timeout=5000)
        song_number = page.locator('p.pageHeader02_songNumber').inner_text(timeout=5000)
        title = page.locator('h1.pageHeader02_title').inner_text(timeout=5000)

        if not all([lesson, song_number, title]):
            logger.warning("一部のメタデータ要素が見つかりませんでした。")
            return None

        metadata = VideoMetadata(lesson=lesson, song_number=song_number, title=title)
        logger.info(f"メタデータを抽出しました: {metadata}")
        return metadata
    except Exception as e:
        logger.error(f"メタデータの抽出中にエラーが発生しました: {e}")
        return None