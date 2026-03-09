# 🔑 API 配置指南 - 超级简洁

## 📱 Twitter API（必需！）

### 步骤 1：申请密钥
1. 打开 https://developer.twitter.com/
2. 进入 **Projects & Apps** → **Create App**
3. 创建后获取：
   - **API Key** (Consumer Key)
   - **API Secret** (Consumer Secret)
   - **Bearer Token** (在 Keys and tokens 标签页下)

### 步骤 2：设置环境变量
```bash
export TWITTER_API_KEY="你的API Key"
export TWITTER_API_SECRET="你的API Secret"
export TWITTER_BEARER_TOKEN="你的Bearer Token"
```

---

## 📊 GitHub API（必需！）

### 步骤 1：申请 Token
1. 打开 GitHub
2. 点击头像 → **Settings**
3. 左侧滚动到底 → **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token (classic)**
6. 勾选：
   - ✅ **repo** (访问公开仓库）
   - ✅ **public_repo** (如果需要)
7. 点击 **Generate token**
8. 复制生成的 Token（只显示一次！）

### 步骤 2：设置环境变量
```bash
export GITHUB_TOKEN="你的GitHub Token"
```

---

## ✅ 验证配置

```bash
# 检查 Twitter
echo $TWITTER_API_KEY
echo $TWITTER_BEARER_TOKEN

# 检查 GitHub
echo $GITHUB_TOKEN
```

每个都应该输出你的密钥！

---

## 🚀 开始使用

配置好 API 密钥后，直接运行：

```bash
cd /Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar
python orchestrator.py --days 7
```

---

## ⚠️ 重要提醒

1. **Twitter API 有免费限制**：每月可以获取推文数有限
2. **GitHub API**：公开数据不需要密钥，但私有仓库需要
3. **保存好密钥**：GitHub Token 只显示一次，立刻保存！
4. **不要分享**：这些是你的私密密钥！

---

**有问题随时通过 WhatsApp 联系我！** 🐱✨
