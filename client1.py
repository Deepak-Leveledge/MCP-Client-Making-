import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.messages import ToolMessage
import json

SERVERS ={
    "Simple Calculator remote server":{
        "transport":"stdio",
        "command": "C:\\Users\\zezos\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\uv.exe",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "C:\\Users\\zezos\\Desktop\\demo-remote-mcp-server\\main.py"
      ],
    },
    "Expenses Tracker": {
        "transport":"streamable_http",
        "url": "https://deepak-expenses-tracker-mcp.fastmcp.app/mcp",
    },
    "manim-server": {
        "transport":"stdio",
      "command": "C:\\Users\\zezos\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": [
        "C:\\Users\\zezos\\Desktop\\manim-mcp-server\\src\\manim_server.py"
      ],
      "env": {
        "MANIM_EXECUTABLE": "C:\\Users\\zezos\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\manim.exe"
      }
    }
    # "Demo Server": {
    # "transport":"stdio",
    #   "command": "C:\\Users\\zezos\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\uv.exe",
    #   "args": [
    #     "run",
    #     "--with",
    #     "fastmcp",
    #     "fastmcp",
    #     "run",
    #     "C:\\Users\\zezos\\Desktop\\demo-mcp-server\\main.py"
    #   ],
    #   "env": {}
    # }
}
async def main():
    print("Starting Multi-Server MCP Client...")

    client = MultiServerMCPClient(SERVERS)
    tools= await client.get_tools()
    # print(tools)
    
    name_tools={}
    for tool in tools:
        name_tools[tool.name]=tool
    print("avalaible tools:",name_tools.keys())
    
    
    llm = ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), temperature=0, model="gemini-2.5-flash", max_retries=3)
    llm_with_tools = llm.bind_tools(tools)
    # prompt = "Calculate the sum of 123 and 456 using the Simple Calculator remote server."
    prompt = "Draw a triangle rotating in place using the manim tool."
    
    
    response =await llm_with_tools.ainvoke(prompt)
    if not getattr(response, "tool_calls", None):
        print("LLM Reply:", response.content)
        return
    
    
    tool_messages =[]
    for each_tool in response.tool_calls:
        # if you have multiple tools and severel tool calls
        selected_tool = each_tool["name"]
        seleccted_args = each_tool.get("args") or {}
        selected_id = each_tool["id"]
        
    # print("Initial Response:", response)
    # for signle tool if you have only one 
    # selected_tool = response.tool_calls[0]["name"]
    # seleccted_args = response.tool_calls[0]["args"]
    # selected_id = response.tool_calls[0]["id"]
    # print("Response:", response)
    
    # print(f"Selected Tool: {selected_tool}")
    # print(f"Selected Args: {seleccted_args}")    
    # print(f"Selected ID: {selected_id}")
    
    tool_result = await name_tools[selected_tool].ainvoke(seleccted_args)
    print(f"Tool Result: {tool_result}")
    tool_messages.append(ToolMessage(tool_call_id=selected_id,content=json.dumps(tool_result)))
    print("Tool Message:", tool_messages)
    
    final_response= await llm_with_tools.ainvoke([prompt,response,*tool_messages])
    print("Final Response:", final_response.content)
    
    
    
    
    
    
    
if __name__ == "__main__":
    asyncio.run(main())