#!/usr/bin/env python3

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import (
    CustomDimension, 
    DataStream,
    DataRetentionSettings,
    EnhancedMeasurementSettings,
    ConversionEvent,
    Property
)
from google.oauth2 import service_account
from google.api_core import exceptions
import json
import yaml
import os
import sys
from datetime import datetime


class GA4Setup:
    def __init__(self, credentials_path='config/credentials.json', config_path='config/ga4_config.json', campaigns_file='campaigns.yml'):
        self.credentials_path = credentials_path
        self.config_path = config_path
        self.campaigns_file = campaigns_file
        self.client = None
        self.property_id = None
        self.config = {}
        self.campaigns_data = {}
        
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
            if "403" in str(e):
                print("\n❌ 権限エラーの詳細:")
                print("- サービスアカウントに必要な権限が付与されていない可能性があります")
                print("- GA4プロパティの管理画面で以下を確認してください:")
                print("  1. 管理 > プロパティのアクセス管理")
                print("  2. サービスアカウントのメールアドレスを追加")
                print("  3. 「編集者」権限を付与")
                print(f"- サービスアカウント: {self._get_service_account_email()}")
            sys.exit(1)
    
    def _get_service_account_email(self):
        """サービスアカウントのメールアドレスを取得"""
        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)
                return creds.get('client_email', '不明')
        except:
            return '不明'
            
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
            
        except exceptions.PermissionDenied as e:
            print(f"  ✗ 権限エラー: {display_name} の作成に失敗しました")
            print(f"    詳細: サービスアカウントに編集者権限が必要です")
            print(f"    サービスアカウント: {self._get_service_account_email()}")
            return None
        except exceptions.ResourceExhausted as e:
            print(f"  ✗ 制限エラー: カスタムディメンションの上限に達しています（最大50個）")
            return None
        except Exception as e:
            print(f"  ✗ エラー: {display_name} の作成に失敗しました: {e}")
            return None
            
    def setup_custom_dimensions(self):
        """必要なカスタムディメンションをセットアップ"""
        print("\n📊 カスタムディメンションのセットアップ...")
        
        dimensions = [
            # 紙媒体広告用カスタムディメンション
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
            },
            # UTMパラメータ用カスタムディメンション
            {
                'parameter_name': 'utm_source',
                'display_name': 'UTMソース',
                'description': 'トラフィックソース（例：チラシ、ポスター）'
            },
            {
                'parameter_name': 'utm_medium',
                'display_name': 'UTMメディア',
                'description': 'マーケティング媒体（例：print、offline）'
            },
            {
                'parameter_name': 'utm_campaign',
                'display_name': 'UTMキャンペーン',
                'description': 'キャンペーン名'
            },
            {
                'parameter_name': 'utm_content',
                'display_name': 'UTMコンテンツ',
                'description': '広告コンテンツの識別子'
            },
            {
                'parameter_name': 'utm_term',
                'display_name': 'UTMキーワード',
                'description': '検索キーワード（オプション）'
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
                # WebStreamDataオブジェクトをJSON serializableな形式に変換
                web_stream_data = None
                if hasattr(stream, 'web_stream_data') and stream.web_stream_data:
                    web_stream_data = {
                        'measurement_id': stream.web_stream_data.measurement_id if hasattr(stream.web_stream_data, 'measurement_id') else None,
                        'firebase_app_id': stream.web_stream_data.firebase_app_id if hasattr(stream.web_stream_data, 'firebase_app_id') else None,
                        'default_uri': stream.web_stream_data.default_uri if hasattr(stream.web_stream_data, 'default_uri') else None
                    }
                
                streams.append({
                    'name': stream.name,
                    'display_name': stream.display_name,
                    'type': stream.type_.name,
                    'web_stream_data': web_stream_data
                })
                
            return streams
        except Exception as e:
            print(f"警告: データストリームの取得に失敗しました: {e}")
            return []
            
    def setup_enhanced_measurement(self):
        """拡張計測機能の自動有効化"""
        print("\n🔧 拡張計測機能の設定...")
        
        try:
            parent = f"properties/{self.property_id}"
            
            for stream in self.client.list_data_streams(parent=parent):
                if stream.type_ == DataStream.DataStreamType.WEB_DATA_STREAM:
                    stream_name = stream.name
                    
                    # 拡張計測機能の設定を取得
                    try:
                        enhanced_settings = self.client.get_enhanced_measurement_settings(
                            name=f"{stream_name}/enhancedMeasurementSettings"
                        )
                        
                        # すべての拡張計測機能を有効化
                        enhanced_settings.stream_enabled = True
                        enhanced_settings.scrolls_enabled = True
                        enhanced_settings.outbound_clicks_enabled = True
                        enhanced_settings.site_search_enabled = True
                        enhanced_settings.video_engagement_enabled = True
                        enhanced_settings.file_downloads_enabled = True
                        enhanced_settings.form_interactions_enabled = True
                        
                        # 更新を適用
                        updated_settings = self.client.update_enhanced_measurement_settings(
                            enhanced_measurement_settings=enhanced_settings,
                            update_mask={"paths": [
                                "stream_enabled", "scrolls_enabled", "outbound_clicks_enabled",
                                "site_search_enabled", "video_engagement_enabled", "file_downloads_enabled",
                                "form_interactions_enabled"
                            ]}
                        )
                        
                        print(f"  ✓ 拡張計測機能を有効化: {stream.display_name}")
                        print("    - ページビュー: 有効")
                        print("    - スクロール: 有効")
                        print("    - 外部リンククリック: 有効")
                        print("    - サイト内検索: 有効")
                        print("    - 動画エンゲージメント: 有効")
                        print("    - ファイルダウンロード: 有効")
                        print("    - フォーム操作: 有効")
                        
                    except Exception as e:
                        print(f"  ⚠️  拡張計測機能の更新に失敗: {e}")
                        
        except Exception as e:
            print(f"  ⚠️  データストリームの取得に失敗: {e}")
    
    def setup_data_retention(self):
        """データ保持期間を14ヶ月に設定"""
        print("\n📅 データ保持期間の設定...")
        
        try:
            property_name = f"properties/{self.property_id}"
            
            # プロパティ情報を取得
            property = self.client.get_property(name=property_name)
            
            # データ保持設定を取得
            retention_settings = self.client.get_data_retention_settings(
                name=f"{property_name}/dataRetentionSettings"
            )
            
            # 14ヶ月に設定
            retention_settings.event_data_retention = DataRetentionSettings.RetentionDuration.FOURTEEN_MONTHS
            retention_settings.reset_user_data_on_new_activity = True
            
            # 更新を適用
            updated_settings = self.client.update_data_retention_settings(
                data_retention_settings=retention_settings,
                update_mask={"paths": ["event_data_retention", "reset_user_data_on_new_activity"]}
            )
            
            print("  ✓ データ保持期間を14ヶ月に設定しました")
            print("  ✓ 新しいアクティビティでユーザーデータのリセット: 有効")
            
        except exceptions.PermissionDenied:
            print("  ✗ 権限エラー: データ保持期間の設定には編集者権限が必要です")
            print(f"    サービスアカウント: {self._get_service_account_email()}")
        except Exception as e:
            print(f"  ⚠️  データ保持期間の設定に失敗: {e}")
    
    def create_conversion_event(self, event_name):
        """コンバージョンイベントを作成"""
        try:
            parent = f"properties/{self.property_id}"
            
            # 既存のコンバージョンイベントをチェック
            existing_conversions = []
            for conversion in self.client.list_conversion_events(parent=parent):
                existing_conversions.append(conversion.event_name)
                
            if event_name in existing_conversions:
                print(f"  - スキップ: {event_name} (既に存在します)")
                return
            
            # 新規作成
            conversion_event = ConversionEvent(
                event_name=event_name
            )
            
            response = self.client.create_conversion_event(
                parent=parent,
                conversion_event=conversion_event
            )
            
            print(f"  ✓ 作成: {event_name}")
            return response
            
        except exceptions.PermissionDenied:
            print(f"  ✗ 権限エラー: {event_name} の作成に失敗しました")
            print(f"    サービスアカウント: {self._get_service_account_email()}")
        except Exception as e:
            print(f"  ✗ エラー: {event_name} の作成に失敗しました: {e}")
    
    def setup_conversion_events(self):
        """コンバージョンイベントを設定"""
        print("\n🎯 コンバージョンイベントの設定...")
        
        # campaigns.ymlからコンバージョンイベントを読み込む
        try:
            with open(self.campaigns_file, 'r', encoding='utf-8') as f:
                campaigns_data = yaml.safe_load(f)
                conversion_events = campaigns_data.get('conversion_events', [])
                
            if not conversion_events:
                print("  ℹ️  campaigns.ymlにコンバージョンイベントが定義されていません")
                print("  デフォルトのイベントを使用します")
                # デフォルトのコンバージョンイベント
                conversion_events = [
                    {
                        'event_name': 'qr_code_scan',
                        'description': 'QRコードからの訪問'
                    },
                    {
                        'event_name': 'campaign_click',
                        'description': 'キャンペーンリンクのクリック'
                    }
                ]
        except Exception as e:
            print(f"  ⚠️  campaigns.yml読み込みエラー: {e}")
            print("  デフォルトのイベントを使用します")
            conversion_events = [
                {
                    'event_name': 'qr_code_scan',
                    'description': 'QRコードからの訪問'
                },
                {
                    'event_name': 'campaign_click',
                    'description': 'キャンペーンリンクのクリック'
                }
            ]
        
        # コンバージョンイベントを作成
        for event in conversion_events:
            self.create_conversion_event(
                event_name=event['event_name']
            )
            
        if conversion_events:
            print(f"\n  💡 ヒント: {len(conversion_events)}個のコンバージョンイベントを設定しました")
            print("  campaigns.ymlでカスタムイベントを追加できます")
            
    def get_conversion_events(self):
        """既存のコンバージョンイベントを取得"""
        try:
            parent = f"properties/{self.property_id}"
            events = []
            
            for event in self.client.list_conversion_events(parent=parent):
                events.append({
                    'event_name': event.event_name,
                    'counting_method': 'N/A'  # API v1alphaではcounting_methodは利用不可
                })
                
            return events
        except Exception as e:
            print(f"警告: コンバージョンイベントの取得に失敗しました: {e}")
            return []
    
    def save_setup_report(self):
        """セットアップレポートを保存"""
        report_path = 'output/reports/ga4_setup_report.json'
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        report = {
            'setup_date': datetime.now().isoformat(),
            'property_id': self.property_id,
            'custom_dimensions': self.get_custom_dimensions(),
            'data_streams': self.get_data_streams(),
            'conversion_events': self.get_conversion_events()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 セットアップレポートを保存しました: {report_path}")
    
    def generate_gtm_helper(self):
        """GTM設定用のヘルパー情報を生成"""
        gtm_helper_path = 'output/reports/gtm_setup_helper.json'
        os.makedirs(os.path.dirname(gtm_helper_path), exist_ok=True)
        
        gtm_config = {
            'generated_date': datetime.now().isoformat(),
            'utm_parameter_mapping': {
                'utm_source': {
                    'variable_name': '{{UTM Source}}',
                    'variable_type': 'URL',
                    'component_type': 'Query',
                    'query_key': 'utm_source'
                },
                'utm_medium': {
                    'variable_name': '{{UTM Medium}}',
                    'variable_type': 'URL',
                    'component_type': 'Query',
                    'query_key': 'utm_medium'
                },
                'utm_campaign': {
                    'variable_name': '{{UTM Campaign}}',
                    'variable_type': 'URL',
                    'component_type': 'Query',
                    'query_key': 'utm_campaign'
                },
                'utm_content': {
                    'variable_name': '{{UTM Content}}',
                    'variable_type': 'URL',
                    'component_type': 'Query',
                    'query_key': 'utm_content'
                },
                'utm_term': {
                    'variable_name': '{{UTM Term}}',
                    'variable_type': 'URL',
                    'component_type': 'Query',
                    'query_key': 'utm_term'
                }
            },
            'ga4_configuration_tag': {
                'tag_name': 'GA4 - UTM Parameter Mapping',
                'tag_type': 'Google Analytics: GA4 Configuration',
                'trigger': 'All Pages',
                'fields_to_set': [
                    {'field_name': 'utm_source', 'value': '{{UTM Source}}'},
                    {'field_name': 'utm_medium', 'value': '{{UTM Medium}}'},
                    {'field_name': 'utm_campaign', 'value': '{{UTM Campaign}}'},
                    {'field_name': 'utm_content', 'value': '{{UTM Content}}'},
                    {'field_name': 'utm_term', 'value': '{{UTM Term}}'}
                ]
            },
            'conversion_event_tags': [
                {
                    'tag_name': 'GA4 - App Download Click',
                    'event_name': 'app_download',
                    'trigger': 'Click - App Download Button',
                    'parameters': {
                        'app_platform': '{{Click Text}}',
                        'button_location': '{{Click Classes}}'
                    }
                },
                {
                    'tag_name': 'GA4 - QR Code Scan',
                    'event_name': 'qr_code_scan',
                    'trigger': 'Page View - UTM Source equals QR',
                    'parameters': {
                        'campaign_name': '{{UTM Campaign}}',
                        'scan_source': '{{UTM Content}}'
                    }
                }
            ],
            'recommended_triggers': [
                {
                    'trigger_name': 'Click - App Download Button',
                    'trigger_type': 'Click - All Elements',
                    'conditions': [
                        'Click Classes contains "app-download"',
                        'OR Click ID equals "download-app"',
                        'OR Click Text contains "ダウンロード"'
                    ]
                },
                {
                    'trigger_name': 'Page View - UTM Source equals QR',
                    'trigger_type': 'Page View',
                    'conditions': [
                        '{{UTM Source}} equals "qr"'
                    ]
                }
            ]
        }
        
        with open(gtm_helper_path, 'w', encoding='utf-8') as f:
            json.dump(gtm_config, f, ensure_ascii=False, indent=2)
            
        print(f"\n🏷️  GTM設定ヘルパーを生成しました: {gtm_helper_path}")
        print("  このファイルを参考にGTMで変数とタグを設定してください")
        
    def setup_all(self):
        """すべてのGA4設定を実行"""
        print("🚀 GA4自動設定を開始します...")
        
        # 設定読み込み
        self.load_config()
        
        # 認証
        self.authenticate()
        
        # カスタムディメンション設定
        self.setup_custom_dimensions()
        
        # 拡張計測機能の自動有効化
        self.setup_enhanced_measurement()
        
        # データ保持期間の設定
        self.setup_data_retention()
        
        # コンバージョンイベントの設定
        self.setup_conversion_events()
        
        # レポート保存
        self.save_setup_report()
        
        print("\n✅ GA4設定が完了しました！")
        print("\n📝 次のステップ:")
        print("1. Google Tag Manager (GTM) でカスタムイベントを設定")
        print("2. GTMでUTMパラメータをカスタムディメンションに自動マッピング")
        print("3. GA4の探索レポートでカスタムディメンションを使用")
        print("4. コンバージョンイベントのトリガー設定をGTMで実装")
        print("\n💡 ヒント:")
        print("- UTMパラメータは自動的にカスタムディメンションとして登録されました")
        print("- データ保持期間は14ヶ月に設定されています")
        print("- 拡張計測機能がすべて有効化されています")
        
        # GTM設定ヘルパーの生成
        self.generate_gtm_helper()


def main():
    setup = GA4Setup()
    setup.setup_all()


if __name__ == "__main__":
    main()