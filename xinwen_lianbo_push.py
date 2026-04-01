#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播内容获取脚本 - PushPlus推送版
使用稳定的数据源获取新闻联播内容
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
        # 优先使用央视网API
        print("📡 尝试央视网API...")
        result = self._fetch_cctv_api()
        if result:
            return result

        # 备用：直接抓取新闻联播页面
        print("📡 尝试央视网页面...")
        result = self._fetch_cctv_page()
        if result:
            return result

        # 最后备用：RSSHub
        print("📡 尝试RSSHub...")
        result = self._fetch_rsshub()
        if result:
            return result

        return None

    def _fetch_cctv_api(self):
        """央视网新闻联播API - 最稳定的数据源"""
        try:
            url = "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_4.json"
            resp = self.session.get(url, timeout=15)
            data = resp.json()

            if data.get('data', {}).get('list'):
                items = data['data']['list']
                for item in items[:1]:  # 只取最新一条
                    title = item.get('title', '')
                    url = item.get('url', '')

                    # 获取详情页内容
                    if url:
                        detail = self._fetch_detail(url)
                        if detail:
                            return detail

                    # 没有详情页则用摘要
                    return {
                        'title': title or '新闻联播',
                        'date': item.get('datetime', datetime.now().strftime('%Y-%m-%d')),
                        'content': item.get('brief', '点击链接查看详情'),
                        'url': url or 'https://cctv.cctv.com/lm/xwlb/'
                    }
        except Exception as e:
            print(f"API失败: {e}")
        return None

    def _fetch_cctv_page(self):
        """直接抓取央视网页面"""
        try:
            url = "https://news.cctv.com/world/"
            resp = self.session.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 查找新闻联播相关链接
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if '新闻联播' in text or 'xwlb' in href:
                    return self._fetch_detail(href)
        except Exception as e:
            print(f"页面失败: {e}")
        return None

    def _fetch_rsshub(self):
        """RSSHub备用源"""
        try:
            url = "https://rsshub.app/cctv/xwlb"
            resp = self.session.get(url, timeout=20)
            soup = BeautifulSoup(resp.text, 'xml')

            items = soup.find_all('item')
            if items:
                first = items[0]
                title = first.find('title')
                desc = first.find('description')
                link = first.find('link')

                return {
                    'title': title.get_text() if title else '新闻联播',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'content': desc.get_text() if desc else '点击链接查看详情',
                    'url': link.get_text() if link else 'https://cctv.cctv.com/lm/xwlb/'
                }
        except Exception as e:
            print(f"RSS失败: {e}")
        return None

    def _fetch_detail(self, url):
        """获取详情页完整内容"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 标题
            title = ''
            for selector in ['h1', '.title', '.phd_title', 'h2']:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    if title:
                        break

            # 日期
            date = datetime.now().strftime('%Y-%m-%d')
            for selector in ['.date', '.time', '.info_time']:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    match = re.search(r'\d{4}[-年]\d{1,2}[-月]\d{1,2}', text)
                    if match:
                        date = match.group().replace('年', '-').replace('月', '-').rstrip('日')
                        break

            # 正文
            content = ''
            for selector in ['.content', '.article-content', '#content_area', '#article', '.text', '.page-content']:
                div = soup.select_one(selector)
                if div:
                    paragraphs = div.find_all('p')
                    texts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 5:
                            texts.append(text)
                    content = '\n\n'.join(texts)
                    if content:
                        break

            # 如果没找到，尝试获取所有段落
            if not content:
                all_p = soup.find_all('p')
                texts = []
                for p in all_p:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20 and '版权' not in text:
                        texts.append(text)
                content = '\n\n'.join(texts[:20])

            return {
                'title': title or '新闻联播',
                'date': date,
                'content': content or '点击链接查看完整内容',
                'url': url
            }
        except Exception as e:
            print(f"详情页失败: {e}")
        return None


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
                print("✅ PushPlus推送成功！")
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
    if len(content) > 3500:
        content = content[:3500] + '\n\n...(内容过长，已截断)'

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

    print("\n📋 获取成功！")
    print(formatted[:500] + "...\n")

    # 推送
    token = os.environ.get('PUSHPLUS_TOKEN')

    if token:
        print("📤 正在推送...")
        pusher = PushPlus(token)
        pusher.push(
            title=f"📺 新闻联播 {result['date']}",
            content=markdown,
            template='markdown'
        )
    else:
        print("⚠️ 未配置 PUSHPLUS_TOKEN")

    # 保存
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f'xinwen_lianbo_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(formatted)
    print(f"💾 已保存: xinwen_lianbo_{today}.txt")

    print("\n✅ 完成!")


if __name__ == "__main__":
    main()