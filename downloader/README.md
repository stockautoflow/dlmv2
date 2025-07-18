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
- ダウンロードされた動画は、`downloader`ディレクトリ内に、`SingAlong_Lyrics/01/`のような形式で保存されます。
- 実行ログは`downloader/log/`ディレクトリに保存されます。