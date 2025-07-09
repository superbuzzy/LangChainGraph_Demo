from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from pathlib import Path

from models import QueryRequest, QueryResponse, UploadResponse, DocumentInfo
from rag_service import SimpleRAGService
from sql_file import DocumentManager

# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# from langgraph.checkpoint.memory import MemorySaver
# memory = MemorySaver()

# http://localhost:8000/docs

app = FastAPI(title="律师事务所RAG系统", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化RAG服务
rag_service = SimpleRAGService()

# 初始化文档管理器
get_all_documents = DocumentManager()


@app.get("/", tags=["首页"], summary="首页", description="这是律师事务所RAG系统API的首页")
async def root():
    return {"message": "律师事务所RAG系统API"}

@app.post("/api/login", tags=["用户管理"], summary="用户登录")
async def login(): 
    pass

@app.post("/api/upload", tags=["文档上传"], response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general")
    ):
    """上传文档"""
    try:
        # 验证文件类型
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="只支持PDF和DOCX文件")
        
        document_id = str(uuid.uuid4())

        suffix = Path(file.filename).suffix
        saved_name = f"{document_id}{suffix}"

        uploads_dir = Path(__file__).parent / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = Path(uploads_dir) / saved_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # print("Saved file exists? ", file_path, file_path.exists())

        try:
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            print(f"文件保存成功: {file_path.exists()}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # 处理文档
        rag_service.process_document(file_path, document_id, file.filename, category)
        
        return UploadResponse(
            filename=file.filename,
            document_id=document_id,
            message="文档上传成功",
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse, tags=["文档对话"])
async def query_documents(request: QueryRequest):
    """文档对话"""
    try:
        result = rag_service.query_documents(request.query)
        print("Query result: ", result)
        return QueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents", response_model=list[DocumentInfo], tags=["获取所有文档"])
async def get_documents():
    """获取所有文档"""
    try:
        documents = get_all_documents.get_all_documents()
        return [DocumentInfo(**doc) for doc in documents]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/documents/{document_id}/download", tags=["文档下载"])
async def download_document(document_id: str):
    pass

@app.get("/api/documents/{document_id}/preview", tags=["文档预览"])
async def preview_document(document_id: str):
    pass


@app.delete("/api/documents/{document_id}", tags=["文档删除"])
async def delete_document(document_id: str):
    """删除文档"""
    try:
        success = get_all_documents.delete_document(document_id)
        if success:
            return {"message": "文档删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# 第一章第八条是什么？

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",reload=True)