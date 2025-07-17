import logging
from playwright.sync_api import Page
from config_loader import Config
from countdown_timer import start_countdown

logger = logging.getLogger(__name__)

def play_video(page: Page, video_url: str, config: Config):
    """
    指定された動画URLに遷移し、再生を開始し、待機する
    """
    logger.info(f"動画ページにアクセスします: {video_url}")
    page.goto(video_url, wait_until='domcontentloaded')

    logger.info("キーボード操作による動画の再生を開始します。")
    
    try:
        # ページのフォーカスの猶予として2秒待機
        logger.debug("ページのフォーカスを待機します...")
        page.wait_for_timeout(2000)

        # 1. ページのフォーカスを確実にするため、body要素をクリック
        page.locator('body').click(force=True)
        logger.debug("ページにフォーカスを合わせました。")

        # 2. TABキーを4回押す
        for i in range(4):
            page.keyboard.press('Tab')
            logger.debug(f"TABキーを押しました ({i+1}/4回)")
            page.wait_for_timeout(200) # キー入力の間にわずかな待機を入れる

        # 3. スペースキーを1回押して再生
        page.keyboard.press('Space')
        logger.info("スペースキーで動画の再生を実行しました。")

        # 再生開始の猶予として2秒待機
        logger.debug("再生開始を待機します...")
        page.wait_for_timeout(2000)

    except Exception as e:
        logger.error(f"キーボード操作による動画再生に失敗しました: {e}")
        raise # エラーを呼び出し元に伝播させてループを継続させる

    # 汎用化したカウントダウン関数を呼び出す
    start_countdown(config.video_play_duration)
    
    logger.info("動画の再生待機を終了します。")
