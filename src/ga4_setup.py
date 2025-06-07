#!/usr/bin/env python3

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import CustomDimension, DataStream
from google.oauth2 import service_account
import json
import yaml
import os
import sys
from datetime import datetime


class GA4Setup:
    def __init__(self, credentials_path='config/credentials.json', config_path='config/ga4_config.json'):
        self.credentials_path = credentials_path
        self.config_path = config_path
        self.client = None
        self.property_id = None
        self.config = {}
        
    def load_config(self):
        """GA4設定を読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.property_id = self.config.get('property_id')
                if not self.property_id:
                    print("エラー: property_idが設定されていません")
                    sys.exit(1)
                print(f"✓ GA4設定を読み込みました (Property ID: {self.property_id})")
        except FileNotFoundError:
            print(f"エラー: {self.config_path} が見つかりません")
            print("ヒント: config/ga4_config.json を作成してください")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"エラー: JSONファイルの解析に失敗しました: {e}")
            sys.exit(1)
            
    def authenticate(self):
        """Google Analytics Admin APIの認証"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/analytics.edit']
            )
            self.client = AnalyticsAdminServiceClient(credentials=credentials)
            print("✓ Google Analytics Admin APIの認証に成功しました")
        except FileNotFoundError:
            print(f"エラー: {self.credentials_path} が見つかりません")
            print("ヒント: Googleコンソールからサービスアカウントの認証ファイルをダウンロードしてください")
            sys.exit(1)
        except Exception as e:
            print(f"エラー: 認証に失敗しました: {e}")
            sys.exit(1)
            
    def get_custom_dimensions(self):
        """既存のカスタムディメンションを取得"""
        try:
            parent = f"properties/{self.property_id}"
            dimensions = []
            
            for dimension in self.client.list_custom_dimensions(parent=parent):
                dimensions.append({
                    'name': dimension.name,
                    'display_name': dimension.display_name,
                    'parameter_name': dimension.parameter_name,
                    'scope': dimension.scope.name
                })
                
            return dimensions
        except Exception as e:
            print(f"警告: カスタムディメンションの取得に失敗しました: {e}")
            return []
            
    def create_custom_dimension(self, parameter_name, display_name, description=""):
        """カスタムディメンションを作成"""
        try:
            parent = f"properties/{self.property_id}"
            
            # 既存のディメンションをチェック
            existing = self.get_custom_dimensions()
            for dim in existing:
                if dim['parameter_name'] == parameter_name:
                    print(f"  - スキップ: {display_name} (既に存在します)")
                    return dim
                    
            # 新規作成
            dimension = CustomDimension(
                parameter_name=parameter_name,
                display_name=display_name,
                description=description,
                scope=CustomDimension.DimensionScope.EVENT
            )
            
            response = self.client.create_custom_dimension(
                parent=parent,
                custom_dimension=dimension
            )
            
            print(f"  ✓ 作成: {display_name} ({parameter_name})")
            return response
            
        except Exception as e:
            print(f"  ✗ エラー: {display_name} の作成に失敗しました: {e}")
            return None
            
    def setup_custom_dimensions(self):
        """必要なカスタムディメンションをセットアップ"""
        print("\n📊 カスタムディメンションのセットアップ...")
        
        dimensions = [
            {
                'parameter_name': 'campaign_id',
                'display_name': 'キャンペーンID',
                'description': '紙媒体広告のキャンペーンID'
            },
            {
                'parameter_name': 'campaign_name',
                'display_name': 'キャンペーン名',
                'description': '紙媒体広告のキャンペーン名（日本語）'
            },
            {
                'parameter_name': 'campaign_location',
                'display_name': '配布場所',
                'description': '紙媒体広告の配布場所'
            },
            {
                'parameter_name': 'print_medium',
                'display_name': '印刷媒体タイプ',
                'description': 'チラシ、ポスター等の媒体種別'
            }
        ]
        
        for dim in dimensions:
            self.create_custom_dimension(
                parameter_name=dim['parameter_name'],
                display_name=dim['display_name'],
                description=dim['description']
            )
            
    def get_data_streams(self):
        """データストリームを取得"""
        try:
            parent = f"properties/{self.property_id}"
            streams = []
            
            for stream in self.client.list_data_streams(parent=parent):
                streams.append({
                    'name': stream.name,
                    'display_name': stream.display_name,
                    'type': stream.type_.name,
                    'web_stream_data': stream.web_stream_data if hasattr(stream, 'web_stream_data') else None
                })
                
            return streams
        except Exception as e:
            print(f"警告: データストリームの取得に失敗しました: {e}")
            return []
            
    def setup_enhanced_measurement(self):
        """拡張計測機能の設定"""
        print("\n🔧 拡張計測機能の確認...")
        
        streams = self.get_data_streams()
        if not streams:
            print("  ⚠️  データストリームが見つかりません")
            return
            
        for stream in streams:
            print(f"  ✓ データストリーム: {stream['display_name']} ({stream['type']})")
            
    def save_setup_report(self):
        """セットアップレポートを保存"""
        report_path = 'output/reports/ga4_setup_report.json'
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        report = {
            'setup_date': datetime.now().isoformat(),
            'property_id': self.property_id,
            'custom_dimensions': self.get_custom_dimensions(),
            'data_streams': self.get_data_streams()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 セットアップレポートを保存しました: {report_path}")
        
    def setup_all(self):
        """すべてのGA4設定を実行"""
        print("🚀 GA4自動設定を開始します...")
        
        # 設定読み込み
        self.load_config()
        
        # 認証
        self.authenticate()
        
        # カスタムディメンション設定
        self.setup_custom_dimensions()
        
        # 拡張計測機能の確認
        self.setup_enhanced_measurement()
        
        # レポート保存
        self.save_setup_report()
        
        print("\n✅ GA4設定が完了しました！")
        print("\n📝 次のステップ:")
        print("1. Google Tag Manager (GTM) でカスタムイベントを設定")
        print("2. UTMパラメータをカスタムディメンションにマッピング")
        print("3. GA4の探索レポートでカスタムディメンションを使用")


def main():
    setup = GA4Setup()
    setup.setup_all()


if __name__ == "__main__":
    main()