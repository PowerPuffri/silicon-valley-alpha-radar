# 持续监控服务 - 快速指南

## 🚀 服务状态

✅ **服务已启动** - 持续监控运行中
- 📅 检查间隔：每 30 分钟
- 📡 推送渠道：Telegram (Chat ID: 7974510481)
- 🔴 重磅级：立即推送
- 🟠 重要：每小时推送
- 🟡 普通：每3小时推送

---

## 📱 Telegram 推送已测试通过

请检查您的 Telegram 是否收到了测试消息！

---

## 🛠️ 服务管理

### 1. 启动服务

**方式一：使用启动脚本（推荐）**
```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
./start_monitoring.sh
```

**方式二：直接运行**
```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
source venv/bin/activate
python src/services/unified_push_service.py --start --interval 30
```

### 2. 停止服务

在运行服务的终端中按 `Ctrl+C`

### 3. 查看队列状态

```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
source venv/bin/activate
python src/services/unified_push_service.py --status
```

### 4. 发送测试消息

```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
source venv/bin/activate
python test_telegram_push.py
```

---

## 📊 推送时机

| 级别 | 推送频率 | 推送时间 |
|------|----------|----------|
| 🔴 重磅 | 立即 | 检测到即推送（00:00-07:00 静默） |
| 🟠 重要 | 每小时 | 整点推送 |
| 🟡 普通 | 每3小时 | 09:00, 12:00, 15:00, 18:00, 21:00 |

---

## ⚙️ 配置文件

### 主配置 (`config/config.json`)
- 监控账号和仓库
- 关键词列表
- **Telegram 配置**（botToken, chatId）

### 推送配置 (`config/push_config.json`)
- 推送策略（间隔、批量大小、静默时段）
- 判断阈值
- 权重配置
- 关键词列表

---

## 🔍 监控范围

### 仓库
- `openai/*`
- `deepmind/*`
- `anthropic/*`
- `google-research/*`
- `facebookresearch/*`
- `huggingface/*`

### 作者
- sama, ilyasut, gdb (OpenAI)
- demishassabis, mustafasuleyman (DeepMind)
- karpathy, lecun, jeffdean
- andrewyng, goodfellow

### 数据源
- **GitHub**（主要数据源）
- Twitter
- Reddit
- Hacker News

---

## 📝 工作流程

```
数据收集 (30分钟间隔)
    ↓
信息判断 (分级: 🔴🟠🟡)
    ↓
添加到队列
    ↓
定时推送
    ↓
Telegram 推送
```

---

## 🐛 故障排查

### 问题：没有收到推送
1. 检查 Telegram 配置是否正确
2. 查看服务日志
3. 测试推送：`python test_telegram_push.py`

### 问题：判断级别不准确
1. 调整 `config/push_config.json` 中的权重和阈值
2. 添加或修改关键词列表

### 问题：推送过多
1. 调整静默时段（00:00-07:00）
2. 减少每日上限（默认 10 条/天）
3. 调整批量大小

---

## 📈 后续优化建议

1. **机器学习优化**：使用历史数据训练模型，提高判断准确性
2. **自适应阈值**：根据历史数据动态调整阈值
3. **用户反馈**：允许标记推送级别，持续优化
4. **多渠道推送**：支持 Email、Slack 等

---

## 📁 相关文件

```
silicon-valley-alpha-radar/
├── start_monitoring.sh          # 启动脚本
├── test_telegram_push.py         # Telegram 测试
├── test_full_push_mechanism.py   # 完整测试
├── src/services/
│   └── unified_push_service.py   # 推送服务
├── config/
│   ├── config.json               # 主配置
│   └── push_config.json          # 推送配置
└── storage/data/
    ├── github_activity.db         # GitHub 数据
    └── push_queue.db             # 推送队列
```

---

## ✅ 快速检查

```bash
# 查看队列状态
python src/services/unified_push_service.py --status

# 发送测试消息
python test_telegram_push.py

# 运行完整测试
python test_full_push_mechanism.py
```

---

## 📞 联系方式

如有问题，请查看日志或运行测试脚本诊断。

---

_信息不对称是终极力量。保持优势！_ 🐱✨
