# 推送机制使用指南

## 概述

已成功实现信息判断层和分级推送机制！系统会自动判断收集到的信息属于哪个量级，并按照对应的级别进行推送。

---

## 架构组件

### 1. 信息判断层 (`src/judges/info_judge.py`)
负责判断信息的级别，基于以下维度：

**🔴 重磅级 (BREAKING)** - 立即推送
- 活动类型：`release`、`security_advisory`
- 知名作者：sama, ilyasut, gdb, demishassabis 等
- 关键词：breaking, launch, announce, CVE, gpt, agi 等
- 跨公司共识：3+ 公司同时讨论同一技术方向
- 高热度：点赞/评论突增 > 300%

**🟠 一般重要 (IMPORTANT)** - 每小时推送
- 活动类型：`pull_request` (merged)、`discussion`
- 知名仓库：openai/*, deepmind/*, anthropic/*
- 关键词：update, improvement, feature, paper 等

**🟡 普通信息 (NORMAL)** - 每3小时推送
- 活动类型：`issue`, `comment`, `fork`
- 监控范围内的仓库
- 技术关键词

**⚪ 非有效 (IGNORE)** - 不推送
- 不在监控范围内的仓库/账号
- 重复信息（相似度 > 80%）
- 无技术价值的纯讨论

### 2. 推送队列管理 (`src/queues/push_queue_manager.py`)
管理不同级别的推送队列：
- 🔴 `urgent_queue` - 立即推送队列
- 🟠 `hourly_queue` - 每小时推送队列
- 🟡 `normal_queue` - 每3小时推送队列

### 3. 推送格式化器 (`src/formatters/push_formatter.py`)
生成不同格式的推送消息：
- 🔴 重磅格式 - 单条详细格式
- 🟠/🟡 批量格式 - 汇总列表格式

### 4. 统一推送服务 (`src/services/unified_push_service.py`)
整合所有组件，提供完整的推送功能。

---

## 配置文件

### `config/push_config.json`

包含所有推送策略和判断规则：

```json
{
  "push_policy": {
    "breaking": {
      "interval": "immediate",
      "max_per_day": 10,
      "quiet_hours": ["00:00-07:00"]
    },
    "important": {
      "interval": "1h",
      "batch_size": 5
    },
    "normal": {
      "interval": "3h",
      "schedule": ["09:00", "12:00", "15:00", "18:00", "21:00"],
      "batch_size": 10
    }
  },
  "thresholds": {
    "breaking": 5,
    "important": 2,
    "normal": 1
  },
  "keywords": {
    "breaking": [...],
    "important": [...],
    "tech": [...]
  }
}
```

---

## 使用方法

### 1. 测试推送机制

运行完整测试：
```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
source venv/bin/activate
python test_full_push_mechanism.py
```

### 2. 单独测试信息判断层
```bash
python src/judges/info_judge.py
```

### 3. 单独测试格式化器
```bash
python src/formatters/push_formatter.py
```

### 4. 运行统一推送服务

**测试模式（单次运行）：**
```bash
python src/services/unified_push_service.py --test --days 1
```

**持续监控模式：**
```bash
python src/services/unified_push_service.py --start --interval 30
```

**查看队列状态：**
```bash
python src/services/unified_push_service.py --status
```

---

## 推送格式示例

### 🔴 重磅级消息
```
🚨 BREAKING

GPT-5 Technical Preview Released

👤 作者: sama
🏷️ 类型: release
📦 仓库: openai/gpt-5
🎯 关键词: breaking, gpt, agi

🔗 查看详情

💡 判断依据:
   1. 活动类型: release (+4)
   2. 知名作者: sama (+3)
   3. 重磅关键词: breaking (+3)

🕐 检测时间: 2026-03-09 10:00:00
```

### 🟠/🟡 批量消息
```
📊 SV Alpha Radar | 过去1小时

▸ 优化 Transformer 架构
   🏷️ pull_request | 👤 demishassabis | 📦 deepmind/alpha
   💡 监控仓库: deepmind/alpha (+2)
   🔗 链接

📊 总计: 2 条重要信息
🕐 更新时间: 2026-03-09 10:00
```

---

## 推送时机

| 级别 | 推送频率 | 推送时间 |
|------|----------|----------|
| 🔴 重磅级 | 立即 | 检测到即推送（静默时段除外） |
| 🟠 一般重要 | 每1小时 | 整点推送 |
| 🟡 普通信息 | 每3小时 | 09:00, 12:00, 15:00, 18:00, 21:00 |
| ⚪ 非有效 | 不推送 | - |

---

## 集成到现有系统

### 选项 1: 独立运行
直接运行统一推送服务：
```bash
python src/services/unified_push_service.py --start --interval 30
```

### 选项 2: 作为模块导入
```python
from src.services.unified_push_service import UnifiedPushService

# 创建服务实例
service = UnifiedPushService()

# 运行一个周期
service.run_one_cycle(days=1)

# 或启动持续监控
service.start(interval_minutes=30)
```

### 选项 3: 集成到 Orchestrator
修改 `orchestrator.py`，在数据收集后调用推送服务。

---

## WhatsApp 推送

系统支持通过 WhatsApp 发送推送消息（需要 wacli 工具）。

### 安装 wacli
```bash
npm install -g wacli
```

### 配置
设置环境变量：
```bash
export WHATSAPP_TARGET_PHONE="+8619353185819"
```

系统会自动检测 wacli 是否可用，如果不可用则跳过 WhatsApp 推送。

---

## 数据库

### GitHub 活动数据库
- 路径：`storage/data/github_activity.db`
- 存储：GitHub 活动数据

### 推送队列数据库
- 路径：`storage/data/push_queue.db`
- 存储：推送队列和统计信息

---

## 注意事项

1. **静默时段**：重磅级推送在 00:00-07:00 时段会自动暂停
2. **每日上限**：重磅级推送每天最多 10 条
3. **批量大小**：重要信息每次最多推送 5 条，普通信息每次最多 10 条
4. **去重**：相似度 > 80% 的信息会被自动过滤

---

## 故障排查

### 问题：没有数据收集
- 检查 GitHub Token 是否设置
- 确认网络连接正常

### 问题：推送未发送
- 检查 WhatsApp 是否配置
- 确认目标手机号正确

### 问题：判断级别不准确
- 调整 `config/push_config.json` 中的权重和阈值
- 添加或修改关键词列表

---

## 后续优化建议

1. **机器学习优化**：使用历史数据训练模型，提高判断准确性
2. **自适应阈值**：根据历史数据动态调整阈值
3. **用户反馈**：允许用户标记推送级别，持续优化
4. **多渠道推送**：支持 Telegram、Email 等多种推送渠道

---

## 文件清单

```
silicon-valley-alpha-radar/
├── config/
│   └── push_config.json          # 推送配置文件
├── src/
│   ├── judges/
│   │   └── info_judge.py        # 信息判断层
│   ├── queues/
│   │   └── push_queue_manager.py # 推送队列管理
│   ├── formatters/
│   │   └── push_formatter.py    # 推送格式化器
│   └── services/
│       └── unified_push_service.py # 统一推送服务
├── test_full_push_mechanism.py   # 完整测试脚本
└── README_PUSH_MECHANISM.md     # 本文档
```

---

_信息不对称是终极力量。保持优势！_ 🐱✨
