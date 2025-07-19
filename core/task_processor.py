import logging
import os
import time
from datetime import datetime
from core.browser_manager import BrowserManager
from utils.config_loader import load_config
from actions.video_actions import play_video
from parsers.metadata_parser import extract_metadata
from parsers.url_finder import UrlFinder
from reporters.yaml_reporter import save_results

logger = logging.getLogger(__name__)

class TaskProcessor:
    """
    設定に基づき、動画処理タスクの実行全体を管理するクラス
    """
    def __init__(self):
        self.config = load_config()
        self.browser_manager = BrowserManager(self.config) if self.config else None
        self.all_results = {}

    def run(self):
        """ タスク処理を実行する """
        if not self.browser_manager or not self.config:
            logger.error("設定の読み込みまたはブラウザマネージャーの初期化に失敗しました。")
            return

        try:
            self.browser_manager.start()
            self._process_rules()
        finally:
            self._save_final_report()
            self.browser_manager.stop()

    def _process_rules(self):
        """ 設定されたルールに基づいて動画を処理する """
        for rule in self.config.video_processing_rules:
            id_range = rule.get('id_range', {})
            start_id, end_id = id_range.get('start'), id_range.get('end')
            versions = rule.get('versions', [])

            if start_id is None or end_id is None: continue

            for video_id in range(start_id, end_id + 1):
                if video_id not in self.all_results:
                    self.all_results[video_id] = {"metadata": None, "versions": {}}
                for version in versions:
                    self._process_single_task_with_retry(video_id, version)

    def _process_single_task_with_retry(self, video_id: int, version: int | None):
        """ 1つの動画処理タスクをリトライロジック付きで実行する """
        for attempt in range(self.config.retry_count + 1):
            context = None
            try:
                logger.info(f"--- Video ID: {video_id} (Ver: {version or 'N/A'}) の処理を開始 (試行: {attempt + 1}/{self.config.retry_count + 1}) ---")
                
                # HAR記録オプションなしでコンテキストを作成
                context = self.browser_manager.browser.new_context(
                    storage_state=self.browser_manager.storage_state,
                    user_agent=self.browser_manager.user_agent
                )
                page = context.new_page()

                video_url = f"{self.config.video_url_base}{video_id}/"
                if version is not None:
                    video_url += f"?ver={version}"
                
                # ★★★ 修正点: 正規表現のバックスラッシュを修正 ★★★
                # URL監視を開始
                finder = UrlFinder(page, r"https://.*_9\.m3u8")

                # ページに移動
                page.goto(video_url, wait_until='domcontentloaded')
                
                # メタデータを抽出
                if self.all_results[video_id]["metadata"] is None:
                    metadata = extract_metadata(page)
                    if not metadata: raise ValueError("メタデータの抽出に失敗しました。")
                    self.all_results[video_id]["metadata"] = metadata

                # 動画再生をトリガー
                play_video(page, self.config)
                
                # URLが捕捉されるのを待つ (15秒)
                url = finder.wait_for_url(timeout=15000)
                
                if not url:
                    raise ValueError("指定されたパターンのURLが見つかりませんでした。")

                self.all_results[video_id]["versions"][version] = url
                logger.info(f"Video ID: {video_id} Ver:{version or 'N/A'} の処理に成功しました。")
                return # 成功したのでリトライを終了

            except Exception as e:
                logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} の処理中にエラー (試行 {attempt + 1}): {e}")
                if attempt < self.config.retry_count:
                    logger.info("リトライします...")
                    time.sleep(3)
                else:
                    logger.error(f"Video ID {video_id} Ver:{version or 'N/A'} のリトライ上限に達しました。")
            finally:
                if context:
                    context.close()
                    logger.info(f"Video ID {video_id} Ver:{version or 'N/A'} のコンテキストを閉じました。")

    def _save_final_report(self):
        """ 最終的な結果をファイルに保存する """
        if not self.config: return
        
        output_dir = "urls"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_filename = f"urls_{timestamp}.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        save_results(self.all_results, output_path, self.config.video_processing_rules)

        if not any(self.all_results.values()):
            logger.info("対象のURLは一件も見つかりませんでした。")
