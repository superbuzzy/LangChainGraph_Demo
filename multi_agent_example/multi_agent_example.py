import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chat_models import init_chat_model

from langgraph.graph import Graph, END


load_dotenv() 

# 定义数据结构
class ResearchTopic(BaseModel):
    """研究主题"""
    topic: str = Field(description="研究主题")
    keywords: List[str] = Field(description="关键词列表")
    research_questions: List[str] = Field(description="研究问题列表")

class ResearchData(BaseModel):
    """研究数据"""
    sources: List[str] = Field(description="信息来源")
    key_findings: List[str] = Field(description="关键发现")
    data_quality: str = Field(description="数据质量评估")

class AnalysisResult(BaseModel):
    """分析结果"""
    summary: str = Field(description="分析摘要")
    insights: List[str] = Field(description="关键洞察")
    recommendations: List[str] = Field(description="建议")

class FinalReport(BaseModel):
    """最终报告"""
    title: str = Field(description="报告标题")
    executive_summary: str = Field(description="执行摘要")
    main_findings: List[str] = Field(description="主要发现")
    recommendations: List[str] = Field(description="建议")
    conclusion: str = Field(description="结论")

# 定义状态
class AgentState(BaseModel):
    """多代理状态"""
    original_query: str = ""
    research_topic: ResearchTopic = None
    research_data: ResearchData = None
    analysis_result: AnalysisResult = None
    final_report: FinalReport = None
    messages: List[str] = []

class MultiAgentResearchTeam:
    """多代理研究团队"""
    
    def __init__(self, api_key: str = None):
        """初始化"""
        self.llm = init_chat_model(
        "deepseek:deepseek-chat",
        api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
        temperature=0
    )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Graph:
        """构建工作流图"""
        # 创建图
        workflow = Graph()
        
        # 添加节点
        workflow.add_node("research_planner", self._research_planner_agent)
        workflow.add_node("data_collector", self._data_collector_agent)
        workflow.add_node("data_analyst", self._data_analyst_agent)
        workflow.add_node("report_writer", self._report_writer_agent)
        
        # 定义边（工作流）
        workflow.add_edge("research_planner", "data_collector")
        workflow.add_edge("data_collector", "data_analyst")
        workflow.add_edge("data_analyst", "report_writer")
        workflow.add_edge("report_writer", END)
        
        # 设置入口点
        workflow.set_entry_point("research_planner")
        
        return workflow
    
    def _research_planner_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """研究规划代理 - 负责分析查询并制定研究计划"""
        print("🔍 研究规划代理正在工作...")
        
        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的研究规划师。请根据用户的查询，制定详细的研究计划。
        
        用户查询：{query}
        
        请分析这个查询并提供：
        1. 明确的研究主题
        2. 3-5个相关关键词
        3. 3-5个具体的研究问题
        
        请以JSON格式返回，包含topic、keywords、research_questions字段。
        """)
        
        parser = PydanticOutputParser(pydantic_object=ResearchTopic)
        
        response = self.llm.invoke(
            prompt.format_messages(query=state["original_query"])
        )
        
        try:
            research_topic = parser.parse(response.content)
        except:
            # 如果解析失败，创建默认结构
            research_topic = ResearchTopic(
                topic=state["original_query"],
                keywords=["分析", "研究", "调查"],
                research_questions=[f"关于{state['original_query']}的关键问题有哪些？"]
            )
        
        state["research_topic"] = research_topic
        state["messages"].append(f"研究规划完成：{research_topic.topic}")
        
        return state
    
    def _data_collector_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """数据收集代理 - 负责收集相关信息"""
        print("📊 数据收集代理正在工作...")
        
        research_topic = state["research_topic"]
        
        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的数据收集员。请根据研究主题收集相关信息。
        
        研究主题：{topic}
        关键词：{keywords}
        研究问题：{questions}
        
        请模拟收集数据并提供：
        1. 信息来源列表（3-5个）
        2. 关键发现（3-5个）
        3. 数据质量评估
        
        请以JSON格式返回，包含sources、key_findings、data_quality字段。
        """)
        
        parser = PydanticOutputParser(pydantic_object=ResearchData)
        
        response = self.llm.invoke(
            prompt.format_messages(
                topic=research_topic.topic,
                keywords=", ".join(research_topic.keywords),
                questions=", ".join(research_topic.research_questions)
            )
        )
        
        try:
            research_data = parser.parse(response.content)
        except:
            # 如果解析失败，创建默认结构
            research_data = ResearchData(
                sources=["学术论文", "行业报告", "专家访谈"],
                key_findings=[f"关于{research_topic.topic}的重要发现"],
                data_quality="中等质量"
            )
        
        state["research_data"] = research_data
        state["messages"].append(f"数据收集完成：找到{len(research_data.sources)}个信息源")
        
        return state
    
    def _data_analyst_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """数据分析代理 - 负责分析收集的数据"""
        print("🔬 数据分析代理正在工作...")
        
        research_data = state["research_data"]
        research_topic = state["research_topic"]
        
        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的数据分析师。请分析收集到的研究数据。
        
        研究主题：{topic}
        数据来源：{sources}
        关键发现：{findings}
        
        请进行深入分析并提供：
        1. 分析摘要
        2. 关键洞察（3-5个）
        3. 建议（3-5个）
        
        请以JSON格式返回，包含summary、insights、recommendations字段。
        """)
        
        parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        
        response = self.llm.invoke(
            prompt.format_messages(
                topic=research_topic.topic,
                sources=", ".join(research_data.sources),
                findings=", ".join(research_data.key_findings)
            )
        )
        
        try:
            analysis_result = parser.parse(response.content)
        except:
            # 如果解析失败，创建默认结构
            analysis_result = AnalysisResult(
                summary=f"对{research_topic.topic}的分析结果",
                insights=[f"关于{research_topic.topic}的重要洞察"],
                recommendations=["需要进一步研究"]
            )
        
        state["analysis_result"] = analysis_result
        state["messages"].append("数据分析完成：生成了关键洞察和建议")
        
        return state
    
    def _report_writer_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """报告撰写代理 - 负责撰写最终报告"""
        print("📝 报告撰写代理正在工作...")
        
        research_topic = state["research_topic"]
        analysis_result = state["analysis_result"]
        
        prompt = ChatPromptTemplate.from_template("""
        你是一个专业的中文报告撰写员。请根据研究和分析结果撰写最终报告。
        
        研究主题：{topic}
        分析摘要：{summary}
        关键洞察：{insights}
        建议：{recommendations}
        
        请撰写一份完整的报告，包含：
        1. 报告标题
        2. 执行摘要
        3. 主要发现（3-5个）
        4. 建议（3-5个）
        5. 结论
        
        请以JSON格式返回，包含title、executive_summary、main_findings、recommendations、conclusion字段。
        """)
        
        parser = PydanticOutputParser(pydantic_object=FinalReport)
        
        response = self.llm.invoke(
            prompt.format_messages(
                topic=research_topic.topic,
                summary=analysis_result.summary,
                insights=", ".join(analysis_result.insights),
                recommendations=", ".join(analysis_result.recommendations)
            )
        )
        
        try:
            final_report = parser.parse(response.content)
        except:
            # 如果解析失败，创建默认结构
            final_report = FinalReport(
                title=f"{research_topic.topic}研究报告",
                executive_summary=f"关于{research_topic.topic}的研究报告摘要",
                main_findings=[f"{research_topic.topic}的主要发现"],
                recommendations=analysis_result.recommendations,
                conclusion=f"对{research_topic.topic}的结论"
            )
        
        state["final_report"] = final_report
        state["messages"].append("最终报告撰写完成")
        
        return state
    
    def run_research(self, query: str) -> Dict[str, Any]:
        """运行研究流程"""
        print(f"🚀 开始研究：{query}\n")
        
        # 初始化状态
        initial_state = {
            "original_query": query,
            "research_topic": None,
            "research_data": None,
            "analysis_result": None,
            "final_report": None,
            "messages": []
        }
        
        # 编译并运行图
        app = self.graph.compile()
        result = app.invoke(initial_state)
        
        return result
    
    def print_results(self, result: Dict[str, Any]):
        """打印结果"""
        print("\n" + "="*50)
        print("📋 研究结果")
        print("="*50)
        
        if result.get("final_report"):
            report = result["final_report"]
            print(f"\n📖 标题：{report.title}")
            print(f"\n📄 执行摘要：\n{report.executive_summary}")
            print(f"\n🔍 主要发现：")
            for i, finding in enumerate(report.main_findings, 1):
                print(f"{i}. {finding}")
            print(f"\n💡 建议：")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"{i}. {rec}")
            print(f"\n📝 结论：\n{report.conclusion}")
        
        print(f"\n🔄 处理流程：")
        for i, msg in enumerate(result["messages"], 1):
            print(f"{i}. {msg}")

# 使用示例
def main():
    """主函数"""
    api_key = os.environ["DEEPSEEK_API_KEY"]

    # 创建研究团队
    team = MultiAgentResearchTeam(api_key=api_key)
    
    # 定义研究查询
    query = "人工智能在教育领域的应用前景"
    
    # 运行研究
    result = team.run_research(query)
    
    # 打印结果
    team.print_results(result)

if __name__ == "__main__":
    main()
