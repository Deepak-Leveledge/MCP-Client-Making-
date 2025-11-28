from langgraph.graph import StateGraph,START
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict,Annotated
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import tool
import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


llm = ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), temperature=0, model="gemini-2.5-flash")

client = MultiServerMCPClient({
    "Simple Calculator remote server": {
        "transport": "stdio",
        "command": "C:\\Users\\zezos\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\uv.exe",
        "args": [
            "run",
            "--with",
            "fastmcp",
            "fastmcp",
            "run",
            "C:\\Users\\zezos\\Desktop\\demo-remote-mcp-server\\main.py"
        ],
    }
})


# @tool
# def calculator_tool(first_number: float,second_number:float,operation:str)->dict:
#     """A simple calculator tool that can perform basic arithmetic operations."""
#     if operation == "add":
#         result = first_number + second_number
#     elif operation == "subtract":
#         result = first_number - second_number
#     elif operation == "multiply":
#         result = first_number * second_number
#     elif operation == "divide":
#         if second_number == 0:
#             return {"error": "Division by zero is not allowed."}
#         result = first_number / second_number
#     else:
#         return {"error": f"Unsupported operation: {operation}"}
    
#     return {"result": result}





# state definition
class Chatstate(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
async def Build_graph():
    
    tools = await client.get_tools()
    print("Retrieved tools from MCP server:", [tool.name for tool in tools])

    llm_with_tools = llm.bind_tools(tools)
    
    async def chat_node(state: Chatstate):
        
        message = state["messages"]
        response = await llm_with_tools.ainvoke(message)
        return {"messages": [response]}


    tool_node = ToolNode(tools)

    graph = StateGraph(Chatstate)

    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile()

    return chatbot

async def main():
    
    chatbot = await Build_graph()
    result = await chatbot.ainvoke({"messages":[HumanMessage(content="Tell me a joke and then calculate 15 multiplied by 3 .")]})

    print("Chatbot Response:", result["messages"][-1].content)

    
if __name__ == "__main__":
    asyncio.run(main())