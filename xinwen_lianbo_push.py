#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本
多数据源 + 本地缓存机制
"""

import requests
from datetime import datetime, timedelta
import os
import json
import xml.etree.ElementTree as ET

class XinwenLianbo:
    """新闻联播获取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml,text/xml,*/*'
        }

    def get_latest_news(self):
        """获取最新新闻"""
        # 数据源列表（按稳定性排序）
        sources = [
            ('央视网RSS', self._fetch_cctv_rss),
            ('RSSHub官方', self._fetch_rsshub),
            ('RSSHub镜像1', self._fetch_rsshub_mirror1),
            ('RSSHub镜像2', self._fetch_rsshub_mirror2),
        ]

        for name, fetch_func in sources:
            print(f"📡 尝试 {name}...")
            try:
                news = fetch_func()
                if news and news.get('content'):
                    print(f"✅ {name} 成功")
                    return news
            except Exception as e:
                print(f"  ❌ {str(e)[:50]}")

        return None

    def _fetch_cctv_rss(self):
        """央视网官方RSS"""
        url = "https://news.cctv.com/world/rss/world.xml"
        resp = requests.get(url, headers=self.headers, timeout=15)
        return self._parse_rss_content(resp.content, '新闻联播')

    def _fetch_rsshub(self):
        """RSSHub官方"""
        url = "https://rsshub.app/cctv/xwlb"
        resp = requests.get(url, headers=self.headers, timeout=20)
        return self._parse_rss(resp.content)

    def _fetch_rsshub_mirror1(self):
        """RSSHub镜像"""
        url = "https://rsshub.rssforever.com/cctv/xwlb"
        resp = requests.get(url, headers=self.headers, timeout=20)
        return self._parse_rss(resp.content)

    def _fetch_rsshub_mirror2(self):
        """RSSHub镜像2"""
        url = "https://rsshub.liumingye.cn/cctv/xwlb"
        resp = requests.get(url, headers=self.headers, timeout=20)
        return self._parse_rss(resp.content)

    def _parse_rss(self, content):
        """解析RSS"""
        root = ET.fromstring(content)
        for item in root.iter('item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            pub_date = item.findtext('pubDate', '')

            if title and '新闻联播' in (title + desc):
                date = self._parse_date(pub_date)
                return {
                    'title': title,
                    'date': date,
                    'content': self._clean_content(desc),
                    'url': link
                }
        return None

    def _parse_rss_content(self, content, keyword):
        """解析RSS内容"""
        root = ET.fromstring(content)
        for item in root.iter('item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            pub_date = item.findtext('pubDate', '')

            date = self._parse_date(pub_date)
            return {
                'title': title or f'新闻联播 {date}',
                'date': date,
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
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        return datetime.now().strftime('%Y-%m-%d')

    def _clean_content(self, content):
        """清理内容"""
        if not content:
            return ''
        # 移除HTML标签
        import re
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        return content


class PushPlus:
    def __init__(self, token):
        self.token = token

    def push(self, title, content):
        if not self.token:
            return False
        try:
            r = requests.post(
                "http://www.pushplus.plus/send",
                json={
                    "token": self.token,
                    "title": title,
                    "content": content,
                    "template": "markdown"
                },
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
        print(f"\n📰 标题: {news['title'][:50]}")
        print(f"📅 日期: {news['date']}")
        print(f"📄 内容: {len(news['content'])}字")

        content = news['content'][:3500] if len(news['content']) > 3500 else news['content']

        md = f"""# {news['title']}

**日期**: {news['date']}

{content}

---
[阅读原文]({news['url']})"""

        token = os.environ.get('PUSHPLUS_TOKEN')
        if token:
            print("\n📤 推送中...")
            if PushPlus(token).push(f"📺 新闻联播 {news['date']}", md):
                print("✅ 推送成功！")
            else:
                print("❌ 推送失败")

        # 保存
        with open(f'xinwen_lianbo_{datetime.now():%Y-%m-%d}.txt', 'w', encoding='utf-8') as f:
            f.write(f"{news['title']}\n\n{news['date']}\n\n{content}\n\n{news['url']}")
        print("💾 已保存")
    else:
        print("\n❌ 所有数据源均不可用")


if __name__ == "__main__":
    main()