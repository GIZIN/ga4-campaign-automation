#!/usr/bin/env python3

import click
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.qr_generator import QRCodeGenerator
from src.ga4_setup import GA4Setup
from src.report_generator import ReportGenerator


@click.group()
def cli():
    """GA4 紙広告効果測定自動化システム
    
    紙の広告（チラシ、ポスター等）の効果測定をGoogle Analytics 4で
    自動的に行うためのツールです。
    """
    pass


@cli.command()
def setup():
    """初期設定を実行
    
    必要なディレクトリ構造の作成と設定ファイルのチェックを行います。
    """
    click.echo("🚀 初期設定を開始します...")
    
    # ディレクトリ作成
    directories = [
        'config',
        'output/qr_codes',
        'output/reports'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ ディレクトリ作成: {dir_path}")
        
    # 設定ファイルチェック
    required_files = {
        'campaigns.yml': 'キャンペーン設定ファイル',
        'config/credentials.json': 'Google Cloud認証ファイル',
        'config/ga4_config.json': 'GA4設定ファイル'
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if not Path(file_path).exists():
            missing_files.append((file_path, description))
            click.echo(f"✗ {description}が見つかりません: {file_path}", err=True)
        else:
            click.echo(f"✓ {description}: {file_path}")
            
    if missing_files:
        click.echo("\n⚠️  以下のファイルを作成してください:", err=True)
        for file_path, description in missing_files:
            click.echo(f"  - {file_path} ({description})", err=True)
            
        # テンプレートの案内
        if any('ga4_config.json' in f[0] for f in missing_files):
            click.echo("\n📝 ga4_config.json のテンプレート:")
            click.echo('''
{
  "property_id": "YOUR_GA4_PROPERTY_ID",
  "measurement_id": "YOUR_MEASUREMENT_ID"
}
            ''')
            
    else:
        click.echo("\n✅ すべての設定ファイルが揃っています！")
        

@cli.command()
def generate_qr():
    """QRコードを生成
    
    campaigns.ymlに定義されたキャンペーンのQRコードを生成します。
    """
    try:
        generator = QRCodeGenerator()
        generator.generate_all()
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        sys.exit(1)
        

@cli.command()
def configure_ga4():
    """GA4の自動設定を実行
    
    カスタムディメンションなどのGA4設定を自動的に行います。
    """
    try:
        setup = GA4Setup()
        setup.setup_all()
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        sys.exit(1)
        

@cli.command()
@click.option('--date', help='レポート日付 (YYYY-MM-DD形式、省略時は前日)')
def generate_report(date):
    """日次レポートを生成
    
    指定日のキャンペーン効果測定レポートを生成します。
    """
    try:
        generator = ReportGenerator()
        generator.run(mode='daily', date=date)
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        sys.exit(1)
        

@cli.command()
@click.option('--start-date', required=True, help='開始日 (YYYY-MM-DD形式)')
@click.option('--end-date', required=True, help='終了日 (YYYY-MM-DD形式)')
def generate_period_report(start_date, end_date):
    """期間レポートを生成
    
    指定期間のキャンペーン効果測定レポートを生成します。
    """
    try:
        generator = ReportGenerator()
        generator.run(mode='period', start_date=start_date, end_date=end_date)
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        sys.exit(1)
        

@cli.command()
def all():
    """すべての処理を実行
    
    QRコード生成、GA4設定、レポート生成を順番に実行します。
    """
    click.echo("🚀 すべての処理を開始します...\n")
    
    # 1. QRコード生成
    click.echo("1️⃣ QRコード生成")
    try:
        generator = QRCodeGenerator()
        generator.generate_all()
    except Exception as e:
        click.echo(f"QRコード生成エラー: {e}", err=True)
        
    click.echo("\n" + "="*60 + "\n")
    
    # 2. GA4設定
    click.echo("2️⃣ GA4設定")
    try:
        setup = GA4Setup()
        setup.setup_all()
    except Exception as e:
        click.echo(f"GA4設定エラー: {e}", err=True)
        
    click.echo("\n" + "="*60 + "\n")
    
    # 3. レポート生成（前日分）
    click.echo("3️⃣ レポート生成（前日分）")
    try:
        reporter = ReportGenerator()
        reporter.run(mode='daily')
    except Exception as e:
        click.echo(f"レポート生成エラー: {e}", err=True)
        
    click.echo("\n✅ すべての処理が完了しました！")


@cli.command()
def info():
    """システム情報を表示
    
    現在の設定やキャンペーン情報を表示します。
    """
    click.echo("📊 GA4 紙広告効果測定システム 情報\n")
    
    # キャンペーン情報
    try:
        import yaml
        with open('campaigns.yml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            campaigns = data.get('campaigns', [])
            
        click.echo(f"📋 登録キャンペーン数: {len(campaigns)}")
        for i, campaign in enumerate(campaigns, 1):
            click.echo(f"\n  [{i}] {campaign['name']}")
            click.echo(f"      場所: {campaign['location']}")
            click.echo(f"      期間: {campaign['start_date']} 〜 {campaign['end_date']}")
            click.echo(f"      予算: ¥{campaign['budget']:,}")
            
    except Exception as e:
        click.echo(f"キャンペーン情報の読み込みエラー: {e}", err=True)
        
    # 出力ファイル情報
    click.echo("\n📁 出力ファイル:")
    
    qr_path = Path('output/qr_codes')
    if qr_path.exists():
        qr_files = list(qr_path.glob('*.png'))
        click.echo(f"  - QRコード: {len(qr_files)}個")
        
    report_path = Path('output/reports')
    if report_path.exists():
        report_files = list(report_path.glob('*.csv'))
        click.echo(f"  - レポート: {len(report_files)}個")


if __name__ == '__main__':
    cli()