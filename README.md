# GA4 紙広告効果測定自動化システム

紙の広告（チラシ、ポスター等）にQRコードを掲載し、その効果測定をGoogle Analytics 4で自動的に行うシステムです。

## 特徴

- 📱 UTMパラメータ付きQRコードの自動生成
- 🎯 日本語でわかりやすいキャンペーン管理
- 📊 GA4のカスタムディメンション自動設定
- 📈 日次・期間レポートの自動生成
- 💰 CPA（獲得単価）の自動計算

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

`campaigns.yml`でキャンペーンを定義（サンプルは既に用意されています）

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
カスタムディメンションが自動的に作成されます。

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

## トラブルシューティング

### 認証エラーが発生する場合

1. `config/credentials.json`が正しく配置されているか確認
2. サービスアカウントにGA4プロパティへのアクセス権限があるか確認
3. 必要なAPIが有効化されているか確認

### データが取得できない場合

1. UTMパラメータが正しく設定されているか確認
2. GA4でデータが記録されているか確認（24-48時間のタイムラグあり）
3. カスタムディメンションが正しく設定されているか確認

### QRコードが読み取れない場合

1. QRコードのサイズが小さすぎないか確認
2. 印刷品質が十分か確認
3. URLが長すぎる場合は短縮URLの使用を検討

## 注意事項

- GA4のデータ反映には24-48時間かかる場合があります
- カスタムディメンションは最大125個まで作成可能です
- レポートデータの精度は、GA4の設定とトラッキング実装に依存します

## ライセンス

このプロジェクトはMITライセンスで公開されています。