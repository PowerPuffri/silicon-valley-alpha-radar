# Silicon Valley Alpha Radar - 快速参考

## 📊 当前真实数据源（3个）

### ✅ 1. Reddit
- **状态：** ⚠️ 未初始化
- **收集器：** `src/collectors/reddit_collector.py`
- **数据库：** `storage/data/reddit_posts.db`
- **监控：** r/MachineLearning, r/artificial, r/deeplearning, r/singularity, r/ArtificialIntelligence

### ✅ 2. Hacker News
- **状态：** ⚠️ 已初始化但空（0 条）
- **收集器：** `src/collectors/hackernews_collector.py`
- **数据库：** `storage/data/hacker_news.db`
- **表名：** `hacker_news`

### ✅ 3. Twitter (Jina API)
- **状态：** ✅ 有数据（2 条）
- **收集器：** `src/collectors/jina_twitter_collector.py`
- **数据库：** `storage/data/twitter_posts_jina.db`
- **优点：** 无需 Token，免费使用

---

## ❌ 已移除的数据源

### GitHub（已完全移除）
- ❌ `src/collectors/github_monitor.py` - 已删除
- ❌ `storage/data/github_activity.db` - 已删除
- ❌ 所有 GitHub 相关代码 - 已清理

---

## 🚀 快速命令

### 测试推送
```bash
python test_complete_push_v2.py
```

### 运行推送服务
```bash
# 测试模式
python src/services/unified_push_service.py --test --days 7

# 持续监控
python src/services/unified_push_service.py --start --interval 30

# 查看状态
python src/services/unified_push_service.py --status
```

### 收集数据
```bash
# Reddit
python -c "from src.collectors.reddit_collector import RedditCollector; RedditCollector('config/config.json').collect_all_subreddits(days=7)"

# Hacker News
python -c "from src.collectors.hackernews_collector import HackerNewsCollector; HackerNewsCollector('config/config.json').collect_all_stories(days=7)"

# Twitter
python -c "from src.collectors.jina_twitter_collector import JinaTwitterCollector; JinaTwitterCollector('config/config.json').collect_all_accounts(days=7)"
```

---

## 📱 推送配置

- **默认渠道：** Telegram ✅
- **备用渠道：** WhatsApp
- **推送策略：**
  - 🔴 重磅：立即推送
  - 🟠 重要：每小时
  - 🟡 普通：每3小时

---

## 📁 重要文件

```
silicon-valley-alpha-radar/
├── src/collectors/
│   ├── reddit_collector.py          ✅ Reddit
│   ├── hackernews_collector.py      ✅ Hacker News
│   └── jina_twitter_collector.py   ✅ Twitter (Jina)
├── src/services/
│   └── unified_push_service.py     推送服务
├── config/
│   ├── config.json                  主配置
│   └── push_config.json             推送配置
├── storage/data/
│   ├── reddit_posts.db             Reddit 数据库
│   ├── hacker_news.db              Hacker News 数据库
│   └── twitter_posts_jina.db       Twitter 数据库
└── test_complete_push_v2.py        推送测试
```

---

## 🎯 总结

- ✅ GitHub 已完全移除
- ✅ 推送服务正常运行
- ✅ 3个真实数据源：Reddit, Hacker News, Twitter
- ⚠️ 需要收集 Reddit 和 Hacker News 数据

---

_信息不对称是终极力量。保持优势！_ 🐱✨
