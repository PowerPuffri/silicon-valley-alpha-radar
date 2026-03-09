# SV Alpha Radar - 快速开始

## 一、手动运行

```bash
# 收集数据并推送
python scheduler.py

# 仅收集数据
python scheduler.py --collect

# 后台持续运行（每6小时收集一次）
python scheduler.py --daemon
```

## 二、当前状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 多数据源收集 | ✅ | OpenAI + Anthropic + DeepMind |
| 标题优化 | ✅ | 智能提取真实标题 |
| 链接过滤 | ✅ | 排除导航/页脚链接 |
| 去重 | ✅ | 自动删除重复文章 |
| Telegram 推送 | ✅ | 简化格式，避免 400 错误 |
| 定时任务 | ✅ | scheduler.py --daemon |

## 三、数据源

| 来源 | 类型 | 优先级 |
|------|------|--------|
| OpenAI Blog | 博客 | 100 |
| Anthropic Research | 博客 | 100 |
| DeepMind Discover | 博客 | 100 |

## 四、数据库位置

```
storage/data/collected_articles.db
```

## 五、配置文件

```json
// config/config.json
{
  "telegram": {
    "botToken": "YOUR_BOT_TOKEN",
    "chatId": "YOUR_CHAT_ID"
  }
}
```

## 六、常用命令

```bash
# 查看数据库内容
sqlite3 storage/data/collected_articles.db "SELECT title, source FROM articles ORDER BY collected_at DESC LIMIT 10"

# 手动推送测试
python -c "
import sqlite3
import requests
import json
from datetime import datetime

with open('config/config.json') as f:
    config = json.load(f)
    bot_token = config['telegram']['botToken']
    chat_id = config['telegram']['chatId']

conn = sqlite3.connect('storage/data/collected_articles.db')
cursor = conn.cursor()
cursor.execute('SELECT title, url, source FROM articles WHERE title NOT LIKE \"%\#%\" ORDER BY priority DESC LIMIT 8')
articles = cursor.fetchall()
conn.close()

lines = [f'🚨 SV Alpha Radar | {datetime.now().strftime(\"%Y-%m-%d\")}', '', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━', '⚡ NEW UPDATES', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━', '']
icons = {'openai_blog': '🟢', 'anthropic_blog': '🟣', 'deepmind_blog': '🔵'}
for title, url, source in articles:
    icon = icons.get(source, '📄')
    lines.append(f'{icon} {title.split(\"|\")[0].strip()[:40]}')
    lines.append(f'   {url}')
    lines.append('')

lines.append(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
lines.append(f'🕐 {datetime.now().strftime(\"%H:%M\")}')

requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id': chat_id, 'text': '\\n'.join(lines), 'disable_web_page_preview': True})
print('Done!')
"
```
