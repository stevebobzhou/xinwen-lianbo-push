#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本
使用多个稳定数据源
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re

class XinwenLianbo:
    """新闻联播内容获取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })

    def get_latest_news(self):
        """获取最新新闻"""
        # 方法1: 央视网JSON API
        print("📡 尝试央视网API...")
        try:
            url = "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_4.json"
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            if data.get('data', {}).get('list'):
                item = data['data']['list'][0]
                detail = self._fetch_detail(item.get('url', ''))
                if detail:
                    return detail
        except Exception as e:
            print(f"  失败: {e}")

        # 方法2: RSSHub
        print("📡 尝试RSSHub...")
        try:
            url = "https://rsshub.app/cctv/xwlb"
            resp = self.session.get(url, timeout=20)
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')
            if items:
                first = items[0]
                title = first.find('title')
                desc = first.find('description')
                link = first.find('link')
                return {
                    'title': title.get_text() if title else '新闻联播',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'content': desc.get_text() if desc else '',
                    'url': link.get_text() if link else 'https://cctv.cctv.com/lm/xwlb/'
                }
        except Exception as e:
            print(f"  失败: {e}")

        # 方法3: 直接访问新闻联播页面
        print("📡 尝试央视网页面...")
        try:
            url = "https://news.cctv.com/xwlb"
            resp = self.session.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 找新闻链接
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                if 'xwlb' in href and '/202' in href:
                    detail = self._fetch_detail(href)
                    if detail:
                        return detail
        except Exception as e:
            print(f"  失败: {e}")

        return None

    def _fetch_detail(self, url):
        """获取详情页"""
        if not url:
            return None
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 标题
            title = ''
            for sel in ['h1', '.title', 'h2']:
                el = soup.select_one(sel)
                if el:
                    title = el.get_text(strip=True)
                    break

            # 日期
            date = datetime.now().strftime('%Y-%m-%d')
            for sel in ['.date', '.time', '.info']:
                el = soup.select_one(sel)
                if el:
                    m = re.search(r'\d{4}[-年]\d{1,2}[-月]\d{1,2}', el.get_text())
                    if m:
                        date = m.group().replace('年','-').replace('月','-').rstrip('日')
                        break

            # 内容
            content = ''
            for sel in ['.content', '#content_area', '.article-content']:
                el = soup.select_one(sel)
                if el:
                    ps = el.find_all('p')
                    content = '\n'.join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 10)
                    if content:
                        break

            return {
                'title': title or '新闻联播',
                'date': date,
                'content': content,
                'url': url
            }
        except Exception as e:
            print(f"  详情页失败: {e}")
        return None


class PushPlus:
    """PushPlus推送"""
    def __init__(self, token):
        self.token = token

    def push(self, title, content):
        if not self.token:
            print("❌ 未配置Token")
            return False
        try:
            resp = requests.post(
                "http://www.pushplus.plus/send",
                json={"token": self.token, "title": title, "content": content, "template": "markdown"},
                timeout=15
            )
            r = resp.json()
            if r.get('code') == 200:
                print("✅ 推送成功")
                return True
            print(f"❌ 推送失败: {r.get('msg')}")
        except Exception as e:
            print(f"❌ 推送异常: {e}")
        return False


def main():
    print("=" * 50)
    print(f"📺 新闻联播 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    crawler = XinwenLianbo()
    news = crawler.get_latest_news()

    if not news:
        print("❌ 获取失败")
        return

    content = news['content'][:3500] if len(news['content']) > 3500 else news['content']

    md = f"""# 📺 {news['title']}

**日期**: {news['date']}

{content}

---
> 链接: {news['url']}"""

    print(f"\n✅ 获取成功: {news['title']}")
    print(f"📅 日期: {news['date']}")
    print(f"📄 内容长度: {len(news['content'])}字\n")

    token = os.environ.get('PUSHPLUS_TOKEN')
    if token:
        print("📤 推送中...")
        PushPlus(token).push(f"📺 新闻联播 {news['date']}", md)
    else:
        print("⚠️ 未配置Token")

    # 保存
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f'xinwen_lianbo_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(f"📺 {news['title']}\n\n📅 {news['date']}\n\n{content}\n\n🔗 {news['url']}")
    print(f"💾 已保存")


if __name__ == "__main__":
    main()