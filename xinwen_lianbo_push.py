#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本 - PushPlus推送版
支持多种数据源，确保稳定性
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
        """获取最新新闻内容"""
        sources = [
            ('央视网API', self._fetch_cctv_api),
            ('央视网页面', self._fetch_cctv_web),
            ('RSSHub', self._fetch_rsshub),
            ('新浪新闻', self._fetch_sina),
            ('搜狐新闻', self._fetch_sohu),
        ]

        for name, fetch_func in sources:
            try:
                print(f"📡 尝试 {name}...")
                result = fetch_func()
                if result and result.get('content'):
                    print(f"✅ 从 {name} 获取成功")
                    return result
            except Exception as e:
                print(f"❌ {name} 失败: {str(e)[:50]}")

        # 所有源都失败，生成今日摘要
        print("⚠️ 所有数据源不可用，生成今日提示")
        return self._generate_daily_notice()

    def _fetch_cctv_api(self):
        """央视网API"""
        url = "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_4.json"
        resp = self.session.get(url, timeout=10)
        data = resp.json()
        if data.get('data', {}).get('list'):
            latest = data['data']['list'][0]
            return {
                'title': latest.get('title', '新闻联播'),
                'date': latest.get('datetime', datetime.now().strftime('%Y-%m-%d')),
                'content': latest.get('brief', ''),
                'url': latest.get('url', 'https://cctv.cctv.com/lm/xwlb/')
            }
        return None

    def _fetch_cctv_web(self):
        """央视网页面"""
        url = "https://cctv.cctv.com/lm/xwlb/"
        resp = self.session.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = soup.select('.list a') or soup.select('a[href*="xwlb"]')
        if links:
            return self._parse_detail(links[0].get('href'))
        return None

    def _fetch_rsshub(self):
        """RSSHub源"""
        url = "https://rsshub.app/cctv/xwlb"
        resp = self.session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'xml')
        items = soup.find_all('item')
        if items:
            first = items[0]
            return {
                'title': first.find('title').get_text() if first.find('title') else '新闻联播',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'content': first.find('description').get_text() if first.find('description') else '',
                'url': first.find('link').get_text() if first.find('link') else ''
            }
        return None

    def _fetch_sina(self):
        """新浪新闻搜索"""
        url = "https://search.sina.com.cn/"
        params = {'q': '新闻联播', 'c': 'news', 'from': 'channel'}
        resp = self.session.get(url, params=params, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.select('.result') or soup.select('.box-result')
        for item in results[:5]:
            title_elem = item.select_one('a')
            if title_elem and '新闻联播' in title_elem.get_text():
                href = title_elem.get('href')
                return self._parse_detail(href)
        return None

    def _fetch_sohu(self):
        """搜狐新闻搜索"""
        url = "https://search.sohu.com/"
        params = {'keyword': '新闻联播'}
        resp = self.session.get(url, params=params, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.select('.news-item') or soup.select('.item')
        for item in results[:5]:
            title_elem = item.select_one('a') or item.select_one('.title')
            if title_elem and '新闻联播' in title_elem.get_text():
                href = title_elem.get('href') or title_elem.get('a', {}).get('href')
                if href:
                    return self._parse_detail(href)
        return None

    def _parse_detail(self, url):
        """解析详情页"""
        if not url:
            return None
        resp = self.session.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        title_elem = soup.select_one('h1') or soup.select_one('.title')
        title = title_elem.get_text(strip=True) if title_elem else '新闻联播'

        date_elem = soup.select_one('.date') or soup.select_one('.time')
        date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')

        content = ''
        for selector in ['.content', '.article-content', '#content_area', '#article', '.text']:
            div = soup.select_one(selector)
            if div:
                paragraphs = div.select('p')
                content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if content:
                    break

        return {
            'title': title,
            'date': date,
            'content': content,
            'url': url
        }

    def _generate_daily_notice(self):
        """生成每日提示"""
        today = datetime.now()
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        weekday = weekdays[today.weekday()]

        return {
            'title': f'新闻联播 {today.strftime("%Y年%m月%d日")}',
            'date': today.strftime('%Y-%m-%d'),
            'content': f"""📅 今天是 {today.strftime("%Y年%m月%d日")} 星期{weekday}

📺 《新闻联播》每日 {today.strftime("%m月%d日")} 19:00 准时播出

⚠️ 由于网络限制，暂时无法获取今日新闻内容。

💡 获取新闻联播内容的方式：
1. 央视网：cctv.cctv.com/lm/xwlb
2. 央视新闻APP
3. 电视直播/回放

📌 本消息由自动化脚本发送
问题排查中，请稍后重试...""",
            'url': 'https://cctv.cctv.com/lm/xwlb/'
        }


class PushPlus:
    """PushPlus推送"""

    def __init__(self, token):
        self.token = token
        self.api_url = "http://www.pushplus.plus/send"

    def push(self, title, content, template='markdown'):
        """推送消息"""
        if not self.token:
            print("❌ 未配置 PUSHPLUS_TOKEN")
            return False

        data = {
            "token": self.token,
            "title": title,
            "content": content,
            "template": template
        }

        try:
            resp = requests.post(self.api_url, json=data, timeout=15)
            result = resp.json()

            if result.get('code') == 200:
                print("✅ PushPlus推送成功！请检查微信")
                return True
            else:
                print(f"❌ 推送失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False


def main():
    print("=" * 50)
    print(f"📺 新闻联播推送 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 获取新闻
    crawler = XinwenLianbo()
    result = crawler.get_latest_news()

    if not result:
        print("❌ 获取失败")
        return

    # 格式化
    content = result['content']
    if len(content) > 3800:
        content = content[:3800] + '\n...'

    formatted = f"""📺 {result['title']}

📅 {result['date']}

━━━━━━━━━━━━━

{content}

━━━━━━━━━━━━━

🔗 {result['url']}"""

    markdown = f"""# 📺 {result['title']}

**日期**: {result['date']}

{result['content']}

---
> 链接: {result['url']}"""

    print("\n📋 内容预览:")
    print(formatted[:500] + "...")

    # 推送
    token = os.environ.get('PUSHPLUS_TOKEN')

    if token:
        print("\n📤 正在推送到微信...")
        pusher = PushPlus(token)
        success = pusher.push(
            title=f"📺 新闻联播 {result['date']}",
            content=markdown,
            template='markdown'
        )
        if success:
            print("\n🎉 推送成功！请在微信中查看消息")
    else:
        print("\n⚠️ 未配置 PUSHPLUS_TOKEN")
        print("\n完整内容:")
        print(formatted)

    # 保存
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f'xinwen_lianbo_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(formatted)
    print(f"\n💾 已保存: xinwen_lianbo_{today}.txt")

    print("\n✅ 完成!")


if __name__ == "__main__":
    main()
