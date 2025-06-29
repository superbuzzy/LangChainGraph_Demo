各种基于LangChain和LangGraph的Demo

"""
使用说明：

1. 安装依赖：
   pip install langchain langgraph langchain-deepseek python-dotenv
   
    Name: langchain
    Version: 0.3.25

    Name: langgraph
    Version: 0.4.9 

    Name: langchain-deepseek
    Version: 0.1.3

    Name: python-dotenv
    Version: 1.1.0

2. 设置环境变量：
   创建.env文件并添加：
   DEEPSEEK_API_KEY=你的apikey

3. 运行示例：
   python multi_agent_example.py


这个示例展示了：
- 多个专门化的AI代理（研究规划、数据收集、分析、报告撰写）
- 使用LangGraph定义代理间的工作流
- 结构化的数据传递和状态管理
- 可扩展的架构设计
"""