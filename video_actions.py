import logging
from playwright.sync_api import Page
from config_loader import Config
from countdown_timer import start_countdown

logger = logging.getLogger(__name__)

def play_video(page: Page, video_url: str, config: Config):
    """
    指定された動画URLに遷移し、再生を開始し、待機する
    """
    # この関数はメタデータ取得のためにページアクセスを行わない
    # page.goto(video_url, wait_until='domcontentloaded')

    logger.info("キーボード操作による動画の再生を開始します。")
    
    try:
        # ページのフォーカスの猶予として2秒待機
        logger.debug("ページのフォーカスを待機します...")
        page.wait_for_timeout(2000)

        page.locator('body').click(force=True)
        logger.debug("ページにフォーカスを合わせました。")

        for i in range(4):
            page.keyboard.press('Tab')
            logger.debug(f"TABキーを押しました ({i+1}/4回)")
            page.wait_for_timeout(200)

        page.keyboard.press('Space')
        logger.info("スペースキーで動画の再生を実行しました。")

        logger.debug("再生開始を待機します...")
        page.wait_for_timeout(2000)

    except Exception as e:
        logger.error(f"キーボード操作による動画再生に失敗しました: {e}")
        raise 

    start_countdown(config.video_play_duration)
    
    logger.info("動画の再生待機を終了します。")