#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本
多数据源 + 友好格式推送
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
        """解析RSS"""
        root = ET.fromstring(content)
        for item in root.iter('item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            pub_date = item.findtext('pubDate', '')

            if title:
                return {
                    'title': title,
                    'date': self._parse_date(pub_date),
                    'content': self._clean_content(desc),
                    'url': link
                }
        return None

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

    def _clean_content(self, content):
        """清理并格式化内容"""
        if not content:
            return ''
        # 移除HTML标签
        content = re.sub(r'<br\s*/?>', '\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'&nbsp;', ' ', content)
        content = re.sub(r'&[a-z]+;', '', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'\s+', ' ', content).strip()
        return content


class PushPlus:
    def __init__(self, token):
        self.token = token

    def push_html(self, title, content, news_url):
        """推送HTML格式（支持链接跳转）"""
        if not self.token:
            return False
        try:
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #c41e3a, #8b0000); color: #fff; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header .date {{ margin-top: 8px; opacity: 0.9; }}
        .content {{ padding: 20px; line-height: 1.8; color: #333; font-size: 15px; }}
        .content p {{ margin: 0 0 12px 0; text-indent: 2em; }}
        .footer {{ padding: 20px; text-align: center; border-top: 1px solid #eee; }}
        .btn {{ display: inline-block; background: #c41e3a; color: #fff; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-size: 14px; }}
        .btn:hover {{ background: #a01830; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📺 新闻联播</h1>
            <div class="date">{title.split()[-1] if title else ''}</div>
        </div>
        <div class="content">
            {content.replace('\n\n', '</p><p>').replace('\n', '<br/>')}
        </div>
        <div class="footer">
            <a class="btn" href="{news_url}">阅读原文</a>
        </div>
    </div>
</body>
</html>
"""
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

    def push_txt(self, title, content, news_url):
        """推送txt格式（兼容性好）"""
        if not self.token:
            return False
        try:
            txt = f"""📺 新闻联播

{title}

━━━━━━━━━━━━━

{content}

━━━━━━━━━━━━━

📎 点击链接阅读原文：
{news_url}

💡 复制链接到浏览器打开"""
            r = requests.post(
                "http://www.pushplus.plus/send",
                json={
                    "token": self.token,
                    "title": title,
                    "content": txt,
                    "template": "txt"
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

        content = news['content']
        if len(content) > 3000:
            content = content[:3000] + '...'

        token = os.environ.get('PUSHPLUS_TOKEN')
        if token:
            print("\n📤 推送中...")
            pusher = PushPlus(token)

            # 使用HTML格式推送（链接可点击）
            title = f"📺 新闻联播 {news['date']}"
            success = pusher.push_html(title, content, news['url'])

            if success:
                print("✅ 推送成功！")
            else:
                # 降级为txt格式
                print("HTML推送失败，尝试txt格式...")
                if pusher.push_txt(title, content, news['url']):
                    print("✅ 推送成功！")

        # 保存
        with open(f'xinwen_lianbo_{datetime.now():%Y-%m-%d}.txt', 'w', encoding='utf-8') as f:
            f.write(f"{news['title']}\n\n{news['date']}\n\n{content}\n\n{news['url']}")
        print("💾 已保存")
    else:
        print("\n❌ 所有数据源均不可用")


if __name__ == "__main__":
    main()