#!/usr/bin/env python3
"""
简单的 Telegram 测试 - 纯文本
"""

import requests
import json

# 读取配置
with open("config/config.json", 'r', encoding='utf-8') as f:
    config = json.load(f)
    bot_token = config.get('telegram', {}).get('botToken', '')
    chat_id = config.get('telegram', {}).get('chatId', '')

print(f"Bot Token: {bot_token[:10]}...")
print(f"Chat ID: {chat_id}")

# 1. 先测试纯文本
print("\n[测试1] 发送纯文本...")
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    'chat_id': chat_id,
    'text': '🚀 SV Alpha Radar 测试消息\n\n这是一条纯文本测试消息。',
}

response = requests.post(url, json=payload, timeout=30)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:200]}")

if response.status_code == 200:
    print("✅ 纯文本发送成功！")

    # 2. 测试简单 HTML
    print("\n[测试2] 发送简单 HTML...")
    payload = {
        'chat_id': chat_id,
        'text': '<b>🚀 SV Alpha Radar</b>\n\n<i>测试 HTML 格式</i>',
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=payload, timeout=30)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        print("✅ HTML 发送成功！")
    else:
        print(f"❌ HTML 失败: {response.text[:200]}")
else:
    print(f"❌ 纯文本失败: {response.text[:200]}")
