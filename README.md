# NovelWriter

基于大语言模型的智能小说创作平台。Vue 3 前端 + FastAPI 后端，从构思到成稿的一站式 AI 创作体验。

## 更新记录

### 2026-03-30
- **场景润色对比面板** — 全新段落对齐对比视图，左右分列展示润色前后差异（字符级高亮），下方独立编辑面板支持选择编辑润色前/后文本并保存
- **续写修订上下文注入** — 续写架构的 5 个修订面板（方向大纲/世界观/角色/剧情弧/角色状态）新增"注入上下文"复选框，可选择注入种子/角色/世界观/剧情作为参考
- **修订功能增强** — 后端修订接口支持读取项目已有架构内容作为参考资料注入 prompt，提升修订质量
- **角色状态匹配修复** — 修复精炼章节时角色名匹配失败的问题（如"男主角名：\n陈玉"格式），现在会检查角色块文本前几行进行辅助匹配

### 2026-03-25
- **功能同步** — 同步私有版功能更新：创意讨论、分步修订、角色外貌固定项、蓝图细化、去AI痕迹分轮多深度处理、阅读器可编辑保存等
- **Docker 部署修复** — 修复多个 Docker 首次部署问题（xp_presets.json 目录冲突、单文件挂载报错、shell 运算符优先级等），简化部署流程

### 2026-03-12
- **初始公开发布** — NovelWriter 公开版首次发布，包含完整的小说架构生成、章节生成、文风仿写、叙事DNA、续写扩展等核心功能

## 功能特性

| 功能模块 | 说明 |
|---------|------|
| 小说架构生成 | 核心种子 / 世界观构建 / 角色动力学 / 情节架构 |
| 章节目录规划 | 悬念节奏曲线 / 伏笔管理 / 强度分布设计 |
| 智能章节生成 | 知识库检索 / 前文摘要 / 上下文连贯性保障 |
| 文风仿写 | 分析目标文本风格 → 保存为模板 → 章节生成时自动模仿 |
| 叙事DNA | 分析作者叙事模式（内容配比 / 节奏 / 场景结构）→ 注入架构、蓝图、章节三层生成 |
| 作者参考库 | 导入作者原文 → 向量化存储 → 生成时检索相似片段作为写法示例 |
| 续写扩展 | 在已有故事基础上追加新剧情弧与角色 |
| 创意讨论 | 多轮对话头脑风暴，注入项目上下文（种子/角色/世界观等），与 AI 商讨创意方向 |
| 分步修订 | 对分步生成的每个环节，可基于已有内容 + 修改建议让 LLM 局部修订，无需重新生成 |
| 去AI痕迹 | 分轮多深度清除 AI 生成痕迹，支持单章和批量处理，生成前后对比 |
| 状态追踪 | 角色状态自动更新 / 前文摘要自动维护 / 外貌特征固定项保护（更新时不丢失） |
| 一致性检查 | 检测剧情矛盾与设定冲突 |
| 知识库 | 导入外部参考资料，增强创作深度 |
| 提示词预设 | 多套提示词方案一键切换，支持自定义编辑（含创意讨论提示词） |
| XP预设管理 | 自定义内容类型预设，可创建/编辑/删除，一键注入所有生成阶段 |
| 小说阅读 | 内置阅读器，支持单章 / 全文阅读、字号调节 |
| 项目管理 | 多项目并行管理，独立配置与存储 |

## 快速开始

### 环境要求

- Python 3.12
- Node.js 18+（仅开发模式需要）
- 有效的 LLM API Key（DeepSeek / OpenAI / Gemini / Ollama 等兼容 OpenAI 格式的服务）

### 本地启动

```bash
# 克隆项目
git clone <你的仓库地址>
cd NovelWriter

# 安装 Python 依赖
pip install -r requirements.txt

# 生产模式启动（自动构建前端）
bash start_api.sh

# 或开发模式（后端热重载 + 前端开发服务器）
bash start_api.sh --dev
```

启动后访问 http://localhost:7860

### Docker 部署

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
docker build -t novel-writer .

docker run -d \
  --name novel-writer \
  -p 7860:7860 \
  -v ./output:/app/output \
  -v ./config.json:/app/config.json \
  -v ./styles:/app/styles \
  -v ./prompts:/app/prompts \
  novel-writer
```

## 使用流程

### 1. 配置模型

在「模型配置」页面设置：

- **LLM 配置** — API Key、Base URL、模型名、Temperature 等
- **Embedding 配置** — 向量嵌入模型，用于知识库和作者参考库检索

支持所有兼容 OpenAI API 格式的服务（DeepSeek、硅基流动、OpenRouter、Ollama 等）。

### 2. 创作

在「创作工坊」中按步骤操作：

1. **Step 1 生成架构** — 输入主题 / 类型 / 章节数，生成核心种子、角色体系、世界观、情节架构（支持分步生成，每步可基于建议修订）
2. **Step 2 生成目录** — 规划各章定位、悬念密度、伏笔操作
3. **Step 3 生成章节** — 逐章生成正文，可指定角色 / 道具 / 场景 / 文风（支持流式输出）
4. **Step 4 定稿** — 润色章节，自动更新前文摘要与角色状态
5. **Step 5 去AI痕迹** — 分轮清除 AI 生成痕迹，支持单章和批量处理
6. **Step 6 续写** — 追加新弧与角色（支持分步续写，每步可修订），回到 Step 2-5 继续

### 3. 辅助功能

- **创意讨论** — 在导航栏「创意讨论」中与 AI 进行多轮对话头脑风暴，可选择注入项目上下文（核心种子 / 角色 / 世界观等），讨论创意方向和解决创作难题
- **分步修订** — 分步生成的每个环节（核心种子 / 角色 / 世界观 / 情节等）生成后，展开「✏️ 基于建议修订」面板，输入修改建议即可局部修订
- **文风仿写** — 粘贴目标文本 → 分析风格 → 保存模板 → 在 Step 3「文风选择」中选用
- **叙事DNA** — 粘贴样本文章 → 分析叙事模式 → 在 Step 1/2/3 的「叙事DNA风格」中选用
- **作者参考库** — 上传 .txt 原文 → 向量化 → 生成时自动检索相似片段注入 prompt
- **提示词方案** — 切换 / 编辑不同风格的提示词预设（含创意讨论提示词）
- **知识库** — 导入 .txt 参考资料，生成章节时自动检索
- **一致性检查** — 检测章节与设定的逻辑矛盾
- **小说阅读** — 内置阅读器，按章或全文阅读已生成的内容

## 高级功能

### 叙事DNA

叙事DNA 分析作者在**内容层面**的写作模式，包括：内容配比、推进节奏、场景结构、角色关系模式、对话风格、叙事视角。

**使用步骤：**

1. 打开「文风与DNA」页面
2. 选择 LLM 配置和目标样式（需先创建同名文风样式）
3. 粘贴 1000–5000 字的样本文本（建议使用完整章节）
4. 点击「分析叙事DNA」，结果自动保存
5. 在创作工坊 Step 1/2/3 的「叙事DNA风格」下拉框中选择

> **叙事DNA vs 文风仿写：**
> - 文风仿写（文笔层）= 词汇、句式、修辞、节奏感 → Step 3「文风选择」
> - 叙事DNA（叙事层）= 内容配比、升温节奏、场景结构 → 各阶段「叙事DNA风格」
> - 两者可独立选择、相互叠加

### 作者参考库

将作者原文导入向量库，生成章节时自动检索相似片段作为写法示例。

1. 在「文风与DNA」页面右侧「作者参考库」区域
2. 选择 Embedding 配置，选择关联的文风样式
3. 上传 .txt 格式作者原文（支持多文件批量上传）
4. 生成章节时系统自动检索并以 `【参考原文写法】` 注入 prompt

### 提示词预设

项目内置多套提示词方案，可在「提示词方案」页面切换或自定义编辑：

| 预设 | 适用场景 |
|------|---------|
| 网络小说 | 起点、番茄等网络连载小说 |
| 短篇小说 | 3 万字内短篇小说，剧情短平快 |
| 连载小说 | 多弧结构连载小说 |

每套预设包含完整的架构、目录、章节等各阶段 prompt，可根据需要自由修改。

## 项目结构

```
NovelWriter/
├── api_server.py              # FastAPI 后端入口
├── web_server.py              # Gradio 旧版入口（兼容保留）
├── prompt_definitions.py      # 提示词定义与预设管理
├── config_manager.py          # 配置管理
├── llm_adapters.py            # LLM 接口适配（OpenAI / Ollama）
├── embedding_adapters.py      # Embedding 接口适配
├── consistency_checker.py     # 一致性检查
├── chapter_directory_parser.py# 章节目录解析
├── utils.py                   # 工具函数
├── novel_generator/           # 核心生成逻辑
│   ├── architecture.py        #   架构生成
│   ├── blueprint.py           #   目录生成
│   ├── chapter.py             #   章节生成
│   ├── finalization.py        #   定稿处理
│   ├── humanizer.py           #   去AI痕迹处理
│   ├── knowledge.py           #   知识库管理
│   └── vectorstore_utils.py   #   向量存储工具
├── api/                       # FastAPI 路由
│   └── routers/               #   各功能模块路由
├── frontend/                  # Vue 3 + TypeScript 前端
│   └── src/
│       ├── views/             #   页面视图
│       ├── components/        #   组件
│       └── stores/            #   状态管理
├── prompts/                   # 提示词预设 JSON
├── styles/                    # 文风模板 JSON
├── config.example.json        # 配置模板
├── Dockerfile                 # Docker 多阶段构建
├── docker-compose.yml         # Docker Compose 编排
├── requirements.txt           # Python 依赖
├── start_api.sh               # Linux/macOS 启动脚本
└── start_web.bat              # Windows 启动脚本
```

## 常用配置模板

### DeepSeek

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

### 硅基流动（SiliconFlow）

```
LLM:
  Base URL: https://api.siliconflow.cn/v1
  模型: deepseek-ai/DeepSeek-V3
  Temperature: 0.7
  Max Tokens: 32768

Embedding:
  接口格式: OpenAI
  Base URL: https://api.siliconflow.cn/v1
  模型: Qwen/Qwen3-Embedding-4B
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
Description=NovelWriter Web Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/NovelWriter
ExecStart=/usr/bin/python3 -m uvicorn api_server:app --host 0.0.0.0 --port 7860
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

## 疑难解答

**Q: 无法访问页面？**
检查防火墙是否放通 7860 端口，确认服务正常运行。

**Q: 生成失败 / Expecting value 错误？**
API Key 或 Base URL 配置有误，检查「模型配置」页面。

**Q: 生成速度慢？**
尝试降低 max_tokens、使用更快的模型，或部署本地 Ollama。

**Q: 章节目录信息（本章定位/简述等）全部为空？**
LLM 生成目录时格式不标准。系统已内置兼容处理，若仍出现可打开「文件管理」检查 `Novel_directory.txt`，确认章节头为 `第X章 - 标题` 格式。

**Q: 叙事DNA 分析后章节没有体现风格？**
确认在 Step 1/2/3 各自的「叙事DNA风格」下拉框中选择了对应样式。叙事DNA 与文风仿写是两个独立的选项。

## 致谢
部分代码参考了：https://github.com/YILING0013/AI_NovelGenerator

## License

AGPL-3.0
