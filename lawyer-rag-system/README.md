# 律师事务所RAG系统

本项目是一个基于LangChain、FastAPI、Chroma等技术栈实现的法律文档智能问答与管理系统，支持文档上传、分块、向量化检索、智能问答、文档管理等功能，适用于律师事务所等法律行业场景。

## 目录结构
```
<!--
lawyer-rag-system/         # 项目根目录
├── README.md              # 项目说明文档
├── requirements.txt       # Python依赖包列表
├── backend/               # 后端代码目录
│   ├── main.py            # 后端主程序入口
│   ├── models.py          # 数据模型定义
│   ├── rag_service.py     # RAG相关服务逻辑
│   ├── sql_file.py        # SQL数据库操作相关代码
│   ├── chroma_db/         # Chroma向量数据库目录
│   │   └── chroma.sqlite3 # Chroma数据库文件
│   ├── db_file/           # 其他数据库文件目录
│   │   └── documents.db   # 文档数据库文件
│   └── uploads/           # 上传文档存储目录
│       └── ...（上传的文档） # 用户上传的原始文档
├── frontend/              # 前端代码目录
│   ├── index.html         # 前端入口HTML文件
│   ├── package.json       # 前端依赖及脚本配置
│   ├── tailwind.config.js # Tailwind CSS配置文件
│   ├── vite.config.js     # Vite构建工具配置
│   ├── public/            # 前端静态资源目录
│   └── src/               # 前端源码目录
│       └── ...（前端源码） # 具体前端实现代码
-->

```

## 功能简介

### 1. 文档上传与管理

- 支持PDF、DOCX文档上传（`/api/upload`）。
- 文档上传后自动分块、向量化，并存入Chroma向量数据库。
- 文档元数据（ID、文件名、类别、上传时间、状态）存储于SQLite数据库。
- 支持按类别、状态、上传时间等条件查询文档列表（`/api/documents`）。
- 支持文档删除（`/api/documents/{document_id}`）。

### 2. 智能问答（RAG）

- 基于LangChain和本地大模型（如Qwen3）实现法律文档智能问答（`/api/query`）。
- 检索相关文档片段，结合用户问题生成专业法律答复。
- 返回答案及引用的文档来源信息。

### 3. 文档下载与预览（接口预留）

- `/api/documents/{document_id}/download`：文档下载（待实现）。
- `/api/documents/{document_id}/preview`：文档预览（待实现）。

### 4. 用户管理（接口预留）

- `/api/login`：用户登录（待实现）。

## 技术栈

- **后端**：FastAPI、LangChain、Chroma、SQLite
- **前端**：React + Vite + TailwindCSS
- **向量检索**：Chroma
- **大模型**：HuggingFace Embeddings、Ollama Qwen3
- **文档处理**：PyPDFLoader、Docx2txtLoader

## 主要后端模块说明

### `backend/main.py`

- FastAPI应用主入口，定义所有API接口。
- 集成CORS，适配前后端分离开发。
- 初始化RAG服务与文档管理器。

### `backend/rag_service.py`

- `SimpleRAGService`类：负责文档分块、向量化、检索、问答。
- 支持文档处理（分块、embedding、入库）与智能问答（检索+生成）。
- 采用HuggingFace Embeddings和Chroma向量数据库。

### `backend/sql_file.py`

- `DocumentManager`类：负责文档元数据的SQLite存储与管理。
- 支持文档的增、删、查、条件筛选等操作。

### `backend/models.py`

- 定义API请求与响应的数据结构（Pydantic模型）。

## 快速开始

### 1. 安装依赖

后端依赖（建议使用Python 3.10+）：

```bash
cd backend
pip install -r requirements.txt
```

前端依赖：

```bash
cd frontend
npm install
```

### 2. 启动后端服务

```bash
cd backend
python main.py
```

### 3. 启动前端服务

```bash
cd frontend
npm run dev
```

### 4. 访问

- 前端开发环境默认：http://localhost:3000
- 后端API文档：http://localhost:8000/docs

## 主要API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传文档（PDF/DOCX） |
| POST | `/api/query` | 智能问答 |
| GET  | `/api/documents` | 获取所有文档信息 |
| DELETE | `/api/documents/{document_id}` | 删除文档 |
| GET  | `/api/documents/{document_id}/download` | 下载文档（预留） |
| GET  | `/api/documents/{document_id}/preview` | 预览文档（预留） |

## 注意事项

- 上传文档仅支持PDF和DOCX格式。
- 向量数据库和文档数据库默认存储于`backend/chroma_db`和`backend/db_file`目录下。
- 需配置本地大模型（如Ollama Qwen3）和CUDA环境以获得最佳性能。

## 参考

- [LangChain](https://github.com/langchain-ai/langchain)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Chroma](https://www.trychroma.com/)
- [React](https://react.dev/)

## 贡献与许可

本项目仅供学习与研究使用，禁止用于商业用途。如有建议或问题，欢迎提交Issue。
