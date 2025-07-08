from datetime import datetime
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma   # from langchain_chroma import Chrom
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model

from sql_file import DocumentManager


class SimpleRAGService:
    def __init__(self):
        # 初始化embedding模型
        self.embed_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={'device': 'cuda'}  
        )
         # 初始化llm模型
        self.llm = init_chat_model("ollama:qwen3:1.7b", temperature=0)

        # 清空已有的向量数据库（仅用于测试）
        import shutil
        shutil.rmtree("./chroma_db", ignore_errors=True)

        # 初始化向量数据库
        self.vector_db = Chroma(
            collection_name="lawyer_documents",
            embedding_function=self.embed_model,
            persist_directory="./chroma_db"
        )
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "],
            keep_separator = "end"
        )
        
        # 简单的文档存储，后续接入数据库
        self.documents = {}

        # 初始化文档管理器
        self.save_document = DocumentManager().save_document
    
    def process_document(self, file_path: str, document_id : str, filename: str, category: str = "general") -> str:
        """处理上传的文档"""
        try:
            # document_id = str(uuid.uuid4())

            file_path_str = str(file_path)
            
            # 根据文件类型加载文档
            if file_path_str.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path_str.endswith('.docx'):
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError("不支持的文件格式")
            
            
            # 加载并分割文档
            documents = loader.load()
            texts = self.text_splitter.split_documents(documents)
            
            # 为每个文本块添加元数据
            for i, text in enumerate(texts):
                text.metadata.update({
                    "document_id": document_id,
                    "filename": filename,
                    "category": category,
                    "chunk_index": i,
                    "upload_time": datetime.now().isoformat()
                })

            # 添加到向量数据库
            self.vector_db.add_documents(texts)
            
            # 保存文档信息到内存
            self.documents[document_id] = {
                "document_id": document_id,
                "filename": filename,
                "category": category,
                "upload_time": datetime.now().isoformat(),
                "status": "completed"
            }

            # 保存文档信息到数据库
            success = self.save_document(
                    document_id=document_id,
                    filename=filename,
                    category=category,
                    upload_time=datetime.now().isoformat(),
                    status="completed"
                )
            if not success:
                print(f"❌ 保存文档到数据库失败：{filename}（ID: {document_id}）")
            else:
                print(f"✅ 保存文档到数据库成功：{filename}（ID: {document_id}）")

            return document_id
            
        except Exception as e:
            raise Exception(f"文档处理失败: {str(e)}")
    
    def query_documents(self, query: str, k: int = 3) -> Dict[str, Any]:
        """文档问答"""
        try:
            # 检索相关文档
            # relevant_docs = self.vector_db.similarity_search_with_score(query, k=k)
            relevant_docs = self.vector_db.similarity_search(query , k = k)
            source_knowledge = "\n".join([x.page_content for x in relevant_docs])

            # 构建prompt
            prompt = ChatPromptTemplate.from_template( """
                你是一名专业的法律助理。请结合以下法律文献片段（source_knowledge）和用户问题（query），运用严谨的法律推理方法给出回答。如果你不知道就说不知道。

                以下是相关文献片段：
                {source_knowledge}

                用户问题:
                {query}

                请按照以下格式输出：

                <analysis>
                1. 法律问题识别：简要梳理用户的法律需求与争议焦点  
                2. 法律条文与判例引证：说明检索到的相关法律条文、司法解释或判例，并注明来源编号  
                3. 推理过程：结合上下文资料和法律原则，逐步论证如何得出结论  
                </analysis>

                <conclusion>
                - 法律结论：依据何种法律依据、原则或案例作何判定  
                - 风险提示：如有必要，指出潜在风险或后续注意事项  
                - 建议步骤：如需进一步操作（起草文书、申请诉讼等），给出简要建议  
                </conclusion>

            """)

            # 构建chain
            chain = prompt | self.llm | StrOutputParser()

            # 生成回答
            response = chain.invoke({
                "source_knowledge": source_knowledge,
                "query": query
            })   

            # 整理来源信息
            sources = []
            for doc in relevant_docs:
                sources.append({
                    "document_id": doc.metadata.get('document_id'),
                    "filename": doc.metadata.get('filename', '未知文档'),
                    "category": doc.metadata.get('category', 'general'),
                    "preview": doc.page_content[:100] + "..."
                })
            
            return {
                "answer": response,
                "sources": sources
            }
        except Exception as e:
            raise Exception(f"查询失败: {str(e)}")
    