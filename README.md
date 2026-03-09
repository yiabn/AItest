游戏知识库 & AI测试辅助系统
📋 项目简介
本项目旨在构建一个智能化的游戏测试辅助系统，能够从游戏官网（以《魔域》为例）自动抓取资料，通过AI技术分析页面内容，提取实体信息（幻兽、技能、装备、任务等），构建知识库，并支持通过对话方式补充和完善数据。系统最终目标是为游戏测试人员提供智能化的测试点生成和管理工具。
✨ 核心功能
🔍 资料抓取与分析
• 输入网址自动抓取游戏官网资料
• 智能识别页面类型（幻兽、技能、装备、任务等）
• 提取实体名称、属性、描述等信息
• 自动保存原始页面快照，便于回溯
📚 知识库管理
• 所有分析结果持久化存储到 PostgreSQL
• 支持实体列表浏览（网格/列表视图）
• 按类型过滤、关键词搜索
• 查看实体详情（属性、关系、补充历史）
• 知识库统计（总实体数、类型分布、今日新增等）
💬 对话式补充
• 针对单个实体进行信息补充
• AI智能解析用户输入（获取方式、属性数值、技能描述等）
• 自动更新实体属性并记录补充历史
• 支持多轮对话（基础版）
📜 历史记录
• 本地保存分析历史
• 支持重新分析和查看详情
🏗️ 技术架构
前端
• 框架：Vue 3 + TypeScript
• UI组件库：Element Plus
• HTTP客户端：Axios
• 日期处理：dayjs
• 数据可视化：ECharts
后端
• Web框架：FastAPI
• 数据库：PostgreSQL 16 + asyncpg
• 爬虫：requests + BeautifulSoup4
• 中文分词：jieba
• 配置管理：pydantic-settings
• 日志：loguru
🚀 快速开始
环境要求
• Python 3.10+
• Node.js 18+
• PostgreSQL 16
• Git
安装步骤
1. 克隆项目
bash
￼
复制
￼
￼
下载
￼
git clone <repository-url>

cd mygame-knowledge
￼
￼
2. 后端安装配置
bash
￼
复制
￼
￼
下载
￼
# 进入后端目录

cd backend


# 创建虚拟环境

python -m venv venv

# Windows

venv\Scripts\activate

# Linux/Mac

source venv/bin/activate


# 安装依赖

pip install -r requirements.txt


# 安装 playwright 浏览器（用于动态页面抓取）

playwright install chromium


# 配置环境变量

cp .env.example .env

# 编辑 .env 文件，填写数据库密码等信息
￼
￼
3. 数据库初始化
bash
￼
复制
￼
￼
下载
￼
# 登录 PostgreSQL

psql -U postgres


# 创建数据库

CREATE DATABASE game_knowledge;


# 执行建表脚本

\c game_knowledge

\i database/init.sql
￼
￼
4. 前端安装配置
bash
￼
复制
￼
￼
下载
￼
# 进入前端目录

cd ../frontend


# 安装依赖

npm install


# 配置环境变量

cp .env.example .env

# 根据需要修改 API 地址
￼
￼
5. 启动服务
bash
￼
复制
￼
￼
下载
￼
# 启动后端（在 backend 目录下）

python run.py


# 启动前端（在 frontend 目录下）

npm run dev
￼
￼
访问 http://localhost:5173 即可使用系统。
项目整体结构
text
mygame-knowledge/
├── frontend/                     # 前端项目 (Vue 3 + TypeScript)
│   ├── public/                   # 静态资源
│   ├── src/
│   │   ├── api/                   # API 接口封装
│   │   │   └── config.ts           # Axios 配置及所有后端接口定义
│   │   ├── assets/                 # 图片、样式等
│   │   ├── components/             # 可复用组件
│   │   ├── router/                 # 路由配置
│   │   │   └── index.ts             # 路由表
│   │   ├── types/                   # TypeScript 类型定义
│   │   │   └── index.ts              # 全局类型（AnalysisResult, Entity 等）
│   │   ├── views/                    # 页面视图组件
│   │   │   ├── HomeView.vue           # 首页：网址输入、分析结果、对话补充
│   │   │   ├── HistoryView.vue        # 历史记录页面
│   │   │   ├── KnowledgeView.vue      # 知识库浏览页面
│   │   │   └── SettingsView.vue       # 设置页面（占位）
│   │   ├── App.vue                    # 根组件（含侧边栏布局）
│   │   ├── main.ts                    # 入口文件
│   │   └── shims-vue.d.ts             # Vue 模块声明
│   ├── .env                           # 环境变量
│   ├── index.html                     # HTML 模板
│   ├── package.json                   # 依赖管理
│   ├── tsconfig.json                  # TypeScript 配置
│   └── vite.config.ts                  # Vite 配置
│
├── backend/                      # 后端项目 (FastAPI + Python)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 应用入口，注册路由，CORS，生命周期
│   │   ├── config.py                   # 配置类（从环境变量加载）
│   │   ├── database.py                  # 数据库连接池及通用 CRUD 操作
│   │   ├── models/                      # Pydantic 模型（请求/响应）
│   │   │   ├── __init__.py
│   │   │   ├── request.py                # 请求模型（AnalyzeRequest, ChatRequest）
│   │   │   └── response.py               # 响应模型（AnalyzeResponse, EntityInfo, ChatResponse）
│   │   ├── api/                          # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py                 # 分析相关接口
│   │   │   ├── chat.py                    # 对话补充接口
│   │   │   └── knowledge.py                # 知识库查询接口
│   │   ├── services/                      # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   └── analysis_service.py         # 分析服务（爬虫+解析+存储）
│   │   ├── crawlers/                       # 爬虫模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py                      # 基础爬虫类
│   │   │   └── m99_crawler.py                # 魔域官网专用爬虫
│   │   ├── parsers/                         # 解析器模块
│   │   │   ├── __init__.py
│   │   │   └── entity_extractor.py           # 实体提取器（基于 jieba 和规则）
│   │   └── utils/                           # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py                    # 辅助函数（生成ID、JSON处理等）
│   ├── logs/                             # 日志目录
│   ├── .env                               # 环境变量（数据库密码等）
│   ├── requirements.txt                   # Python 依赖
│   └── run.py                             # 开发环境启动脚本
└── README.md                          # 项目说明
核心文件功能详解
前端关键文件
文件路径	功能描述
src/api/config.ts	封装 Axios 实例，定义 analyzeApi、chatApi、knowledgeApi 三大模块的接口方法，统一处理请求响应和错误提示。
src/types/index.ts	定义全局 TypeScript 类型：Entity、AnalysisResult、ChatMessage、KnowledgeStats 等，确保前后端数据类型一致。
src/views/HomeView.vue	主页面：网址输入、分析选项、分析结果展示（基础信息、实体卡片/表格、AI建议、原始内容）、对话补充对话框。
src/views/HistoryView.vue	历史记录页：从 localStorage 读取历史分析记录，支持重新分析、查看详情、删除、清空。
src/views/KnowledgeView.vue	知识库浏览页：统计卡片、搜索过滤、实体列表（网格/列表切换）、分页、实体详情抽屉（含属性和关系）、统计详情弹窗。
src/App.vue	根组件：包含侧边栏导航（资料分析、历史记录、知识库、设置）和主内容区布局。
src/router/index.ts	定义路由映射，实现页面切换。
后端关键文件
文件路径	功能描述
app/main.py	FastAPI 应用入口：配置 CORS、注册路由（/api/analyze、/api/chat、/api/knowledge），添加启动/关闭事件管理数据库连接。
app/config.py	使用 pydantic-settings 从环境变量加载配置（数据库连接、爬虫参数等）。
app/database.py	定义 Database 类，封装 PostgreSQL 连接池和通用数据库操作（fetch、execute 等），并提供实体、关系、补充等专用方法。
app/models/response.py	定义 Pydantic 响应模型：EntityInfo、AnalyzeResponse、ChatResponse 等，用于接口返回数据校验。
app/api/analyze.py	分析接口：POST /url 接收网址，调用 AnalysisService 分析并返回结果；GET /task/{task_id} 获取任务结果。
app/api/chat.py	对话补充接口：POST /supplement 接收用户消息，解析意图并更新实体属性；GET /history/{entity_id} 获取补充历史。
app/api/knowledge.py	知识库接口：GET /entities（分页、过滤）、GET /entities/{id}（详情）、GET /types（类型统计）、GET /search（搜索）、GET /relations/{id}、GET /recent、GET /stats 等。
app/services/analysis_service.py	核心业务类：整合爬虫和解析器，执行分析流程，将结果存入数据库，并返回标准化响应。
app/crawlers/m99_crawler.py	魔域官网专用爬虫：实现 analyze_page 方法，根据 URL 判断页面类型，提取标题、纯文本和原始 HTML，调用对应解析方法。
app/parsers/entity_extractor.py	实体提取器：基于 jieba 分词和正则规则，从文本中识别实体名称、类型和简单属性。
run.py	开发环境启动脚本：设置 Python 路径，启动 uvicorn 服务器。
数据库表结构（PostgreSQL）
已在前一个回答中详细列出，包含 entities、relations、user_supplements、page_snapshots、analysis_tasks 五张表及其索引、触发器。核心表使用 UUID 主键和 JSONB 字段存储动态属性，支持灵活扩展。

总结
整个项目采用前后端分离架构，前端使用 Vue 3 + TypeScript + Element Plus，后端使用 FastAPI + asyncpg + Pydantic。实现了从游戏官网抓取资料、解析实体、存入数据库、提供查询和对话补充的完整流程。当前系统已具备基础功能，下一步可在此基础上增强解析智能、测试点生成和对话交互能力。
￼
￼
📊 数据库设计
核心表包括：
• entities：实体主表，使用JSONB存储动态属性
• relations：实体关系表
• user_supplements：用户补充记录
• page_snapshots：页面快照
• analysis_tasks：分析任务记录
详细表结构见 database/init.sql
🎯 已实现功能
✅ 基础架构：前后端分离，FastAPI + Vue 3
✅ 数据抓取：支持魔域官网资料页面抓取
✅ 实体提取：基于规则的实体识别
✅ 数据库持久化：PostgreSQL 存储
✅ 知识库查询：列表、详情、搜索、统计
✅ 对话补充：基础意图识别和信息更新
✅ 历史记录：本地存储分析历史
🚧 待优化项
1. 解析能力增强：支持更复杂的页面（技能专精、任务活动），提取结构化数据
2. 测试点生成：基于游戏规则自动生成可执行的测试用例
3. 对话升级：上下文理解、多轮交互、主动提问
4. 关系图谱：完善实体关系提取和可视化
5. 用户系统：支持多用户，数据跨设备同步
6. 部署方案：Docker 容器化，支持云部署
📝 使用指南
分析页面
1. 在首页输入网址（如 https://my.99.com/data/pet/123.html）
2. 点击"开始分析"，等待结果
3. 查看提取的实体信息和AI建议
4. 可通过对话补充缺失信息
浏览知识库
1. 点击左侧"知识库"导航
2. 查看统计卡片了解数据概况
3. 使用搜索和过滤快速定位实体
4. 点击实体查看详情（属性、关系、补充历史）
查看历史
1. 点击"历史记录"导航
2. 查看所有历史分析任务
3. 可重新分析或查看详情
🤝 贡献指南
欢迎提交 Issue 和 Pull Request 来帮助改进项目。
📄 许可证
MIT License
📧 联系方式
项目维护者：[你的名字]
邮箱：[你的邮箱]
￼
项目状态：开发中 v1.0.0
