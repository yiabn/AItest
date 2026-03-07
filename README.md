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