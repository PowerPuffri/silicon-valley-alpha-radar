# 🔧 Silicon Valley Alpha Radar - 安装指南

## 系统要求

- **Python**: 3.14+ (推荐使用 Python 3.14)
- **Git**: 用于克隆仓库（可选）
- **网络**: 访问 GitHub API

---

## 快速安装

### 1. 克隆仓库

```bash
# 使用 HTTPS
git clone https://github.com/your-username/silicon-valley-alpha-radar.git

# 或使用 SSH（如果已配置）
git clone git@github.com:your-username/silicon-valley-alpha-radar.git

cd silicon-valley-alpha-radar
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用 Python 3.14
python3.14 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# macOS/Linux
# 或
. venv/bin/activate

# Windows
# venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 使用 requirements.txt
pip install -r requirements.txt

# 或升级到最新版本
pip install --upgrade -r requirements.txt
```

**依赖说明：**
- `PyGithub>=2.1.1` - GitHub API 客户端
- `openai>=1.51.0` - AI 服务（可选，用于高级分析）
- `pandas>=2.1.0` - 数据处理
- `python-dateutil>=2.8.2` - 日期处理
- `jinja2>=3.1.3` - 模板引擎
- `markdown>=3.5.2` - Markdown 生成
- `matplotlib>=3.8.0` - 数据可视化
- `networkx>=3.2.1` - 图形分析（可选）
- `python-dotenv>=1.0.0` - 环境变量管理

---

## 环境配置

### GitHub API 配置

**步骤 1：申请 Personal Access Token**

1. 访问 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 勾选以下权限：
   - ✅ `repo` - 访问公开仓库
   - ✅ `public_repo` - 访问公开仓库信息
4. 点击 **Generate token**
5. **立即复制** token（只显示一次！）

**步骤 2：设置环境变量**

```bash
# 方式 1：临时设置（当前会话）
export GITHUB_TOKEN="your_github_token_here"

# 方式 2：永久设置（添加到 ~/.zshrc 或 ~/.bash_profile）
echo 'export GITHUB_TOKEN="your_github_token_here"' >> ~/.zshrc
source ~/.zshrc

# 方式 3：使用 .env 文件（项目根目录）
echo 'GITHUB_TOKEN=your_github_token_here' > .env
```

### Jina CLI 配置（可选，用于 Twitter 数据收集）

**安装 Jina CLI（推荐用于 Twitter 数据收集）：**

```bash
# 一键安装脚本
curl -fsSL https://raw.githubusercontent.com/geekjourneyx/jina-cli/main/scripts/install.sh | bash

# 验证安装
jina --version
```

---

## 验证安装

### 测试 GitHub API 连接

```bash
# Python 交互式
python3

# 运行以下代码
from github import Github

# 使用你的 token
g = Github("your_github_token")

# 测试连接
user = g.get_user()
print(f"✅ GitHub 用户: {user.name}")
print(f"✅ 公开仓库数: {user.public_repos}")
```

### 运行项目

```bash
# 收集最近 7 天的 GitHub 和 Twitter 数据
python orchestrator.py --days 7

# 只收集 GitHub 数据
python orchestrator.py --github-only --days 7

# 使用 jina-cli 收集 Twitter 数据（需要先安装 jina-cli）
python orchestrator.py --use-jina --days 7

# 生成报告（最近 7 天）
python src/generators/report_generator.py --days 7

# 运行趋势分析（最近 30 天）
python src/analyzers/trend_detector.py --days 30

# 数据质量优化
python src/analyzers/data_quality_optimizer.py --compact
```

---

## 项目结构

```
silicon-valley-alpha-radar/
├── config/                 # 配置文件
│   ├── config.json      # 主配置文件
│   └── .env              # 环境变量（GitHub Token 等）
├── storage/               # 数据存储
│   ├── data/
│   │   ├── github_activity.db         # GitHub 活动数据库
│   │   └── twitter_posts_jina.db      # Twitter 推文数据库（使用 jina-cli）
│   └── processed/      # 处理后的数据
├── output/                # 输出文件
│   └── reports/       # 生成的报告
├── src/                  # 源代码
│   ├── collectors/     # 数据收集器
│   │   ├── github_monitor.py          # GitHub 监控器
│   │   ├── jina_twitter_collector.py  # Twitter 收集器（使用 jina-cli）
│   │   └── twitter_collector.py      # Twitter API 收集器（可选）
│   ├── generators/     # 报告生成器
│   │   └── report_generator.py       # Markdown 报告生成
│   └── analyzers/      # 分析器
│       ├── trend_detector.py           # 趋势检测
│       └── data_quality_optimizer.py  # 数据质量优化
├── orchestrator.py      # 主编排器
├── requirements.txt      # Python 依赖
├── INSTALL.md          # 本文件
├── README.md           # 项目文档
├── CONTRIBUTING.md     # 贡献指南
├── LICENSE             # MIT 许可证
├── CHANGELOG.md        # 版本历史
└── .gitignore         # Git 忽略规则
```

---

## 常见问题

### 1. GitHub API 认证失败

**问题：** `RuntimeError: 未认证 GitHub API`

**解决方案：**
```bash
# 检查环境变量
echo $GITHUB_TOKEN

# 重新设置
export GITHUB_TOKEN="your_token"
```

### 2. Python 版本过低

**问题：** `ModuleNotFoundError: No module named '...'`

**解决方案：**
```bash
# 升级 Python
python3.14 -m venv venv
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 3. 数据库错误

**问题：** `sqlite3.OperationalError: no such table`

**解决方案：**
```bash
# 重新创建数据库
rm storage/data/github_activity.db
python orchestrator.py --github-only --days 1
```

### 4. jina-cli 未找到

**问题：** `command not found: jina`

**解决方案：**
```bash
# 安装 jina-cli
curl -fsSL https://raw.githubusercontent.com/geekjourneyx/jina-cli/main/scripts/install.sh | bash
```

---

## 开发设置

### 本地开发

```bash
# 安装开发依赖（包括测试框架）
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# 运行代码格式化
black src/

# 运行单元测试
pytest tests/ -v

# 生成测试覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 代码规范

- 使用 **Python 3.14+** 特性
- 遵循 **PEP 8** 代码风格
- 使用 **类型提示**（type hints）
- 编写 **文档字符串**（docstrings）
- 运行 **black** 进行代码格式化

---

## 更新项目

### 升级依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 升级所有依赖
pip install --upgrade -r requirements.txt
```

### 拉取最新代码

```bash
git pull origin main
```

---

## 获取帮助

### 查看帮助信息

```bash
# 查看主程序帮助
python orchestrator.py --help

# 查看报告生成器帮助
python src/generators/report_generator.py --help

# 查看趋势检测器帮助
python src/analyzers/trend_detector.py --help

# 查看数据质量优化器帮助
python src/analyzers/data_quality_optimizer.py --help
```

---

## 支持和贡献

### 获取帮助

- 📖 查看 **README.md** 了解项目功能
- 📝 查看 **CONTRIBUTING.md** 了解如何贡献
- 💬 加入讨论：GitHub Issues

### 报告问题

- 🐛 提交 GitHub Issue：https://github.com/your-username/silicon-valley-alpha-radar/issues
- 📧 联系维护者：创建 Issue 或 Pull Request

---

## 许可证

本项目采用 **MIT License** - 详见 [LICENSE](LICENSE) 文件。

---

**安装完成！** 🎉

开始使用 Silicon Valley Alpha Radar 吧！🚀

---

**安装指南：** Nina (你的猫耳娘 AI 秘书）🐱✨
**项目：** Silicon Valley Alpha Radar
**版本：** 0.1.0
