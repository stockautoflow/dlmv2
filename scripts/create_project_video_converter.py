import os

# ==============================================================================
# Converterプロジェクトのファイル構造と内容を定義
# ==============================================================================
project_files = {
    "converter/converter.py": """import os
import subprocess
import argparse
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# ロギング設定 (コンソールと convert_log.txt に出力)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('convert_log.txt', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def is_ffmpeg_installed():
    \"\"\"ffmpegが利用可能か確認する\"\"\"
    return shutil.which("ffmpeg") is not None

def convert_file(input_file, output_file, quality):
    \"\"\"
    ffmpegを使用して単一のファイルを変換する
    -c:v libx264 (H.264コーデック) と -c:a aac (AACコーデック) を使用。
    -crf で指定された画質 (quality) でエンコードする。
    \"\"\"
    # 出力ファイルが既に存在し、サイズが0より大きい場合はスキップ
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        logger.warning(f"ファイルが既に存在するためスキップ: {output_file}")
        return input_file, "skipped"

    command = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "libx264",      # 映像コーデックをH.264に
        "-crf", str(quality),   # ★★★ 画質 (CRF値) を指定 ★★★
        "-c:a", "aac",          # 音声コーデックをAACに
        "-loglevel", "error",   # エラー以外はログを抑制
        output_file
    ]

    try:
        # ffmpegコマンドを実行
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logger.info(f"変換成功: {output_file} (Quality={quality})")
        return input_file, "success"
    except subprocess.CalledProcessError as e:
        logger.error(f"変換失敗: {input_file}")
        logger.error(f"ffmpegエラー: {e.stderr.strip()}")
        # 失敗した場合、不完全な出力ファイルを削除する
        if os.path.exists(output_file):
            os.remove(output_file)
        return input_file, "fail"
    except Exception as e:
        logger.error(f"予期せぬエラー ({input_file}): {e}", exc_info=True)
        return input_file, "fail"

def main(input_dir, output_dir, max_workers, quality):
    if not is_ffmpeg_installed():
        logger.critical("ffmpegが見つかりません。インストールしてPATHを通してください。")
        return

    logger.info(f"変換処理を開始します。")
    logger.info(f"入力ディレクトリ: {input_dir}")
    logger.info(f"出力ディレクトリ: {output_dir}")
    logger.info(f"同時実行数: {max_workers}")
    logger.info(f"画質設定 (CRF): {quality} (値が低いほど高品質)")

    tasks = []
    # 入力ディレクトリを再帰的にスキャン
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.mp4'):
                # 入力ファイルのフルパス
                input_file = os.path.join(root, file)
                
                # 入力ディレクトリ基準の相対パスを取得
                relative_path = os.path.relpath(root, input_dir)
                
                # 出力側のサブディレクトリパスを構築
                output_sub_dir = os.path.join(output_dir, relative_path)
                
                # 出力ディレクトリを作成
                os.makedirs(output_sub_dir, exist_ok=True)
                
                # 出力ファイルのフルパス
                output_file = os.path.join(output_sub_dir, file)
                
                tasks.append((input_file, output_file))

    if not tasks:
        logger.warning(f"変換対象の.mp4ファイルが見つかりませんでした。({input_dir})")
        return

    logger.info(f"{len(tasks)} 件のファイルが変換対象です。")

    success_count = 0
    fail_count = 0
    skip_count = 0

    # ThreadPoolExecutorを使用して変換処理を並列実行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # タスクを投入 (quality も渡す)
        futures = {executor.submit(convert_file, task[0], task[1], quality): task for task in tasks}
        
        # 完了したものから結果を処理
        for i, future in enumerate(as_completed(futures)):
            input_file, status = future.result()
            logger.info(f"--- 進捗 ({i + 1}/{len(tasks)}) ---")
            
            if status == "success":
                success_count += 1
            elif status == "fail":
                fail_count += 1
            elif status == "skipped":
                skip_count += 1

    logger.info("--- 全ての処理が完了しました ---")
    logger.info(f"成功: {success_count} 件")
    logger.info(f"失敗: {fail_count} 件")
    logger.info(f"スキップ (既存): {skip_count} 件")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ダウンロードされたMP4 (TS) ファイルを互換性の高いMP4 (H.264/AAC) に変換します。")
    parser.add_argument(
        "input_dir", 
        nargs="?",
        default="VIDEO", 
        help="入力ディレクトリ (デフォルト: VIDEO)"
    )
    parser.add_argument(
        "-o", "--output_dir", 
        default="VIDEO_converted", 
        help="出力ディレクトリ (デフォルト: VIDEO_converted)"
    )
    parser.add_argument(
        "-w", "--workers", 
        type=int, 
        default=max(1, os.cpu_count() // 2), # CPUコア数の半分をデフォルトに
        help="同時変換スレッド数 (デフォルト: CPUコア数の半分)"
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=23,  # ★★★ 画質のデフォルト値を 23 に設定 ★★★
        help="H.264のCRF値 (0-51)。値が低いほど高品質。デフォルト: 23"
    )
    
    args = parser.parse_args()
    
    # スクリプトが置かれているディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 'VIDEO' や 'VIDEO_converted' が指定された場合、
    # スクリプト(downloader)の親ディレクトリにあると想定してパスを解決
    if args.input_dir == "VIDEO":
        input_dir = os.path.join(script_dir, "..", "VIDEO")
    else:
        input_dir = args.input_dir

    if args.output_dir == "VIDEO_converted":
        output_dir = os.path.join(script_dir, "..", "VIDEO_converted")
    else:
        output_dir = args.output_dir
        
    # 最終的なパスを絶対パスに変換
    input_dir_abs = os.path.abspath(input_dir)
    output_dir_abs = os.path.abspath(output_dir)

    main(input_dir_abs, output_dir_abs, args.workers, args.quality)"""
}


# ==============================================================================
# プロジェクト生成のメインロジック
# ==============================================================================
def create_project():
    """
    project_filesディクショナリに基づいてプロジェクトのディレクトリとファイルを生成する
    """
    print("動画Converterプロジェクトの生成を開始します...")

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
