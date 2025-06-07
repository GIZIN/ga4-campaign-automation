#!/bin/bash

# GA4権限設定の半自動化スクリプト

echo "🚀 GA4権限設定の半自動化を開始します..."

# サービスアカウントのメールアドレスを取得
SERVICE_ACCOUNT=$(python3 -c "
import json
with open('config/credentials.json', 'r') as f:
    print(json.load(f).get('client_email', ''))
")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo "❌ サービスアカウント情報が見つかりません"
    exit 1
fi

echo "📧 サービスアカウント: $SERVICE_ACCOUNT"

# クリップボードにコピー
echo "$SERVICE_ACCOUNT" | pbcopy
echo "✅ メールアドレスをクリップボードにコピーしました！"

# GA4を開く
echo "🌐 GA4管理画面を開いています..."
open "https://analytics.google.com/"

echo ""
echo "📋 次の手順を実行してください:"
echo "1. 管理 → プロパティのアクセス管理"
echo "2. ＋ボタン → ユーザーを追加"
echo "3. Cmd+V でメールアドレスを貼り付け"
echo "4. 役割を「編集者」に設定"
echo "5. 追加をクリック"
echo ""
echo "完了したら、以下のコマンドを実行:"
echo "python3 src/main.py configure-ga4"