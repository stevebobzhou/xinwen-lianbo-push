#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本
使用稳定的RSS源
"""

import requests
from datetime import datetime
import os
import xml.etree.ElementTree as ET

class XinwenLianbo:
    """新闻联播获取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_latest_news(self):
        """获取最新新闻"""
        # 使用RSSHub
        rss_sources = [
            "https://rsshub.app/cctv/xwlb",
            "https://rsshub.rssforever.com/cctv/xwlb",
            "https://rsshub.liumingye.cn/cctv/xwlb",
        ]

        for url in rss_sources:
            print(f"📡 尝试: {url[:30]}...")
            try:
                resp = requests.get(url, headers=self.headers, timeout=20)
                if resp.status_code == 200:
                    news = self._parse_rss(resp.content)
                    if news:
                        print(f"✅ 成功")
                        return news
            except Exception as e:
                print(f"  ❌ {str(e)[:40]}")

        return None

    def _parse_rss(self, content):
        """解析RSS"""
        try:
            root = ET.fromstring(content)
            # 找到第一个item
            for item in root.iter('item'):
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                desc = item.findtext('description', '')
                pub_date = item.findtext('pubDate', '')

                if title:
                    # 解析日期
                    date = datetime.now().strftime('%Y-%m-%d')
                    if pub_date:
                        try:
                            from email.utils import parsedate_to_datetime
                            dt = parsedate_to_datetime(pub_date)
                            date = dt.strftime('%Y-%m-%d')
                        except:
                            pass

                    return {
                        'title': title,
                        'date': date,
                        'content': desc,
                        'url': link
                    }
        except Exception as e:
            print(f"  解析失败: {e}")
        return None


class PushPlus:
    def __init__(self, token):
        self.token = token

    def push(self, title, content):
        if not self.token:
            return False
        try:
            r = requests.post(
                "http://www.pushplus.plus/send",
                json={"token": self.token, "title": title, "content": content, "template": "markdown"},
                timeout=15
            ).json()
            return r.get('code') == 200
        except:
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

        content = news['content'][:3000] if len(news['content']) > 3000 else news['content']

        md = f"""# {news['title']}

**日期**: {news['date']}

{content}

---
[阅读原文]({news['url']})"""

        token = os.environ.get('PUSHPLUS_TOKEN')
        if token:
            print("\n📤 推送中...")
            if PushPlus(token).push(f"新闻联播 {news['date']}", md):
                print("✅ 推送成功！请查收微信")
            else:
                print("❌ 推送失败")

        # 保存
        with open(f'xinwen_lianbo_{datetime.now():%Y-%m-%d}.txt', 'w', encoding='utf-8') as f:
            f.write(f"{news['title']}\n\n{news['date']}\n\n{content}\n\n{news['url']}")
        print("💾 已保存")
    else:
        print("\n❌ 获取失败，所有数据源均不可用")


if __name__ == "__main__":
    main()