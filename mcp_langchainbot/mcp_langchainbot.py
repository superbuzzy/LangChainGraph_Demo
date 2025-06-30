import asyncio
import json
import logging
import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate

from langchain_mcp_adapters.client import MultiServerMCPClient

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "mcp-weather-agent" 

class Configuration:
    """读取 .env 与 servers_config.json"""

    def __init__(self) -> None:
        load_dotenv()
        self.api_key: str = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("❌ 未找到 DEEPSEEK_API_KEY， 请在.env 中配置")

    @staticmethod
    def load_servers(config_path = os.path.join(os.path.dirname(__file__), "servers_config.json")) -> Dict[str, Any]:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f).get("mcpServers", {})

async def run_chat_loop() -> None:
    """启动 MCP-Agent 聊天循环"""

    cfg = Configuration()
    api_key = cfg.api_key

    # 连接多台 MCP 服务器
    servers_cfg = Configuration.load_servers()
    mcp_client = MultiServerMCPClient(servers_cfg)

    tools = await mcp_client.get_tools() 

    logging.info(f"✅ 已加载 {len(tools)} 个 MCP 工具： {[t.name for t in tools]}")

    llm = init_chat_model("deepseek:deepseek-chat",api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),temperature=0)

    # prompt = hub.pull("hwchase17/openai-tools-agent")
    file_path = os.path.join(os.path.dirname(__file__), "weather_prompt.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        print("当前工作目录是：", os.getcwd())
        system_template = f.read()
        f.close()

    prompt = ChatPromptTemplate([
        ("system", system_template),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 4️⃣ CLI 聊天
    print("\n🤖 MCP Agent 已启动，输入 'quit' 退出")
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == "quit":
            break
        try:
            result = await agent_executor.ainvoke({"input": user_input})
            print(f"\nAI: {result['output']}")
        except Exception as exc:
            print(f"\n⚠️  出错: {exc}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(run_chat_loop())
