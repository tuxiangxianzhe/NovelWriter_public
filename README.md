# AI Novel Writer

基于大语言模型的智能小说创作平台，通过浏览器访问，从构思到成稿一站式 AI 创作体验。

## 功能特性

| 功能模块 | 说明 |
|---------|------|
| 小说架构生成 | 世界观构建 / 角色动力学 / 三幕式情节架构 |
| 章节目录规划 | 悬念节奏曲线 / 伏笔管理 / 认知颠覆设计 |
| 智能章节生成 | 知识库检索 / 前文摘要 / 上下文连贯性保障 |
| 小说架构生成 | 世界观构建 / 角色动力学 / 三幕式情节架构 |
| 章节目录规划 | 悬念节奏曲线 / 伏笔管理 / 官能强度分布 |
| 智能章节生成 | 知识库检索 / 前文摘要 / 上下文连贯性保障 |
| 文风仿写 | 分析目标文本风格 → 保存为模板 → 章节生成时模仿 |
| 叙事DNA | 分析作者叙事模式（内容配比/节奏/场景结构）→ 注入架构/蓝图/章节三层生成 |
| 作者参考库 | 导入作者原文 → 生成章节时检索相似片段作为写法示例 |
| XP 类型 | 在创作工坊全局设定 XP 类型，自动注入所有生成阶段 |
| 短篇拔作预设 | 专为3万字内官能短篇优化的提示词方案，剧情短平快 |
| 续写扩展 | 在已有故事基础上追加新剧情弧与角色 |
| 状态追踪 | 角色状态自动更新 / 前文摘要自动维护 |
| 一致性检查 | 检测剧情矛盾与设定冲突 |
| 知识库 | 导入外部参考资料，增强创作深度 |
| 提示词预设 | 多套提示词方案一键切换（网文 / 短篇拔作 / Pixiv 等） |

## 快速开始

### 环境要求

- Python 3.9+（推荐 3.10-3.12）
- 有效的 LLM API Key（DeepSeek / OpenAI / Ollama 等）

### 本地启动

```bash
# 克隆项目
git clone https://github.com/YILING0013/AI_NovelGenerator
cd AI_NovelGenerator

# 安装依赖
pip install -r requirements.txt

# 启动
python web_server.py
```

启动后访问 http://localhost:7860

也可以使用启动脚本：

```bash
# Linux / macOS
./start_web.sh

# Windows
start_web.bat
```

### Docker 部署（推荐）

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

启动后访问 http://your-server-ip:7860

#### 手动 Docker 构建

```bash
# 构建镜像
docker build -t ai-novel-writer .

# 运行
docker run -d \
  --name ai-novel-writer \
  -p 7860:7860 \
  -v ./output:/app/output \
  -v ./config.json:/app/config.json \
  -v ./styles:/app/styles \
  -v ./prompts:/app/prompts \
  ai-novel-writer
```

## 使用流程

### 1. 配置模型

- **LLM 配置** — 设置大语言模型的 API Key、地址、模型名等参数
- **Embedding 配置** — 设置向量嵌入模型，用于知识检索

### 2. 创作

在「创作工坊」中按步骤操作：

1. **Step 1 生成架构** — 输入主题/类型/章节数，生成核心种子、角色体系、世界观、情节架构
2. **Step 2 生成目录** — 规划各章定位、悬念密度、伏笔操作
3. **Step 3 生成章节** — 逐章生成正文，可指定角色/道具/场景/文风
4. **Step 4 定稿** — 润色章节，自动更新前文摘要与角色状态
5. **Step 5 续写** — 追加新弧与角色，回到 Step 2-4 继续

### 3. 辅助功能

- **文风仿写** — 粘贴目标文本 → 分析风格 → 保存模板 → 在 Step 3「文风选择」中选用
- **叙事DNA** — 粘贴样本文章 → 分析叙事模式 → 在 Step 1/2/3 的「叙事DNA风格」中选用
- **提示词方案** — 切换/编辑不同风格的提示词预设（包含内置「短篇拔作」方案）
- **知识库** — 导入 .txt 参考资料，生成章节时自动检索
- **一致性检查** — 检测章节与设定的逻辑矛盾

---

## 高级功能

### 短篇拔作（官能向）

适合创作 3 万字以内、剧情短平快的官能小说。

**第一步：切换提示词预设**

在「提示词方案」Tab → 选择「短篇拔作」→ 点击「激活预设」。

该预设针对拔作重写了以下 Prompt：
- 架构生成：去掉三幕式复杂结构，改为起/承/转/合四段快节奏框架
- 章节目录：字段重定义为「升温进度」「官能强度（★1-5）」「XP玩法」
- 章节正文：以心理沉沦、感官沉浸、动作序列化为核心写作重点
- 场景扩写：XP 特质强化（催眠/NTR/乱伦等 XP 的专属扩写逻辑）

**第二步：设定 XP 类型**

在「创作工坊」Tab 顶部找到 XP 类型设定区：

- **XP 类型下拉框** — 选择内置类型（催眠/性转/NTR/乱伦/强制/支配等）
- **XP 补充说明** — 填写更具体的描述，例如：
  - `催眠后人格解离，被催眠者保有意识但无法抵抗`
  - `NTR，视角为被绿的丈夫，旁观视角`
  - `姐弟乱伦，姐姐主动，弟弟半推半就`

XP 类型会以 `【XP类型/核心玩法】...` 的形式自动注入到**所有生成阶段**（架构、目录、章节、场景扩写），无需在每一步手动重复填写。

**推荐创作参数（拔作）：**

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 章节数 | 5–15 章 | 3万字以内，每章2000–3000字 |
| 每章字数 | 2000–3000 字 | 过短则场景不够细腻 |
| Temperature | 0.8–1.0 | 适当提高创意性 |
| Max Tokens | 4096+ | 章节生成需要足够的输出长度 |

---

### 叙事DNA

叙事DNA分析作者在内容层面的写作模式（不同于文风仿写的文笔层分析），包括：内容配比、推进节奏、场景结构、角色关系模式、玩法偏好、对话风格、叙事视角。

**使用步骤：**

1. 打开「叙事DNA」Tab
2. 选择 LLM 配置，选择目标样式（需先在「文风仿写」中创建一个同名样式）
3. 粘贴 1000–5000 字的样本文本（建议使用完整章节）
4. 点击「分析叙事DNA」，等待生成
5. 分析结果自动保存到对应样式的 JSON 文件，包含三段指令：
   - **架构指令** — 在 Step 1 生成架构时注入
   - **蓝图指令** — 在 Step 2 生成目录时注入
   - **章节指令** — 在 Step 3 生成章节时注入
6. 在创作工坊 Step 1/2/3 的「叙事DNA风格」下拉框中选择该样式

> **叙事DNA 与 文风仿写 的区别：**
> - 文风仿写（文笔层）= 词汇、句式、修辞、节奏感 → 在 Step 3「文风选择」中使用
> - 叙事DNA（叙事层）= 内容配比、升温节奏、场景结构、XP玩法偏好 → 在各阶段「叙事DNA风格」中使用
> - 两者可以独立选择，相互叠加

---

### 作者参考库

将作者原文导入向量库，生成章节时自动检索相似片段，直接展示给 LLM 作为写法示例。

**使用步骤：**

1. 打开「叙事DNA」Tab → 找到右侧「作者参考库」区域
2. 选择 Embedding 配置，填写项目保存路径
3. 上传 .txt 格式的作者原文（可多次上传，会追加到同一个库中）
4. 点击「导入参考库」，等待向量化完成
5. 之后在该路径下生成章节（Step 3）时，系统会自动检索相似原文片段，以 `【参考原文写法】` 块注入到 prompt 中

> 参考库按项目路径隔离，不同故事项目互不影响。
> 点击「清空参考库」可删除当前路径下的所有参考库数据。

## 项目结构

```
NovelWriter/
├── web_server.py              # Web 应用入口
├── prompt_definitions.py      # 提示词定义与预设管理
├── config_manager.py          # 配置管理
├── llm_adapters.py            # LLM 接口适配
├── embedding_adapters.py      # Embedding 接口适配
├── consistency_checker.py     # 一致性检查
├── chapter_directory_parser.py# 章节目录解析
├── utils.py                   # 工具函数
├── novel_generator/           # 核心生成逻辑
│   ├── architecture.py        #   架构生成
│   ├── blueprint.py           #   目录生成
│   ├── chapter.py             #   章节生成
│   ├── finalization.py        #   定稿处理
│   └── vectorstore_utils.py   #   向量存储
├── prompts/                   # 提示词预设 JSON
├── styles/                    # 文风模板 JSON
├── Dockerfile                 # Docker 构建
├── docker-compose.yml         # Docker Compose 编排
├── requirements.txt           # Python 依赖
├── start_web.sh               # Linux/macOS 启动脚本
└── start_web.bat              # Windows 启动脚本
```

## 常用配置模板

### DeepSeek（推荐）

```
LLM:
  Base URL: https://api.deepseek.com/v1
  模型: deepseek-chat
  Temperature: 0.7
  Max Tokens: 8192

Embedding:
  接口格式: OpenAI
  Base URL: https://api.openai.com/v1
  模型: text-embedding-ada-002
```

### Ollama 本地（免费）

```bash
# 先安装模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

```
LLM:
  Base URL: http://localhost:11434/v1
  模型: qwen2.5:7b
  API Key: ollama

Embedding:
  接口格式: Ollama
  Base URL: http://localhost:11434
  模型: nomic-embed-text
```

## 服务器部署

### systemd 服务

创建 `/etc/systemd/system/novel-writer.service`：

```ini
[Unit]
Description=AI Novel Writer Web Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/NovelWriter
ExecStart=/usr/bin/python3 web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now novel-writer
```

### Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 访问认证

编辑 `web_server.py` 中的 `demo.launch()`：

```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    auth=("admin", "your-password")
)
```

## 疑难解答

**Q: 无法访问页面？**
检查防火墙是否放通 7860 端口，确认服务正常运行。

**Q: 生成失败 / Expecting value 错误？**
API Key 或 Base URL 配置有误，检查 LLM 配置。

**Q: 生成速度慢？**
尝试降低 max_tokens、使用更快的模型，或部署本地 Ollama。

**Q: 生成章节时目录信息（本章定位/简述等）全部为空？**
LLM 生成目录时使用了非标准格式（中文数字章号、冒号分隔、Markdown 加粗等）。系统已内置兼容处理，若仍出现问题，可打开「查看已有」检查 `Novel_directory.txt` 的格式，确认章节头格式为 `第X章 - 标题` 或其常见变体。

**Q: 叙事DNA分析后，章节生成没有体现叙事风格？**
确认在 Step 1/2/3 各自的「叙事DNA风格」下拉框中选择了对应样式（不是「不使用文风」）。叙事DNA与文风仿写是两个独立的下拉框。

**Q: XP 类型设定了但生成内容没有体现？**
检查「提示词方案」是否已切换为「短篇拔作」预设。默认「网络小说」预设的 prompt 结构不会特别强调 XP 元素，短篇拔作预设的 prompt 才会充分利用 XP 类型指导。
