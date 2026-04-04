#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本
多数据源 + 每条新闻可点击
"""

import requests
from datetime import datetime, timedelta
import os
import json
import xml.etree.ElementTree as ET
import re

class XinwenLianbo:
    """新闻联播获取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml,text/xml,*/*'
        }

    def get_latest_news(self):
        """获取最新新闻"""
        sources = [
            ('RSSHub镜像1', "https://rsshub.rssforever.com/cctv/xwlb"),
            ('RSSHub官方', "https://rsshub.app/cctv/xwlb"),
            ('RSSHub镜像2', "https://rsshub.liumingye.cn/cctv/xwlb"),
        ]

        for name, url in sources:
            print(f"📡 尝试 {name}...")
            try:
                resp = requests.get(url, headers=self.headers, timeout=20)
                if resp.status_code == 200:
                    news = self._parse_rss(resp.content)
                    if news:
                        print(f"✅ {name} 成功")
                        return news
            except Exception as e:
                print(f"  ❌ {str(e)[:50]}")

        return None

    def _parse_rss(self, content):
        """解析RSS，返回所有新闻条目"""
        root = ET.fromstring(content)
        items = []
        
        for item in root.iter('item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            pub_date = item.findtext('pubDate', '')

            if title:
                # 提取单条新闻标题（从描述中解析）
                news_items = self._parse_news_items(desc)
                date_str = self._parse_date(pub_date)
                
                return {
                    'title': title,
                    'date': date_str,
                    'items': news_items,  # 新闻条目列表
                    'url': link
                }
        return None

    def _parse_news_items(self, desc):
        """解析新闻条目，提取每条新闻的标题和链接"""
        items = []
        if not desc:
            return items
        
        # RSSHub返回的格式通常包含多条新闻
        # 格式类似: "1. 标题 2. 标题..." 或带链接的HTML
        
        # 先清理HTML
        text = re.sub(r'<br\s*/?>', '\n', desc)
        text = re.sub(r'</p>', '\n', text)
        
        # 提取带链接的新闻项
        link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, desc)
        
        if links:
            for url, title in links:
                title = title.strip()
                if title and len(title) > 2:
                    items.append({
                        'title': title,
                        'url': url
                    })
        
        # 如果没提取到链接，按编号分割
        if not items:
            # 按数字编号分割
            lines = re.split(r'\d+[\.、]\s*', text)
            for line in lines:
                line = line.strip()
                if line and len(line) > 5:
                    items.append({
                        'title': line[:100],  # 限制长度
                        'url': ''
                    })
        
        return items

    def _parse_date(self, pub_date):
        """解析日期"""
        if pub_date:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub_date)
                return dt.strftime('%Y年%m月%d日')
            except:
                pass
        return datetime.now().strftime('%Y年%m月%d日')


class PushPlus:
    def __init__(self, token):
        self.token = token

    def push_html(self, title, news_items, date_str, main_url):
        """推送HTML格式，每条新闻可点击"""
        if not self.token:
            return False
        try:
            # 构建新闻列表HTML
            items_html = ""
            for i, item in enumerate(news_items, 1):
                item_title = item['title'][:80]  # 限制标题长度
                item_url = item.get('url', '')
                
                if item_url:
                    items_html += f"""
            <div class="item">
                <a href="{item_url}" class="item-link">
                    <span class="num">{i}</span>
                    <span class="title">{item_title}</span>
                    <span class="arrow">›</span>
                </a>
            </div>"""
                else:
                    items_html += f"""
            <div class="item">
                <span class="num">{i}</span>
                <span class="title">{item_title}</span>
            </div>"""

            html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; padding: 12px; }
        .container { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #c41e3a, #8b0000); color: #fff; padding: 20px 16px; text-align: center; }
        .header h1 { font-size: 22px; font-weight: 600; margin-bottom: 6px; }
        .header .date { font-size: 14px; opacity: 0.9; }
        .content { padding: 8px 0; }
        .item { border-bottom: 1px solid #f0f0f0; }
        .item:last-child { border-bottom: none; }
        .item-link { display: flex; align-items: center; padding: 14px 16px; text-decoration: none; color: #333; }
        .num { display: inline-block; width: 24px; height: 24px; line-height: 24px; text-align: center; background: #f5f5f5; border-radius: 50%; font-size: 12px; color: #666; margin-right: 12px; flex-shrink: 0; }
        .title { flex: 1; font-size: 15px; line-height: 1.5; color: #333; }
        .arrow { color: #ccc; font-size: 18px; margin-left: 8px; flex-shrink: 0; }
        .footer { padding: 16px; text-align: center; background: #fafafa; }
        .btn { display: inline-block; background: #c41e3a; color: #fff; padding: 10px 28px; border-radius: 20px; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📺 新闻联播</h1>
            <div class="date">""" + date_str + """</div>
        </div>
        <div class="content">
""" + items_html + """
        </div>
        <div class="footer">
            <a class="btn" href='""" + main_url + """'>查看完整内容</a>
        </div>
    </div>
</body>
</html>"""

            r = requests.post(
                "http://www.pushplus.plus/send",
                json={
                    "token": self.token,
                    "title": title,
                    "content": html,
                    "template": "html"
                },
                timeout=15
            ).json()
            return r.get('code') == 200
        except Exception as e:
            print(f"推送异常: {e}")
            return False


def main():
    print("=" * 50)
    print(f"📺 新闻联播 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    crawler = XinwenLianbo()
    news = crawler.get_latest_news()

    if news:
        print(f"\n📰 标题: {news['title']}")
        print(f"📅 日期: {news['date']}")
        print(f"📋 条目数: {len(news['items'])}")

        token = os.environ.get('PUSHPLUS_TOKEN')
        if token:
            print("\n📤 推送中...")
            pusher = PushPlus(token)

            title = f"📺 新闻联播 {news['date']}"
            success = pusher.push_html(
                title=title,
                news_items=news['items'],
                date_str=news['date'],
                main_url=news['url']
            )

            if success:
                print("✅ HTML推送成功！")
            else:
                print("❌ 推送失败")

        # 保存
        with open(f'xinwen_lianbo_{datetime.now():%Y-%m-%d}.txt', 'w', encoding='utf-8') as f:
            for i, item in enumerate(news['items'], 1):
                f.write(f"{i}. {item['title']}\n")
                if item.get('url'):
                    f.write(f"   {item['url']}\n")
            f.write(f"\n完整链接: {news['url']}\n")
        print("💾 已保存")
    else:
        print("\n❌ 所有数据源均不可用")


if __name__ == "__main__":
    main()