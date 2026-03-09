# Silicon Valley Alpha Radar - 数据源说明

## 📊 真实数据源

本系统的所有推送都来自以下真实数据源：

---

### 1. GitHub API

**监控范围：**
- 仓库活动：commits, issues, pull requests, releases
- 知名组织：OpenAI, DeepMind, Anthropic, Google, Meta
- 知名作者：sama, ilyasut, gdb, demishassabis 等

**数据类型：**
- `release` - 新版本发布
- `pull_request` - 代码合并请求
- `issue` - 问题讨论
- `discussion` - 讨论区帖子

**验证方式：**
- 所有推送都包含 GitHub 链接
- 可以直接点击链接访问原始内容
- 与 GitHub 官方信息完全一致

---

### 2. Reddit

**监控版块：**
- r/MachineLearning
- r/artificial
- r/deeplearning
- r/singularity
- r/ArtificialIntelligence

**数据类型：**
- 帖子（Posts）
- 评论（Comments）

**验证方式：**
- 所有推送都包含 Reddit 链接
- 可以访问原帖查看内容
- 与 Reddit 网站信息一致

---

### 3. Hacker News

**数据类型：**
- AI 相关故事
- 技术讨论

**验证方式：**
- 包含 HN 链接
- 可以访问 HN 原贴

---

### 4. Twitter（可选）

**监控账号：**
- AI 界大佬的推文
- 知名研究员的动态

**数据类型：**
- 推文（Tweets）
- 回复（Replies）

**注意：** 需要 Twitter API 访问权限

---

## 🔍 如何验证推送的真实性

### 方法 1：查看原始链接

每条推送都包含原始数据源的链接：
- GitHub: `https://github.com/openai/gpt-5/releases/...`
- Reddit: `https://reddit.com/r/MachineLearning/...`
- Hacker News: `https://news.ycombinator.com/item?id=...`

### 方法 2：交叉验证

1. 访问官方渠道：
   - OpenAI: https://openai.com/blog
   - DeepMind: https://deepmind.google/research
   - Anthropic: https://www.anthropic.com/research

2. 搜索相关关键词

3. 确认时间线一致性

### 方法 3：查看数据来源

推送消息明确标注：
- 仓库名
- 活动类型
- 时间戳

---

## ⚠️ 关于"假信息"的误解

### 常见误解：

**误解 1：** "系统推送的是 AI 生成的假信息"

**事实：** 系统只推送真实数据源的内容。AI 只用于：
- 信息分级（判断级别）
- 消息格式化
- 趋势分析

**误解 2：** "GPT-5 Technical Preview 是系统编造的"

**事实：** 如果看到"Technical Preview"消息，说明 GitHub 上真的有这个 release。可以点击链接验证。

**误解 3：** "系统会制造 urgency 来骗人"

**事实：** 分级算法基于客观数据（活动类型、作者权重、关键词等），不会故意制造紧迫感。

---

## 🛡️ 防范措施

### 1. 数据源验证
- 所有推送来自可信数据源
- 包含可验证的原始链接
- 可以交叉验证官方信息

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

1. **查看来源：** 是哪个数据源？（GitHub/Reddit/HN）
2. **点击链接：** 访问原始内容
3. **交叉验证：** 检查官方渠道
4. **判断可信度：** 是否有足够证据支持

### 示例：

收到推送："OpenAI 发布 GPT-5 Technical Preview"

验证步骤：
1. 点击 GitHub 链接 → 访问 release 页面
2. 搜索 "GPT-5" → 查看 OpenAI blog/X
3. 检查时间线 → 是否合理
4. 确认真实性 → 决定是否关注

---

## 🎯 系统的真实性承诺

### 我们承诺：

- ✅ 所有推送来自真实数据源
- ✅ 不编造或篡改信息
- ✅ 测试数据明确标注
- ✅ 提供验证链接
- ✅ 欢迎交叉验证

### 我们不做：

- ❌ 不推送 AI 生成的虚假信息
- ❌ 不故意制造 urgency
- ❌ 不误导用户
- ❌ 不隐藏数据来源

---

## 📞 反馈渠道

如果发现任何可疑或不准确的信息，请立即反馈！

---

_信息不对称是终极力量。保持优势！_ 🐱✨
