# 🚀 Silicon Valley Alpha Radar - 快速执行流程

## 📍 项目位置
```
/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar/
```

---

## 📦 一、安装依赖
```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar/
pip install -r requirements.txt
```

---

## 🔑 二、配置 API（必需！）

### 1. Twitter API
去 https://developer.twitter.com/ 申请，获得三个密钥：
```bash
export TWITTER_API_KEY="你的密钥"
export TWITTER_API_SECRET="你的密钥"
export TWITTER_BEARER_TOKEN="你的令牌"
```

### 2. GitHub API
去 GitHub → Settings → Developer settings → Personal access tokens → Generate new token：
```bash
export GITHUB_TOKEN="你的token"
```

---

## ▶️ 三、运行流程

### 步骤 1：测试连接
```bash
python orchestrator.py --stats
```
应该看到：最近 24 小时统计信息（第一次会是 0）

### 步骤 2：收集数据（7 天）
```bash
python orchestrator.py --days 7
```
会自动：
- 收集 Twitter 推文
- 收集 GitHub 活动
- 保存到数据库

### 步骤 3：查看结果
```bash
sqlite3 storage/data/twitter_posts.db "SELECT COUNT(*) FROM twitter_posts;"
sqlite3 storage/data/github_activity.db "SELECT COUNT(*) FROM github_activity;"
```

---

## ⚠️ 常见问题

### 问题 1：API 认证失败
**解决**：检查 API 密钥是否正确

### 问题 2：没有数据
**解决**：确认大佬们最近 7 天有发推或代码活动

### 问题 3：依赖安装失败
**解决**：使用 `pip install --upgrade pip` 升级后重试

---

## 📊 下一步

收集到数据后，我会实现：
1. 语义分析（发现话题）
2. 趋势检测（识别隐性共识）
3. 报告生成（Markdown 报告）

---

## 🎯 核心价值

> **"信息不对称是终极力量。超级开发者通过建立信息网络而不是只写代码来获得优势。"**

现在就收集数据，建立信息网络！

---

**有问题随时通过 WhatsApp 联系我！** 🐱✨
