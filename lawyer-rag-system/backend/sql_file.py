import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict
import json
from pathlib import Path

class DocumentManager:

    def __init__(self, db_path: str = None):
        """初始化文档管理器"""
        if db_path is None:
            db_path = Path(__file__).parent / "db_file/documents.db"
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        os.makedirs(self.db_path.parent, exist_ok=True)

        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建文档表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT,
                    category TEXT,
                    upload_time TEXT,
                    status TEXT
                );
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_category ON documents(category)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON documents(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_upload_time ON documents(upload_time)
            ''')
            
            conn.commit()
    
    def save_document(self, document_id: str, 
                        filename: str, 
                        category: str = "general", 
                        upload_time: str = None, 
                        status: str = None) -> bool:
        """保存文档信息到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO documents 
                    (document_id, filename, category, upload_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    document_id, filename, category, upload_time, status
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"保存文档信息时出错: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """获取单个文档信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM documents WHERE document_id = ?
                ''', (document_id,))
                
                row = cursor.fetchone()
                if row:
                    doc = dict(row)
                    # 解析 metadata JSON
                    if doc['metadata']:
                        doc['metadata'] = json.loads(doc['metadata'])
                    return doc
                return None
                
        except Exception as e:
            print(f"获取文档信息时出错: {e}")
            return None
    
    def get_all_documents(self, category: str = None, status: str = None) -> List[Dict]:
        """获取所有文档信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建查询条件
                query = "SELECT document_id, filename, category, upload_time, status FROM documents"
                conditions = []
                params = []
                
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # 按上传时间降序排列（最新的在前）
                query += " ORDER BY upload_time DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    doc = {
                        'document_id': row['document_id'],
                        'filename': row['filename'],
                        'category': row['category'],
                        'upload_time': row['upload_time'],
                        'status': row['status']
                    }
                    documents.append(doc)
                
                return documents
        
        except Exception as e:
            print(f"获取文档列表时出错: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM documents WHERE document_id = ?
                ''', (document_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"删除文档记录时出错: {e}")
            return False
    
    def get_documents_by_document_id(self, document_id: str) -> List[Dict]:
        """根据document_id获取文档"""
        return self.get_all_documents(document_id=document_id)
        
    def get_documents_by_filename(self, filename: str) -> List[Dict]:
        """根据文件名获取文档"""
        return self.get_all_documents(filename=filename)
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """根据类别获取文档"""
        return self.get_all_documents(category=category)
    
    def get_documents_by_upload_time(self, upload_time: str) -> List[Dict]:
        """根据时间获取文档"""
        return self.get_all_documents(upload_time=upload_time)