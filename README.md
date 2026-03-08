# 🎯 Silicon Valley Alpha Radar

监控 AI 界顶级大佬的"隐性共识"和潜在趋势，发现信息不对称优势。

---

## 📋 项目介绍

这是一个自动化监控系统，用于追踪 OpenAI、DeepMind 和 Anthropic 等顶级 AI 公司关键人物的社交媒体动态和代码活动，识别低关注度的内行讨论和早期趋势信号。

### 🎯 核心目标

1. **数据收集**：监控大佬们的 X (Twitter) 推文和 GitHub 仓库活动
2. **趋势分析**：检测"隐性共识" - 多人私下讨论但公开关注度低的话题
3. **报告生成**：生成每日趋势报告，包含关键信号和洞察
4. **可视化**：展示趋势热度图、参与者网络图

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd silicon-valley-alpha-radar
pip install -r requirements.txt
```

### 2. 配置 API 密钥

#### Twitter API
- 获取 Twitter API Key, Secret 和 Bearer Token
- 设置环境变量：
  ```bash
  export TWITTER_API_KEY="your_api_key"
  export TWITTER_API_SECRET="your_api_secret"
  export TWITTER_BEARER_TOKEN="your_bearer_token"
  ```

#### GitHub API
- 获取 GitHub Personal Access Token
- 设置环境变量：
  ```bash
  export GITHUB_TOKEN="your_github_token"
  ```

### 3. 运行数据收集

```bash
# 收集所有数据源（Twitter + GitHub）
python orchestrator.py --days 7

# 只收集 Twitter 数据
python orchestrator.py --days 7 --twitter-only

# 只收集 GitHub 数据
python orchestrator.py --days 7 --github-only

# 查看最近统计
python orchestrator.py --stats
```

---

## 📁 项目结构

```
silicon-valley-alpha-radar/
├── src/
│   ├── collectors/          # 数据收集器
│   │   ├── twitter_collector.py  # Twitter 推文收集
│   │   └── github_monitor.py     # GitHub 仓库监控
│   ├── analyzers/            # 分析引擎（开发中）
│   │   ├── trend_detector.py      # 趋势检测
│   │   ├── semantic_analyzer.py    # 语义分析
│   │   └── consensus_finder.py     # 共识检测
│   ├── generators/           # 报告生成器（开发中）
│   │   ├── report_generator.py    # 报告生成
│   │   └── ui_visualizer.py       # UI 可视化
│   └── orchestrator.py       # 数据编排器
├── storage/                 # 数据存储
│   ├── data/                # 原始数据
│   └── processed/            # 处理后的数据
├── config/                  # 配置文件
│   └── config.json          # 监控配置
├── output/                  # 输出报告
│   └── reports/             # 生成的报告
├── requirements.txt         # Python 依赖
├── orchestrator.py         # 主程序
└── README.md                # 项目说明
```

---

## ⚙️ 配置说明

### config.json

```json
{
  "monitored_accounts": {
    "openai": {
      "name": "OpenAI",
      "handles": ["sama", "ilyasut", "gdb"],
      "github_repos": ["openai/gpt-4", "openai/whisper"]
    },
    "deepmind": {
      "name": "DeepMind",
      "handles": ["demishassabis", "mustafasuleyman"],
      "github_repos": ["deepmind/deepmind-research"]
    },
    "anthropic": {
      "name": "Anthropic",
      "github_repos": ["anthropic/anthropic"]
    }
  },
  "keywords": [
    "AI", "neural", "attention", "bio-compute",
    "spiking", "architecture", "AGI"
  ],
  "trend_detection": {
    "min_participants": 2,
    "max_public_likes": 100,
    "time_window_days": 7
  }
}
```

---

## 🔧 功能模块

### 1. Twitter Collector (✅ 已完成)
- 监控指定 Twitter 账号的推文
- 关键词过滤
- 低关注度检测（likes < 100）
- SQLite 数据存储

### 2. GitHub Monitor (✅ 已完成)
- 监控指定 GitHub 仓库的活动
- 追踪 commits, issues, pull requests
- 仓库统计信息收集
- SQLite 数据存储

### 3. Semantic Analyzer (🚧 开发中)
- 使用 OpenAI Embeddings 进行语义分析
- 向量化和相似度计算
- 话题聚类分析

### 4. Report Generator (🚧 开发中)
- Markdown 格式报告生成
- 趋势总结和关键信号
- 信息不对称洞察

---

## 📊 数据流

```
00:00 UTC 定时任务触发
    ↓
[数据收集阶段]
    ├── Twitter Collector → 收集 7 天内推文
    └── GitHub Monitor → 监控仓库活动
    ↓
[数据存储阶段]
    └── 存储到 SQLite 数据库
    ↓
[分析阶段 - 开发中]
    ├── Semantic Analyzer → 语义聚类
    └── Trend Detector → 检测隐性趋势
    ↓
[报告生成阶段 - 开发中]
    └── Report Generator → 生成 Markdown 报告
    ↓
[输出阶段]
    └── 保存报告到 output/reports/
```

---

## 🔑 核心概念

### 隐性共识 (Hidden Consensus)

定义：多个大佬私下讨论的话题或技术方向，但公开关注度低。

**特征：**
- 参与人数 >= 2
- 公开关注度低（likes < 100）
- 讨论深度高（Issue 评论数、代码提交活跃）

### 信息不对称 (Information Asymmetry)

定义：内行人员掌握的信息，普通开发者通过公开渠道无法获取。

**价值：**
- 建立早期情报网络
- 超越纯代码工作的优势
- 发现未被广泛注意的技术趋势

---

## 🎯 实施计划

### Phase 1: MVP (✅ 完成)
- ✅ Twitter 数据收集
- ✅ GitHub 仓库监控
- ✅ 基础数据存储
- ✅ 数据编排器

### Phase 2: 核心功能 (🚧 进行中)
- 🔄 语义分析引擎
- 🔄 趋势检测算法
- 🔄 共识检测器

### Phase 3: 高级功能 (📋 规划中)
- 📋 自动定时任务
- 📋 报告生成器
- 📋 UI 可视化

### Phase 4: 优化和扩展 (📋 规划中)
- 📋 Web Dashboard
- 📋 邮件/Webhook 通知
- 📋 添加更多监控目标

---

## 📈 使用示例

### 基础数据收集

```bash
# 收集最近 7 天的数据
python orchestrator.py --days 7
```

### 查看统计信息

```bash
# 显示最近 24 小时的统计
python orchestrator.py --stats
```

### 单独收集 Twitter 数据

```bash
python orchestrator.py --days 7 --twitter-only
```

---

## ⚠️ 注意事项

1. **API 限制**：Twitter 和 GitHub API 都有速率限制，需要合理设置
2. **隐私合规**：只公开可获取的数据，不涉及个人隐私
3. **数据准确性**：隐性共识检测算法需要持续优化
4. **网络依赖**：需要稳定的网络连接来访问 API

---

## 🚧 待办事项

- [ ] 实现语义分析引擎（OpenAI Embeddings）
- [ ] 实现趋势检测算法（DBSCAN 聚类）
- [ ] 实现报告生成器（Markdown 模板）
- [ ] 实现 UI 可视化（趋势图、网络图）
- [ ] 实现定时任务调度（00:00 UTC）
- [ ] 添加邮件/Webhook 通知
- [ ] 创建 Web Dashboard
- [ ] 优化隐性共识检测算法
- [ ] 添加更多监控目标和关键词

---

## 📞 联系

如需帮助或有问题，请通过 WhatsApp 联系。

---

_**💡 信息不对称是终极力量。超级开发者通过建立信息网络而不是只写代码来获得优势。**_
