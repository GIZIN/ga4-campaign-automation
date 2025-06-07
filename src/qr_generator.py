#!/usr/bin/env python3

import qrcode
from PIL import Image, ImageDraw, ImageFont
import yaml
import os
import sys
from datetime import datetime
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
import hashlib


class QRCodeGenerator:
    def __init__(self, campaigns_file='campaigns.yml', output_dir='output/qr_codes'):
        self.campaigns_file = campaigns_file
        self.output_dir = output_dir
        self.campaigns = []
        
    def load_campaigns(self):
        """キャンペーン設定を読み込む"""
        try:
            with open(self.campaigns_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.campaigns = data.get('campaigns', [])
                print(f"✓ {len(self.campaigns)}件のキャンペーンを読み込みました")
        except FileNotFoundError:
            print(f"エラー: {self.campaigns_file} が見つかりません")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"エラー: YAMLファイルの解析に失敗しました: {e}")
            sys.exit(1)
            
    def generate_campaign_id(self, campaign):
        """キャンペーンIDを生成"""
        # 名前と開始日からユニークなIDを生成
        unique_str = f"{campaign['name']}_{campaign['start_date']}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:8]
        
    def build_utm_url(self, campaign):
        """UTMパラメータ付きURLを生成"""
        campaign_id = self.generate_campaign_id(campaign)
        
        # 既存のURLをパース
        parsed = urlparse(campaign['target_url'])
        query_params = parse_qs(parsed.query)
        
        # UTMパラメータを追加
        utm_params = {
            'utm_source': 'offline',
            'utm_medium': 'print',
            'utm_campaign': campaign_id,
            'utm_content': campaign['location'],
            'utm_term': campaign['name']
        }
        
        # 既存のクエリパラメータとマージ
        for key, value in utm_params.items():
            query_params[key] = [value]
            
        # URLを再構築
        new_query = urlencode(query_params, doseq=True)
        utm_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return utm_url, campaign_id
        
    def create_qr_with_label(self, url, campaign_name, campaign_id, location):
        """ラベル付きQRコードを生成"""
        # QRコード生成
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # QRコード画像を作成
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # キャンバスサイズを計算（QRコード + ラベルスペース）
        qr_width, qr_height = qr_img.size
        label_height = 120
        canvas_width = qr_width
        canvas_height = qr_height + label_height
        
        # 新しいキャンバスを作成
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # QRコードを貼り付け
        canvas.paste(qr_img, (0, 0))
        
        # テキストを描画
        draw = ImageDraw.Draw(canvas)
        
        # フォントサイズの設定（システムフォントを使用）
        try:
            # 日本語フォントを試す
            font_large = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc', 24)
            font_small = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc', 16)
        except:
            # フォールバック
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        # テキストを中央揃えで描画
        text_y = qr_height + 10
        
        # キャンペーン名
        bbox = draw.textbbox((0, 0), campaign_name, font=font_large)
        text_width = bbox[2] - bbox[0]
        draw.text(((canvas_width - text_width) // 2, text_y), 
                 campaign_name, fill='black', font=font_large)
        
        # 場所
        text_y += 35
        location_text = f"配布場所: {location}"
        bbox = draw.textbbox((0, 0), location_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text(((canvas_width - text_width) // 2, text_y), 
                 location_text, fill='gray', font=font_small)
        
        # キャンペーンID
        text_y += 25
        id_text = f"ID: {campaign_id}"
        bbox = draw.textbbox((0, 0), id_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        draw.text(((canvas_width - text_width) // 2, text_y), 
                 id_text, fill='gray', font=font_small)
        
        return canvas
        
    def generate_all(self):
        """すべてのキャンペーンのQRコードを生成"""
        # 出力ディレクトリを作成
        os.makedirs(self.output_dir, exist_ok=True)
        
        # キャンペーンを読み込む
        self.load_campaigns()
        
        if not self.campaigns:
            print("エラー: キャンペーンが定義されていません")
            return
            
        print(f"\n📱 QRコード生成を開始します...")
        
        for i, campaign in enumerate(self.campaigns, 1):
            try:
                # UTM URL生成
                utm_url, campaign_id = self.build_utm_url(campaign)
                
                # QRコード生成
                qr_image = self.create_qr_with_label(
                    utm_url,
                    campaign['name'],
                    campaign_id,
                    campaign['location']
                )
                
                # ファイル名を生成
                safe_name = campaign['name'].replace('/', '_').replace(' ', '_')
                filename = f"{campaign_id}_{safe_name}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                # 保存
                qr_image.save(filepath)
                
                print(f"✓ [{i}/{len(self.campaigns)}] {campaign['name']}")
                print(f"  - 保存先: {filepath}")
                print(f"  - URL: {utm_url}")
                print()
                
            except Exception as e:
                print(f"✗ エラー: {campaign['name']} の処理中にエラーが発生しました: {e}")
                
        print(f"✅ QRコード生成が完了しました！")
        print(f"📁 出力先: {self.output_dir}")


def main():
    generator = QRCodeGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()