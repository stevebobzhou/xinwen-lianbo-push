# 新闻联播每日推送

通过 GitHub Actions 自动获取央视《新闻联播》文字版内容，并推送到微信。

## 🚀 快速部署（3步完成）

### 第1步：Fork 本仓库

点击右上角 **Fork** 按钮，将仓库复制到你的账号下。

### 第2步：获取 PushPlus Token

1. 微信扫码关注公众号「**PushPlus推送加**」
2. 关注后，在公众号菜单点击「功能」→「Token」获取 Token
3. 复制你的 Token

### 第3步：配置 Secret

1. 进入你 Fork 的仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 名称填：`PUSHPLUS_TOKEN`
5. 值填：你刚才复制的 Token
6. 点击 **Add secret** 保存

## ✅ 完成！

- 每天 **北京时间 20:00** 自动推送新闻联播到你的微信
- 也可以手动运行：**Actions** → **新闻联播每日推送** → **Run workflow** → **Run workflow**

## 📋 推送效果

```
📺 新闻联播

📅 2024-01-20

━━━━━━━━━━━━━

1. 习近平同美国总统拜登通电话...

2. 李强主持召开国务院常务会议...

...

━━━━━━━━━━━━━

🔗 https://news.cctv.com/...
```

## 🔧 自定义配置

### 修改推送时间

编辑 `.github/workflows/xinwen_lianbo.yml`：

```yaml
schedule:
  - cron: '0 12 * * *'  # UTC时间，北京时间 = UTC + 8
```

| 北京时间 | UTC时间 |
|---------|--------|
| 20:00 | 12:00 |
| 21:00 | 13:00 |
| 08:00 | 00:00 |

### 关闭自动运行

在仓库 Settings → Actions → General 中禁用 Actions。

## ❓ 常见问题

**Q: 没收到推送？**
- 检查 Secret 是否正确配置
- 查看公众号是否被屏蔽
- 查看 Actions 运行日志

**Q: 获取失败？**
- 可能央视网暂时不可访问
- 查看日志确认错误原因

**Q: 如何取消关注？**
- 微信取消关注公众号即可

## 📄 文件说明

| 文件 | 说明 |
|-----|------|
| `xinwen_lianbo_push.py` | 主脚本 |
| `.github/workflows/xinwen_lianbo.yml` | 定时任务配置 |

## 📝 注意事项

- 免费版 PushPlus 每天限制 200 条消息
- 请勿频繁请求，以免被央视网限制
- 仅供学习交流使用
