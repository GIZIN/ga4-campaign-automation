#!/usr/bin/env python3

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter
)
from google.oauth2 import service_account
import pandas as pd
import yaml
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


class ReportGenerator:
    def __init__(self, 
                 credentials_path='config/credentials.json',
                 config_path='config/ga4_config.json',
                 campaigns_file='campaigns.yml'):
        self.credentials_path = credentials_path
        self.config_path = config_path
        self.campaigns_file = campaigns_file
        self.client = None
        self.property_id = None
        self.campaigns = []
        
    def load_config(self):
        """設定ファイルを読み込む"""
        # GA4設定
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.property_id = config.get('property_id')
                if not self.property_id:
                    print("エラー: property_idが設定されていません")
                    sys.exit(1)
        except FileNotFoundError:
            print(f"エラー: {self.config_path} が見つかりません")
            sys.exit(1)
            
        # キャンペーン設定
        try:
            with open(self.campaigns_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.campaigns = data.get('campaigns', [])
        except FileNotFoundError:
            print(f"エラー: {self.campaigns_file} が見つかりません")
            sys.exit(1)
            
    def authenticate(self):
        """Google Analytics Data APIの認証"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            print("✓ Google Analytics Data APIの認証に成功しました")
        except Exception as e:
            print(f"エラー: 認証に失敗しました: {e}")
            sys.exit(1)
            
    def generate_campaign_id(self, campaign):
        """キャンペーンIDを生成（QRジェネレーターと同じロジック）"""
        import hashlib
        unique_str = f"{campaign['name']}_{campaign['start_date']}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:8]
        
    def fetch_campaign_data(self, start_date, end_date, campaign_id=None):
        """GA4からキャンペーンデータを取得"""
        try:
            # リクエストの構築
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionCampaignId"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                    Dimension(name="customEvent:campaign_location"),
                    Dimension(name="landingPage")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="newUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate"),
                    Metric(name="conversions")
                ]
            )
            
            # キャンペーンIDでフィルタリング
            if campaign_id:
                request.dimension_filter = FilterExpression(
                    filter=Filter(
                        field_name="sessionCampaignId",
                        string_filter=Filter.StringFilter(value=campaign_id)
                    )
                )
                
            # APIリクエスト実行
            response = self.client.run_report(request)
            
            # データをDataFrameに変換
            data = []
            for row in response.rows:
                row_data = {}
                for i, dimension in enumerate(response.dimension_headers):
                    row_data[dimension.name] = row.dimension_values[i].value
                for i, metric in enumerate(response.metric_headers):
                    row_data[metric.name] = row.metric_values[i].value
                data.append(row_data)
                
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"警告: データ取得中にエラーが発生しました: {e}")
            return pd.DataFrame()
            
    def calculate_metrics(self, df, campaign):
        """メトリクスを計算"""
        if df.empty:
            return {
                'campaign_name': campaign['name'],
                'campaign_id': self.generate_campaign_id(campaign),
                'location': campaign['location'],
                'budget': campaign['budget'],
                'total_sessions': 0,
                'total_users': 0,
                'new_users': 0,
                'page_views': 0,
                'avg_session_duration': 0,
                'bounce_rate': 0,
                'conversions': 0,
                'cpa': 0,
                'cost_per_session': 0
            }
            
        # 数値型に変換
        numeric_columns = ['sessions', 'totalUsers', 'newUsers', 'screenPageViews', 
                          'averageSessionDuration', 'bounceRate', 'conversions']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # 集計
        total_sessions = df['sessions'].sum() if 'sessions' in df.columns else 0
        total_users = df['totalUsers'].sum() if 'totalUsers' in df.columns else 0
        new_users = df['newUsers'].sum() if 'newUsers' in df.columns else 0
        page_views = df['screenPageViews'].sum() if 'screenPageViews' in df.columns else 0
        avg_duration = df['averageSessionDuration'].mean() if 'averageSessionDuration' in df.columns else 0
        bounce_rate = df['bounceRate'].mean() if 'bounceRate' in df.columns else 0
        conversions = df['conversions'].sum() if 'conversions' in df.columns else 0
        
        # コスト計算
        budget = campaign['budget']
        cpa = budget / conversions if conversions > 0 else 0
        cost_per_session = budget / total_sessions if total_sessions > 0 else 0
        
        return {
            'campaign_name': campaign['name'],
            'campaign_id': self.generate_campaign_id(campaign),
            'location': campaign['location'],
            'budget': budget,
            'total_sessions': int(total_sessions),
            'total_users': int(total_users),
            'new_users': int(new_users),
            'page_views': int(page_views),
            'avg_session_duration': round(avg_duration, 2),
            'bounce_rate': round(bounce_rate, 2),
            'conversions': int(conversions),
            'cpa': round(cpa, 2),
            'cost_per_session': round(cost_per_session, 2)
        }
        
    def generate_daily_report(self, report_date=None):
        """日次レポートを生成"""
        if report_date is None:
            report_date = datetime.now().date() - timedelta(days=1)
        else:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            
        print(f"\n📊 {report_date} のレポートを生成中...")
        
        # 全キャンペーンの結果を収集
        results = []
        
        for campaign in self.campaigns:
            # キャンペーン期間内かチェック
            start_date = datetime.strptime(campaign['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(campaign['end_date'], '%Y-%m-%d').date()
            
            if not (start_date <= report_date <= end_date):
                continue
                
            print(f"  - {campaign['name']} を処理中...")
            
            # データ取得
            campaign_id = self.generate_campaign_id(campaign)
            df = self.fetch_campaign_data(
                start_date=str(report_date),
                end_date=str(report_date),
                campaign_id=campaign_id
            )
            
            # メトリクス計算
            metrics = self.calculate_metrics(df, campaign)
            metrics['report_date'] = str(report_date)
            results.append(metrics)
            
        # レポート保存
        if results:
            self.save_report(results, report_date)
        else:
            print("  ⚠️  有効なキャンペーンデータがありません")
            
    def save_report(self, results, report_date):
        """レポートを保存"""
        # CSVファイル
        output_dir = Path('output/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / f'daily_report_{report_date}.csv'
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✓ CSVレポート: {csv_path}")
        
        # サマリー表示
        print("\n📈 レポートサマリー:")
        print("-" * 80)
        
        for result in results:
            print(f"\n【{result['campaign_name']}】")
            print(f"  配布場所: {result['location']}")
            print(f"  予算: ¥{result['budget']:,}")
            print(f"  セッション数: {result['total_sessions']:,}")
            print(f"  ユーザー数: {result['total_users']:,}")
            print(f"  新規ユーザー: {result['new_users']:,}")
            print(f"  直帰率: {result['bounce_rate']}%")
            print(f"  コンバージョン: {result['conversions']:,}")
            print(f"  CPA: ¥{result['cpa']:,.0f}")
            print(f"  セッション単価: ¥{result['cost_per_session']:,.0f}")
            
        # 全体集計
        total_budget = sum(r['budget'] for r in results)
        total_sessions = sum(r['total_sessions'] for r in results)
        total_conversions = sum(r['conversions'] for r in results)
        
        print("\n" + "=" * 80)
        print("【全体集計】")
        print(f"  総予算: ¥{total_budget:,}")
        print(f"  総セッション数: {total_sessions:,}")
        print(f"  総コンバージョン: {total_conversions:,}")
        if total_conversions > 0:
            print(f"  平均CPA: ¥{total_budget/total_conversions:,.0f}")
            
    def generate_period_report(self, start_date, end_date):
        """期間レポートを生成"""
        print(f"\n📊 期間レポート生成: {start_date} 〜 {end_date}")
        
        # 全キャンペーンの結果を収集
        results = []
        
        for campaign in self.campaigns:
            print(f"  - {campaign['name']} を処理中...")
            
            # キャンペーン期間との重複をチェック
            campaign_start = datetime.strptime(campaign['start_date'], '%Y-%m-%d').date()
            campaign_end = datetime.strptime(campaign['end_date'], '%Y-%m-%d').date()
            report_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            report_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 期間の重複を計算
            actual_start = max(campaign_start, report_start)
            actual_end = min(campaign_end, report_end)
            
            if actual_start > actual_end:
                continue
                
            # データ取得
            campaign_id = self.generate_campaign_id(campaign)
            df = self.fetch_campaign_data(
                start_date=str(actual_start),
                end_date=str(actual_end),
                campaign_id=campaign_id
            )
            
            # メトリクス計算
            metrics = self.calculate_metrics(df, campaign)
            metrics['period'] = f"{actual_start} 〜 {actual_end}"
            results.append(metrics)
            
        # レポート保存
        if results:
            output_dir = Path('output/reports')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            csv_path = output_dir / f'period_report_{start_date}_to_{end_date}.csv'
            df = pd.DataFrame(results)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n✓ 期間レポート保存: {csv_path}")
            
    def run(self, mode='daily', date=None, start_date=None, end_date=None):
        """レポート生成を実行"""
        # 設定読み込み
        self.load_config()
        
        # 認証
        self.authenticate()
        
        # レポート生成
        if mode == 'daily':
            self.generate_daily_report(date)
        elif mode == 'period':
            if not start_date or not end_date:
                print("エラー: 期間レポートには開始日と終了日が必要です")
                sys.exit(1)
            self.generate_period_report(start_date, end_date)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GA4レポート生成ツール')
    parser.add_argument('--mode', choices=['daily', 'period'], default='daily',
                       help='レポートモード')
    parser.add_argument('--date', help='日次レポートの日付 (YYYY-MM-DD)')
    parser.add_argument('--start-date', help='期間レポートの開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='期間レポートの終了日 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    generator.run(
        mode=args.mode,
        date=args.date,
        start_date=args.start_date,
        end_date=args.end_date
    )


if __name__ == "__main__":
    main()