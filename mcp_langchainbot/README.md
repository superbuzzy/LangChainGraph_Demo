# 多服务器 MCP + LangChain Agent 示例

本项目演示如何通过 MCP（多组件协议）服务器，将多个工具（如天气查询、文件写入等）集成到 LangChain Agent 中，由大模型自动选择和调用，实现智能问答与工具协作。

## 项目结构

- `weather_server.py`：天气查询 MCP 服务器，支持当前天气、天气预报、历史天气、获取当前日期等工具。
- `write_server.py`：文件写入 MCP 服务器，提供本地写文件的工具。
- `servers_config.json`：多服务器配置文件，定义各 MCP 服务器的启动方式。
- `weather_prompt.txt`：天气智能体的系统提示词，指导大模型如何理解和调用天气相关工具。
- `mcp_langchainbot.py`：主入口，基于 LangChain Agent 框架，自动加载 MCP 工具，实现多轮对话与工具调用。
- `client.py`：MCP 多服务器客户端示例，支持 Function Calling 风格的工具调用与对话。

## 快速开始

1. **环境准备**
   - 安装依赖：`pip install -r requirements.txt`
   - 配置 `.env` 文件，填写 `DEEPSEEK_API_KEY` 和 `OPENWEATHER_API_KEY` 等必要参数（OpenWeather必须3.0，绑定支付才可以使用免费功能）。

2. **启动 MCP 服务器**
   - 直接运行 `python weather_server.py` 和 `python write_server.py`，或通过主程序自动管理。

3. **运行主程序**
   - 运行 `python mcp_langchainbot.py`，进入命令行对话模式。
   - 输入你的问题（如“北京明天天气如何？”），Agent 会自动选择合适的工具并返回结果。

4. **多服务器客户端（可选）**
   - 运行 `python client.py`，体验 Function Calling 风格的多服务器工具调用。

## 主要功能

- **多服务器集成**：支持同时连接多个 MCP 服务器，工具统一注册到 Agent。
- **智能工具选择**：大模型根据用户意图自动选择并调用合适的工具。
- **天气智能体**：具备时间推理、日期计算、历史/预报/当前天气查询等能力。
- **可扩展性强**：可按需添加更多 MCP 工具服务器，灵活扩展业务能力。

## 配置说明

- `.env`：存放 API Key 等敏感信息。
- `servers_config.json`：定义 MCP 服务器的启动命令、参数和通信方式（如 stdio）。



## 参考

- [LangChain 官方文档](https://python.langchain.com/)
- [MCP 多组件协议](https://github.com/langchain-ai/mcp)
- [OpenWeather API](https://openweathermap.org/api)

---
如需扩展更多工具，只需实现新的 MCP 服务器并在 `servers_config.json` 中配置即可。

