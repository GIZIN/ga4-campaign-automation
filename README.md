# GA4 紙広告効果測定自動化システム

紙の広告（チラシ、ポスター等）にQRコードを掲載し、その効果測定をGoogle Analytics 4で自動的に行うシステムです。

## 特徴

- 📱 UTMパラメータ付きQRコードの自動生成
- 🎯 日本語でわかりやすいキャンペーン管理
- 📊 GA4のカスタムディメンション自動設定
- 🎯 カスタマイズ可能なコンバージョンイベント
- 🔧 拡張計測機能の自動有効化
- 📅 データ保持期間の自動設定（14ヶ月）
- 📈 日次・期間レポートの自動生成
- 💰 CPA（獲得単価）の自動計算
- 🏷️ GTM連携用の設定ヘルパー生成

## 必要な環境

- Python 3.9以上
- Google Cloud Platform アカウント
- Google Analytics 4 プロパティ

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Platform の設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新規プロジェクトを作成（または既存のプロジェクトを選択）
3. 以下のAPIを有効化：
   - Google Analytics Admin API
   - Google Analytics Data API
4. サービスアカウントを作成：
   - IAMと管理 → サービスアカウント → 作成
   - 認証キー（JSON）をダウンロード
   - `config/credentials.json`として保存

### 3. Google Analytics 4 の設定

1. GA4プロパティでサービスアカウントに権限を付与：
   - 管理 → プロパティのアクセス管理
   - サービスアカウントのメールアドレスを追加（編集者権限）
2. プロパティIDを確認：
   - 管理 → プロパティ設定
   - プロパティIDをコピー

### 4. 設定ファイルの準備

`config/ga4_config.json`を編集：
```json
{
  "property_id": "123456789",
  "measurement_id": "G-XXXXXXXXXX"
}
```

### 5. キャンペーン設定

`campaigns.yml`でキャンペーンとコンバージョンイベントを定義：

```yaml
# キャンペーン設定
campaigns:
  - name: "2025年7月SCSチラシiOS"
    location: "仙台"
    start_date: "2025-07-26"
    end_date: "2025-07-27"
    budget: 22000
    target_url: "https://apps.apple.com/jp/app/id1550542928"

# カスタムコンバージョンイベント（オプション）
conversion_events:
  - event_name: "app_store_click"
    description: "App Storeへのクリック"
  - event_name: "qr_code_scan"
    description: "QRコードからの訪問"
```

#### 様々な用途に対応可能

**アプリダウンロード促進の場合：**
```yaml
conversion_events:
  - event_name: "app_store_click"
    description: "App Storeへのクリック"
  - event_name: "google_play_click"
    description: "Google Playへのクリック"
```

**ECサイトの場合：**
```yaml
conversion_events:
  - event_name: "add_to_cart"
    description: "カートに追加"
  - event_name: "purchase"
    description: "購入完了"
```

**資料請求・問い合わせの場合：**
```yaml
conversion_events:
  - event_name: "form_submit"
    description: "資料請求フォーム送信"
  - event_name: "download_brochure"
    description: "パンフレットダウンロード"
```

## 使い方

### 初期設定の確認
```bash
python src/main.py setup
```

### QRコードの生成
```bash
python src/main.py generate-qr
```
生成されたQRコードは`output/qr_codes/`に保存されます。

### GA4の自動設定
```bash
python src/main.py configure-ga4
```

以下が自動的に設定されます：
- ✅ カスタムディメンション（UTMパラメータ、キャンペーン情報）
- ✅ コンバージョンイベント（campaigns.ymlで定義したもの）
- ✅ 拡張計測機能の有効化
- ✅ データ保持期間を14ヶ月に設定
- ✅ GTM設定ヘルパーの生成

### レポート生成

日次レポート（前日分）：
```bash
python src/main.py generate-report
```

特定日のレポート：
```bash
python src/main.py generate-report --date=2024-06-15
```

期間レポート：
```bash
python src/main.py generate-period-report --start-date=2024-06-01 --end-date=2024-06-30
```

### すべての処理を実行
```bash
python src/main.py all
```

### システム情報の確認
```bash
python src/main.py info
```

## ディレクトリ構造

```
ga4-campaign-automation/
├── campaigns.yml           # キャンペーン設定
├── config/
│   ├── ga4_config.json    # GA4設定
│   └── credentials.json   # 認証情報（要作成）
├── src/
│   ├── qr_generator.py    # QRコード生成
│   ├── ga4_setup.py       # GA4自動設定
│   ├── report_generator.py # レポート生成
│   └── main.py            # メインCLI
├── output/
│   ├── qr_codes/          # 生成されたQRコード
│   └── reports/           # レポート出力
├── requirements.txt       # 依存パッケージ
└── README.md             # このファイル
```

## レポートの見方

生成されるレポートには以下の情報が含まれます：

- **キャンペーン名**: 日本語のわかりやすい名前
- **配布場所**: チラシやポスターの配布場所
- **予算**: キャンペーン予算
- **セッション数**: QRコード経由の訪問数
- **ユーザー数**: ユニークユーザー数
- **新規ユーザー**: 初回訪問者数
- **直帰率**: すぐに離脱した割合
- **コンバージョン**: 目標達成数
- **CPA**: 1コンバージョンあたりのコスト
- **セッション単価**: 1訪問あたりのコスト

## 設定の詳細

### 自動設定される項目

#### カスタムディメンション
- `campaign_id` - キャンペーンID
- `campaign_name` - キャンペーン名（日本語）
- `campaign_location` - 配布場所
- `print_medium` - 印刷媒体タイプ
- `utm_source` - UTMソース
- `utm_medium` - UTMメディア
- `utm_campaign` - UTMキャンペーン
- `utm_content` - UTMコンテンツ
- `utm_term` - UTMキーワード

#### GTM設定ヘルパー
`output/reports/gtm_setup_helper.json`に以下の情報が生成されます：
- UTMパラメータのマッピング設定
- GA4設定タグの例
- 推奨トリガーの設定

## トラブルシューティング

### 認証エラーが発生する場合

1. **権限エラーの場合**
   ```bash
   python scripts/setup_permissions.py
   ```
   表示されるサービスアカウントのメールアドレスをGA4に追加（編集者権限）

2. **APIが有効化されていない場合**
   - Google Analytics Data API
   - Google Analytics Admin API
   を[Google Cloud Console](https://console.cloud.google.com/)で有効化

3. **認証ファイルの確認**
   - `config/credentials.json`が正しく配置されているか確認
   - サービスアカウントの認証キーが有効か確認

### データが取得できない場合

1. UTMパラメータが正しく設定されているか確認
2. GA4でデータが記録されているか確認（24-48時間のタイムラグあり）
3. カスタムディメンションが正しく設定されているか確認

### QRコードが読み取れない場合

1. QRコードのサイズが小さすぎないか確認
2. 印刷品質が十分か確認
3. URLが長すぎる場合は短縮URLの使用を検討

## 更新履歴

### v1.1.0 (2025-01-07)
- ✨ コンバージョンイベントのカスタマイズ機能追加
- ✨ 拡張計測機能の自動有効化
- ✨ データ保持期間の自動設定（14ヶ月）
- ✨ GTM設定ヘルパーの生成機能
- 🐛 Google Analytics Admin API v1alphaとの互換性修正
- 📝 権限設定ヘルパースクリプト追加

### v1.0.0 (2025-01-06)
- 🎉 初回リリース
- QRコード生成機能
- GA4カスタムディメンション自動設定
- レポート生成機能

## 注意事項

- GA4のデータ反映には24-48時間かかる場合があります
- カスタムディメンションは最大50個まで作成可能です（GA4の制限）
- コンバージョンイベントは最大30個まで作成可能です（GA4の制限）
- レポートデータの精度は、GA4の設定とトラッキング実装に依存します

## 貢献

プルリクエストを歓迎します！バグ報告や機能要望は[Issues](https://github.com/GIZIN/ga4-campaign-automation/issues)へ。

## ライセンス

このプロジェクトはMITライセンスで公開されています。