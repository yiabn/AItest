AItest 是一个面向游戏测试人员的智能辅助工具。它能自动分析游戏页面内容或相关文档（如策划案、需求文档），并基于分析结果生成结构化的测试点。旨在减少手工编写测试用例的重复劳动，提高测试覆盖率和效率。

核心功能：输入一个游戏相关页面 URL 或上传文档 → 系统自动解析 → 输出测试点列表（含功能点、边界条件、异常场景等）。

✨ 主要功能
🌐 页面分析：输入游戏活动页面、功能界面等 URL，自动提取页面元素和文本内容。

📄 文档解析：支持上传策划文档（如 Word、PDF、Markdown），提取关键需求和规则。

🤖 测试点生成：基于提取的内容，利用 NLP 技术智能生成功能测试点、边界值测试点、异常场景测试点。

📊 结果可视化：前端以表格、卡片等形式清晰展示生成的测试点，并支持导出为 Excel/CSV。

⚙️ 可配置规则：支持自定义测试点生成规则（如包含/排除关键词、测试深度等）。

🛠️ 技术栈
后端
框架：FastAPI (Python 3.8+)

爬虫/解析：Requests, BeautifulSoup4, Playwright (用于动态页面)

文档处理：python-docx, PyPDF2, markdown

NLP/分析：Jieba (分词), Transformers (可选，用于更高级语义)

数据格式：Pydantic, JSON

前端
框架：Vue 3 (Vite)

UI 组件：Element Plus 或 Ant Design Vue

HTTP 请求：Axios

可视化：ECharts 或 Table 组件展示测试点

部署/环境
后端运行：Uvicorn

包管理：pip (requirements.txt) / npm (package.json)

🚀 快速开始
环境要求
Python 3.8 或更高版本

Node.js 16 或更高版本

(可选) 若需分析动态渲染页面，需安装 Playwright 浏览器驱动

1. 克隆仓库
bash
git clone https://github.com/yiabn/AItest.git
cd AItest
2. 后端启动
bash
# 进入后端目录 (假设为 backend/)
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000
后端 API 默认地址：http://localhost:8000

3. 前端启动
bash
# 进入前端目录 (假设为 frontend/)
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
前端访问地址：http://localhost:5173

4. 使用示例
打开前端页面，在输入框中粘贴一个游戏活动页面 URL（如某游戏官网的活动页）。

点击“分析并生成测试点”。

等待几秒后，页面将展示生成的测试点列表。

可导出测试点至 Excel 文件。

📁 项目结构（参考）
text
AItest/
├── mygame-knowledge-backend/                # 后端 Python 代码
│   ├── main.py             # FastAPI 主入口
│   ├── api/                # API 路由
│   ├── core/               # 核心逻辑：爬虫、解析、生成器
│   ├── models/             # Pydantic 数据模型
│   ├── utils/              # 工具函数
│   └── requirements.txt
├── mygame-knowledge-frontend/               # 前端 Vue 项目
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面视图
│   │   ├── api/            # Axios 接口封装
│   │   └── assets/         # 静态资源
│   ├── package.json
│   └── vite.config.js
├── docs/                   # 文档、截图等
└── README.md
🤝 如何贡献
我们欢迎任何形式的贡献！如果您想改进这个项目，请：

Fork 本仓库。

创建您的特性分支 (git checkout -b feature/AmazingFeature)。

提交您的改动 (git commit -m 'Add some AmazingFeature')。

推送到分支 (git push origin feature/AmazingFeature)。

打开一个 Pull Request。

📄 许可证
本项目采用 MIT 许可证，详情请参见 LICENSE 文件。

📧 联系
如有任何问题或建议，请通过 Issues 与我们联系。
