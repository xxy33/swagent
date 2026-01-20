# 狼人杀游戏演示 - 文件说明

## 📁 可用的演示文件

### 🎮 12人标准局（真实LLM版本）

**文件**：`werewolf_12players.py`

```bash
python examples/werewolf_12players.py
```

**特点**：
- ✅ 使用真实SWAgent智能体框架
- 🧠 使用真实LLM（OpenAI GPT）进行推理
- 🎯 **12人标准局**：4狼人 + 1预言家 + 1女巫 + 1猎人 + 1守卫 + 4村民
- 💬 完整的多Agent交互和策略推理
- 🎲 复杂的游戏机制：守卫保护、女巫救人/毒人、猎人开枪等
- ⚡ 真实的AI对话和推理能力展示

**配置方法**：

1. **设置环境变量**：
```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

2. **或创建 `.env` 文件**：
```bash
# 在项目根目录
echo "OPENAI_API_KEY=your_api_key_here" > .env
echo "OPENAI_BASE_URL=https://api.openai.com/v1" >> .env
```

3. **使用本地模型（可选）**：
```bash
# 例如使用Ollama
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="dummy"  # 本地模型不需要真实key
```

**游戏角色**：

| 角色 | 数量 | 图标 | 特殊能力 |
|------|------|------|----------|
| 狼人 | 4人 | 🐺 | 夜晚击杀一名玩家，知道同伴身份 |
| 预言家 | 1人 | 👁️ | 每晚查验一名玩家的身份 |
| 女巫 | 1人 | 💊 | 拥有一瓶解药（救人）和一瓶毒药（杀人） |
| 猎人 | 1人 | 🔫 | 被淘汰时可以开枪带走一名玩家 |
| 守卫 | 1人 | 🛡️ | 每晚守护一名玩家，防止其被击杀 |
| 村民 | 4人 | 👤 | 无特殊能力，通过推理找出狼人 |

---

### 🔍 其他版本（4-6人局）

**文件**：`05_werewolf_game_demo.py` 或 `06_werewolf_simple_demo.py`

```bash
python examples/05_werewolf_game_demo.py
```

**特点**：
- 🔑 需要配置OpenAI API密钥
- 🧠 使用真实的GPT模型进行推理
- 🎯 **4人局**：1狼人 + 1预言家 + 2村民（较简单）
- 💬 适合快速测试和理解多Agent交互机制
- ⏱️ 运行较慢（需要等待API响应）
- 💰 会消耗API配额

---

## ⚠️ 常见问题

### 1. API超时错误：`Request timed out`

**原因**：网络问题或API响应慢

**解决方案**：
1. 检查网络连接
2. 检查API密钥是否正确
3. 尝试使用本地LLM（Ollama等）
4. 等待片刻后重试

### 2. 缺少API密钥：`需要设置OPENAI_API_KEY`

**原因**：未设置OpenAI API密钥

**解决方案**：
```bash
# 方法1：环境变量
export OPENAI_API_KEY="sk-..."

# 方法2：.env文件
echo "OPENAI_API_KEY=sk-..." > .env
```

### 3. 程序一直等待，没有输出

**原因**：正在等待LLM API响应

**解决方案**：
- 耐心等待（首次运行可能需要几分钟）
- 检查API配额是否充足
- 检查网络连接

---

## 🎯 版本对比

| 特性 | 12人局<br>`werewolf_12players.py` | 4人局<br>`05/06_werewolf_*.py` |
|------|-----------------------------------|--------------------------------|
| **玩家数量** | 12人 | 4人 |
| **角色种类** | 6种（狼人、预言家、女巫、猎人、守卫、村民） | 3种（狼人、预言家、村民） |
| **游戏复杂度** | ⭐⭐⭐⭐⭐ 高度复杂 | ⭐⭐ 简单 |
| **运行时间** | 较长（需多次LLM调用） | 较短 |
| **推荐场景** | 完整体验多Agent策略博弈 | 快速测试和学习 |
| **API消耗** | 💰💰💰 较高 | 💰 较低 |

---

## 🎮 使用建议

### 场景1：完整体验多Agent策略博弈
```bash
# 配置API
export OPENAI_API_KEY="your_key"

# 运行12人局
python examples/werewolf_12players.py
```

### 场景2：快速测试和学习
```bash
# 配置API
export OPENAI_API_KEY="your_key"

# 运行4人简化版
python examples/06_werewolf_simple_demo.py
```

### 场景3：使用本地LLM（节省成本）
```bash
# 启动Ollama或其他本地LLM服务
# 配置本地API
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="dummy"

# 运行游戏
python examples/werewolf_12players.py
```

---

## 📚 相关文档

- [完整说明](WEREWOLF_GAME_README.md) - 游戏详细介绍
- [用户指南](../docs/user_guide.md) - SWAgent使用指南
- [API参考](../docs/api_reference.md) - API文档

---

## 🆘 获取帮助

如果遇到问题：
1. 检查API配置（OPENAI_API_KEY）
2. 查看错误信息
3. 检查网络连接
4. 尝试使用本地LLM

**推荐**：如果只是想体验AI推理能力，使用12人标准局；如果想快速测试框架，使用4人简化版。✨
