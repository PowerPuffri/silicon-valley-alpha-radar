# Silicon Valley Alpha Radar - 数据源说明（无 GitHub）

## 📊 真实数据源

本系统的所有推送都来自以下真实数据源：

---

### 1. Reddit

**监控版块：**
- r/MachineLearning
- r/artificial
- r/deeplearning
- r/singularity
- r/ArtificialIntelligence

**数据类型：**
- 帖子（Posts）
- 评论（Comments）

**数据库：** `storage/data/reddit_posts.db`

**验证方式：**
- 所有推送都包含 Reddit 链接
- 可以访问原帖查看内容
- 与 Reddit 网站信息一致

---

### 2. Hacker News

**数据类型：**
- AI 相关故事
- 技术讨论

**数据库：** `storage/data/hacker_news.db`

**验证方式：**
- 包含 HN 链接
- 可以访问 HN 原贴

---

### 3. Twitter

**数据类型：**
- 推文（Tweets）
- 回复（Replies）

**数据库：** `storage/data/twitter_posts_jina.db`

**注意：** 使用 Jina API 爬取 Twitter，无需 Twitter API Token

---

## ❌ 已移除的数据源

### GitHub（已移除）

**原因：** 根据 2026-03-09 的决定，移除 GitHub 数据源。

**已删除文件：**
- `src/collectors/github_monitor.py` - GitHub 监控器
- `test_github.py` - GitHub 测试脚本
- `quick_collect.py` - GitHub 快速收集脚本

**已删除数据库：**
- `storage/data/github_activity.db`

**原因说明：**
- 避免误导性测试数据
- 专注于社交媒体和社区讨论
- 降低信息噪音

---

## 🔍 如何验证推送的真实性

### 方法 1：查看原始链接

每条推送都包含原始数据源的链接：
- Reddit: `https://reddit.com/r/MachineLearning/...`
- Hacker News: `https://news.ycombinator.com/item?id=...`
- Twitter: `https://twitter.com/user/status/...`

### 方法 2：交叉验证

1. 访问原版块/网站：
   - Reddit: https://reddit.com/r/MachineLearning
   - Hacker News: https://news.ycombinator.com
   - Twitter: https://twitter.com

2. 搜索相关关键词

3. 确认时间线一致性

### 方法 3：查看数据来源

推送消息明确标注：
- 来源：Reddit/Hacker News/Twitter
- 作者/用户名
- 时间戳

---

## 📊 数据收集流程

```
Reddit API
    ↓
reddit_posts.db
    ↓

Hacker News API
    ↓
hacker_news.db
    ↓

Jina Twitter API
    ↓
twitter_posts_jina.db
    ↓

信息判断层（分级）
    ↓
推送队列
    ↓
Telegram 推送
```

---

## 🎯 系统优势

### 1. 社区驱动
- Reddit 和 Hacker News 是 AI 界最活跃的社区
- 能够发现讨论热点和趋势
- 避免官方渠道的信息过滤

### 2. 多角度信息
- 从社交媒体获取实时动态
- 从技术社区获取深度讨论
- 综合多个渠道，避免信息偏差

### 3. 低门槛
- 不需要 GitHub Token
- Reddit 和 Hacker News API 免费
- Jina Twitter API 无需认证

---

## 🛡️ 防范措施

### 1. 数据源验证
- 所有推送来自可信社区平台
- 包含可验证的原始链接
- 可以交叉验证官方渠道信息

### 2. 透明度
- 明确标注数据来源
- 显示原始链接和时间戳
- 文档说明工作原理

### 3. 测试隔离
- 测试数据明显虚构
- 测试消息包含免责声明
- 测试和生产环境分离

---

## 📚 推荐验证流程

### 收到推送后：

1. **查看来源：** 哪个数据源？（Reddit/HN/Twitter）

2. **点击链接：** 访问原始内容

3. **交叉验证：** 检查其他渠道

4. **判断可信度：** 是否有足够证据支持

### 示例：

收到推送："Reddit 讨论新的 LLM 优化技术"

验证步骤：
1. 点击 Reddit 链接 → 访问原帖
2. 搜索相关关键词 → 查看 HN 是否有类似讨论
3. 检查时间线 → 是否合理
4. 确认真实性 → 决定是否关注

---

## 🔧 如何添加新数据源

### 步骤 1：创建收集器

```python
# src/collectors/new_collector.py

class NewCollector:
    def collect(self, days: int = 7) -> List[Dict]:
        # 收集数据
        pass

    def save_to_db(self, activities: List[Dict]):
        # 保存到数据库
        pass
```

### 步骤 2：集成到服务

```python
# src/services/unified_push_service.py

def collect_and_judge(self, days: int = 1) -> List[Dict]:
    # 从新数据源收集
    new_activities = self._collect_from_database(
        'storage/data/new_source.db',
        'new_table',
        days
    )
    all_activities.extend(new_activities)
```

### 步骤 3：更新文档

更新 `DATA_SOURCES_V2.md`，添加新数据源的说明。

---

## 📞 反馈渠道

如果发现任何可疑或不准确的信息，或建议添加新数据源，请立即反馈！

---

_信息不对称是终极力量。保持优势！_ 🐱✨
