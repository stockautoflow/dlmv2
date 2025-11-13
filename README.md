# 動画自動処理・ダウンロードツール

このプロジェクトは、特定のウェブサイトの動画コンテンツを自動的に処理するためのツール群です。以下の3つの主要な機能で構成されています。

1.  **パート1: URL抽出ツール (`app.py`)**: ウェブサイトに自動ログインし、指定された動画ページを巡回して、動画のメタデータとストリーミングURL (m3u8) を抽出し、YAMLファイルとして保存します。
2.  **パート2: ダウンロードツール (`downloader/`)**: パート1で作成されたYAMLファイルを読み込み、動画をダウンロードします。
3.  **パート3: 変換ツール (`converter/`)**: ダウンロードした動画を、再生互換性の高いMP4形式（H.264/AAC）に再エンコードします。

## 📖 アーキテクチャとワークフロー

本プロジェクトは、以下のステップで実行することを想定しています。

1.  **[URL抽出]**: `app.py` を実行し、動画のURLリスト (`urls_XXX.yaml`) を生成します。
2.  **[ダウンロード]**: `downloader/download_videos.py` を実行し、YAMLリストに基づいて動画ファイル（`.mp4` コンテナ）を `downloader/VIDEO/` フォルダにダウンロードします。
3.  **[変換 (オプション)]**: ダウンロードした動画が再生できない場合、`converter/converter.py` を実行し、互換性の高いMP4ファイルに再エンコードして `VIDEO_converted/` フォルダに保存します。

## 📁 主要なファイル構成

```
.
├── app.py                      # パート1: URL抽出ツールのエントリーポイント
├── src/                        # パート1: URL抽出ツールのソースコード
│   ├── config/
│   │   ├── config.json         # URL、処理範囲、タイムアウト等の設定
│   │   └── credentials.json    # ログイン認証情報 (要手動設定)
│   ├── core/                   # メインロジック (ブラウザ管理, タスク処理)
│   ├── actions/                # ブラウザ操作 (ログイン, 動画再生)
│   ├── parsers/                # データ抽出 (メタデータ, URL)
│   ├── reporters/              # YAMLファイル出力
│   └── utils/                  # 共通ユーティリティ (ロガー, 設定読み込み)
│
├── downloader/                 # パート2: ダウンロードツール
│   ├── download_videos.py      # 動画ダウンロードスクリプト
│   ├── path_formatter.py       # ダウンロード時のパスとファイル名を生成
│   ├── downloader.py           # yt-dlp を呼び出すラッパー
│   └── requirements.txt        # パート2 のPython依存ライブラリ
│
├── converter/                  # パート3: 変換ツール
│   └── converter.py            # (オプション) 動画変換スクリプト
│
├── requirements.txt            # パート1 のPython依存ライブラリ
└── README.md                   # このファイル
```

## 🛠 必要なツール

このプロジェクトを実行するには、以下のツールが必要です。

  * **Python 3.8** 以上
  * **Playwright**: ブラウザ自動操作ライブラリ (パート1)
  * **yt-dlp**: 動画ダウンロードライブラリ (パート2)
  * **ffmpeg**: 動画変換ライブラリ (パート3・変換オプション)

-----

## 🚀 セットアップ手順

### パート1: URL抽出ツールのセットアップ

1.  **Python依存ライブラリのインストール**:
    プロジェクトのルートディレクトリで `requirements.txt` をインストールします。

    ```bash
    pip install -r requirements.txt
    ```

2.  **Playwrightブラウザのインストール**:
    Playwrightが操作するためのブラウザ（Chromium）をインストールします。

    ```bash
    playwright install
    ```

3.  **認証情報の設定**:
    `src/config/credentials.json` ファイルを開き、ウェブサイトのログイン情報を入力します。

    ```json
    {
      "username": "あなたのメールアドレス",
      "password": "あなたのパスワード"
    }
    ```

### パート2: ダウンロードツールのセットアップ

1.  **Python依存ライブラリのインストール**:
    `downloader` ディレクトリに移動し、`requirements.txt` をインストールします。
    ```bash
    cd downloader
    pip install -r requirements.txt
    cd ..
    ```

### パート3: 変換ツールのセットアップ

1.  **ffmpeg のインストールとPATH設定**:
    (動画変換スクリプト `converter/converter.py` を使用する場合のみ必須)
    お使いのOSの手順に従い、`ffmpeg` をインストールし、システムPATHを通してください。

    **Ubuntu (aptでインストール / 推奨)**
    `apt` を使ってインストールするのが最も簡単で、PATHは自動で設定されます。

    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

    インストール後、`ffmpeg -version` と入力し、バージョン情報が表示されればセットアップ完了です。

    **Ubuntu (手動でPATHを通す場合)**
    `ffmpeg` を手動でダウンロードして `/usr/local/bin` 以外に置いた場合は、`~/.bashrc` にPATHを追記します。

    1.  `ffmpeg` が `~/bin` にあると仮定します。
    2.  `nano ~/.bashrc` で設定ファイルを開きます。
    3.  ファイルの最後に以下の行を追記します。
        ```bash
        export PATH="$HOME/bin:$PATH"
        ```
    4.  保存 (Ctrl+O) して閉じ (Ctrl+X)、`source ~/.bashrc` を実行して設定を再読み込みします。
    5.  `ffmpeg -version` でバージョン情報が表示されれば成功です。

-----

## ▶️ 実行方法 (ワークフロー)

### ステップ1: URLの抽出

1.  **(任意) 処理範囲の指定**:
    `src/config/config.json` を開き、`video_processing_rules` で処理したい動画のID範囲やバージョンを指定します。

2.  **抽出スクリプトの実行**:
    プロジェクトのルートディレクトリで `app.py` を実行します。

    ```bash
    python app.py
    ```

    処理が完了すると、`urls` ディレクトリ（自動生成）に `urls_YYYY-MM-DD-HHMMSS.yaml` という名前のファイルが生成されます。

### ステップ2: 動画のダウンロード

1.  **ダウンロードスクリプトの実行**:
    `downloader` ディレクトリに移動し、`download_videos.py` を実行します。引数として、ステップ1で生成されたYAMLファイルのパスを指定します。
    ```bash
    cd downloader

    # ../urls/ ディレクトリにある最新のYAMLファイルを指定します
    python download_videos.py ../urls/urls_YYYY-MM-DD-HHMMSS.yaml
    ```
    `yt-dlp` が起動し、`downloader/VIDEO/` ディレクトリ内に動画ファイルがダウンロードされます。

### ステップ3: 動画の変換 (オプション)

**🚨 注意: このステップは `ffmpeg` が必須です。**
この変換スクリプト (`converter/converter.py`) を実行するには、**`ffmpeg`** がお使いのシステムにインストールされ、PATHが通っている必要があります。
インストールとPATH設定の手順は、上記の「**パート3: 変換ツールのセットアップ**」セクションを参照してください。

-----

`yt-dlp` はHLSストリームをダウンロードする際、動画ストリームをMP4コンテナに\*\*再多重化（remux）\*\*します。これにより「拡張子は.mp4だが、中身はTSストリームのまま」というファイルが生成され、一部のプレイヤーで再生できないことがあります。

この問題を解決するため、`ffmpeg` を使用して互換性の高いMP4（H.264/AAC）に再エンコードします。

1.  **変換スクリプトの実行**:
    プロジェクトの**ルートディレクトリ**（`app.py` がある場所）に戻ってから、`converter/converter.py` を実行します。

      * **デフォルトの画質 (CRF=23) で変換**:

        ```bash
        # (downloader ディレクトリにいる場合は cd .. でルートに戻る)

        # downloader/VIDEO フォルダを対象に変換
        python converter/converter.py ./downloader/VIDEO
        ```

      * **画質を指定して変換 (高品質 CRF=20)**:
        `-q` または `--quality` オプションでCRF値（0～51、低いほど高品質）を指定します。

        ```bash
        python converter/converter.py ./downloader/VIDEO -q 20
        ```

      * **画質を指定して変換 (低画質・高速 CRF=30, 8スレッド)**:
        画質（-q 30）と並列実行数（-w 8）を指定するコマンド例です。

        ```bash
        python converter/converter.py ./downloader/VIDEO -w 8 -q 30
        ```

    変換されたファイルは、プロジェクトのルートディレクトリに `VIDEO_converted/` フォルダ（自動生成）として、元のディレクトリ構造を維持して保存されます。

## 📋 出力ディレクトリ

  * `urls/`: URL抽出結果のYAMLファイルが保存されます。
  * `log/`: `app.py` の実行ログが保存されます。
  * `downloader/VIDEO/`: ダウンロードされた元の動画ファイル（MP4コンテナ/TSストリーム）が保存されます。
  * `downloader/log/`: `download_videos.py` の実行ログが保存されます。
  * `converter/convert_log.txt`: `converter/converter.py` の変換ログが保存されます。
  * `VIDEO_converted/`: (オプション) `converter/converter.py` で変換された、再生互換性の高いMP4ファイルが保存されます。