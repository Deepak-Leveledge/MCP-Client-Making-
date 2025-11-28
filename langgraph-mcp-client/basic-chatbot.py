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


llm = ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), temperature=0, model="gemini-2.5-flash")


@tool
def calculator_tool(first_number: float,second_number:float,operation:str)->dict:
    """A simple calculator tool that can perform basic arithmetic operations."""
    if operation == "add":
        result = first_number + second_number
    elif operation == "subtract":
        result = first_number - second_number
    elif operation == "multiply":
        result = first_number * second_number
    elif operation == "divide":
        if second_number == 0:
            return {"error": "Division by zero is not allowed."}
        result = first_number / second_number
    else:
        return {"error": f"Unsupported operation: {operation}"}
    
    return {"result": result}

tools = [calculator_tool]

llm_with_tools = llm.bind_tools(tools)

class Chatstate(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
def chat_node(state:Chatstate):
    
    message=  state["messages"]
    respone = llm_with_tools.invoke(message)
    return {"messages":[respone]}


tool_node = ToolNode(tools)

graph = StateGraph(Chatstate)

graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)

graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge("tools","chat_node")

chatbot = graph.compile()

result = chatbot.invoke({"messages":[HumanMessage(content="Tell me a joke and then calculate 15 multiplied by 3 using the calculator tool.")]})

print("Chatbot Response:", result["messages"][-1].content)
