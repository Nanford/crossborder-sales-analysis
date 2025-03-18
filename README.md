# 跨境电商销售数据分析系统

## 项目介绍

跨境电商销售数据分析系统是一款专为跨境电商企业设计的综合性数据分析工具。该系统通过直观的可视化图表和AI辅助分析，帮助企业管理者快速洞察销售趋势、产品表现和市场分布情况，从而做出更加准确的业务决策。

## 主要功能

- **数据导入**：支持Excel和CSV格式销售数据文件上传和自动解析
- **多维度数据展示**：
  - 销售额和销量Top5产品展示
  - 环比上升/下降产品追踪
  - 销售国家分布分析
  - 平台销售渠道分析
  - 销售人员业绩对比
- **交互式图表**：使用ECharts实现多种直观的数据可视化
- **AI智能分析**：基于最新销售数据自动生成业务洞察和建议
- **实时数据筛选**：支持按周期查看和比较销售数据

## 系统架构

- **前端**：React + Ant Design组件库
- **后端**：Python FastAPI框架
- **数据库**：MySQL
- **AI分析**：DeepSeek API

## 安装指南

### 环境要求

- Node.js 14+
- Python 3.8+
- MySQL 5.7+

### 后端安装

##1. 克隆仓库
bash
git clone https://github.com/yourusername/crossborder-sales-analysis.git
cd crossborder-sales-analysis


##2. 创建并激活Python虚拟环境

bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

##3. 安装依赖
bash
pip install -r requirements.txt

##4. 配置数据库
配置MySQL连接信息
编辑 backend/database.py 文件中的数据库连接参数
初始化数据库
mysql -u root -p < init_database.sql
python init_db.py

### 前端安装
bash
cd frontend
npm install

## 运行应用

### 后端服务
bash
cd backend
python main.py
或使用uvicorn
uvicorn main:app --reload

### 前端服务
bash
cd frontend
npm start



访问 http://localhost:3000 查看应用

## 使用指南

1. **数据导入**：点击"数据导入"页面，上传符合格式要求的Excel或CSV文件
2. **查看分析看板**：在"销售看板"页面查看自动生成的数据分析图表
3. **AI分析**：系统会自动根据上传的数据生成AI分析报告，也可点击"重新生成"按钮刷新分析
4. **时间筛选**：使用顶部的周期筛选器选择不同的时间范围查看数据

## 数据格式要求

上传文件需包含以下必要字段：

- **sku** - 产品SKU
- **名称** - 产品名称
- **销量** - 销售数量
- **销售额** - 销售金额
- **买家国家** - 购买者所在国家
- **平台** - 销售平台
- **销售** - 销售人员
- **订单数** - 订单数量
- **毛利率** - 销售毛利率
- **周** - 数据所属周期（"本周"或"上周"）

## 项目结构
crossborder-sales-analysis/
│
├── backend/ # 后端代码
│   ├── main.py # 主应用入口
│   ├── models.py # 数据模型
│   ├── schemas.py # Pydantic模式
│   ├── database.py # 数据库连接
│   ├── ai_service.py # AI分析服务
│   └── uploads/ # 上传文件存储
│
├── frontend/ # 前端代码
│   ├── public/ # 静态资源
│   └── src/ # 源代码
│       ├── App.js # 主应用组件
│       ├── components/ # UI组件
│       │   ├── Dashboard.js # 主看板
│       │   ├── DataImport.js # 数据导入
│       │   └── AIAnalysis.js # AI分析
│       └── index.js # 入口文件
│
└── init_database.sql # 数据库初始化脚本


## 技术栈详情

- **前端**：
  - React (创建用户界面)
  - Ant Design (UI组件库)
  - ECharts (数据可视化图表)
  - Axios (HTTP请求)
  - React Router (路由管理)

- **后端**：
  - FastAPI (API框架)
  - SQLAlchemy (ORM)
  - Pandas (数据处理)
  - Pydantic (数据验证)
  - Uvicorn (ASGI服务器)

## 常见问题解答

1. **如何处理大量数据的上传？**
   系统支持分批上传，建议每次上传不超过5000条记录以获得最佳性能。

2. **AI分析失败怎么办？**
   检查您的网络连接和API密钥配置，或点击"重新生成"按钮重试。系统已配置超时处理，如果AI服务响应时间过长，将自动提供基本分析。

3. **数据导入时字段不匹配怎么办？**
   检查您的Excel文件表头是否符合系统要求，可参考数据导入页面的说明。

## 开发注意事项

1. **AI服务配置**
   - 在`backend/ai_service.py`中配置您的DeepSeek API密钥
   - 可调整`temperature`和`max_tokens`参数以优化AI分析结果

2. **数据库连接**
   - 确保在`database.py`中正确配置MySQL连接信息
   - 首次运行前执行`init_database.sql`创建数据库

3. **前端超时设置**
   - 在`AIAnalysis.js`中已将AI请求超时设置为100秒
   - 后端也配置了异步处理和超时机制，确保系统稳定性

## 许可证

本项目采用 MIT 许可证

## 联系方式

如有问题或建议，请联系：your-email@example.com

---

祝您使用愉快！

