#!/usr/bin/env python3

import json
import sys
import os
import subprocess
from pathlib import Path

def check_gcloud_cli():
    """gcloud CLIがインストールされているか確認"""
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_service_account_email():
    """サービスアカウントのメールアドレスを取得"""
    creds_path = Path(__file__).parent.parent / 'config' / 'credentials.json'
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            return creds.get('client_email')
    except:
        return None

def main():
    print("🔐 GA4権限設定ヘルパー\n")
    
    # サービスアカウント情報を取得
    service_account = get_service_account_email()
    if not service_account:
        print("❌ サービスアカウント情報が見つかりません")
        sys.exit(1)
    
    print(f"📧 サービスアカウント: {service_account}")
    print("\n" + "="*60)
    
    # 手動設定の手順を表示
    print("\n📋 GA4での権限設定手順:\n")
    print("1. GA4管理画面にアクセス")
    print("   https://analytics.google.com/")
    print("\n2. プロパティのアクセス管理を開く")
    print("   管理 → プロパティのアクセス管理")
    print("\n3. ユーザーを追加")
    print("   ＋ボタン → ユーザーを追加")
    print(f"\n4. 以下のメールアドレスをコピーして貼り付け:")
    print(f"   {service_account}")
    print("\n5. 役割を「編集者」に設定して追加")
    
    print("\n" + "="*60)
    
    # クリップボードにコピー（macOS）
    if sys.platform == "darwin":
        try:
            subprocess.run(['pbcopy'], input=service_account.encode(), check=True)
            print("\n✅ サービスアカウントのメールアドレスをクリップボードにコピーしました！")
            print("   GA4の画面で貼り付けてください (Cmd+V)")
        except:
            pass
    
    # GA4 URLを開く提案
    print("\n💡 ヒント: 以下のコマンドでGA4を開けます:")
    print("   open https://analytics.google.com/")
    
    # 権限設定後の確認コマンド
    print("\n✅ 権限設定が完了したら、以下のコマンドを実行してください:")
    print("   python src/main.py configure-ga4")
    
    # オプション: Google Cloud IAMでの権限付与（組織レベル）
    if check_gcloud_cli():
        print("\n🔧 高度なオプション:")
        print("   組織レベルでGoogle Analytics管理者権限を付与する場合:")
        print(f"   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\")
        print(f"     --member='serviceAccount:{service_account}' \\")
        print(f"     --role='roles/analytics.admin'")

if __name__ == "__main__":
    main()