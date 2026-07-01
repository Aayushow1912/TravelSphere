import os
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_AVIATION_MCP_PYTHON = BASE_DIR / "aviationstack-mcp" / ".venv" / "Scripts" / "python.exe"

TAVILY_API_KEY = (os.getenv("TAVILY_API_KEY") or os.getenv("TAVLIY_API_KEY") or "").strip()
AVIATIONSTACK_API_KEY = (os.getenv("AVIATIONSTACK_API_KEY") or "").strip()
OPENWEATHER_API_KEY = (os.getenv("OPENWEATHER_API_KEY") or "").strip()
AVIATION_MCP_PYTHON = os.getenv(
    "AVIATION_MCP_PYTHON",
    str(DEFAULT_AVIATION_MCP_PYTHON if DEFAULT_AVIATION_MCP_PYTHON.exists() else sys.executable)
)
WEATHER_MCP_SCRIPT = os.getenv("WEATHER_MCP_SCRIPT", str(BASE_DIR / "weather_mcp_server.py"))

client = MultiServerMCPClient(
     {
         "tavily": {
             "transport": "streamable_http",
             "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
         },

         "aviationstack": {
            "transport": "stdio",
            "command": AVIATION_MCP_PYTHON,
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run"
            ], 
            "env": {
                "AVIATIONSTACK_API_KEY": AVIATIONSTACK_API_KEY
            }
        },

         "weather": {
            "transport": "stdio",
            "command": AVIATION_MCP_PYTHON,
            "args": [
                WEATHER_MCP_SCRIPT
            ],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }
     }
)

# async def main():
#    tools = await client.get_tools()
#    print("\nAvailable MCP Tools:\n")
#    for tool in tools:
#       print(tool.name)


# async def main():
#     tools = await client.get_tools()
#     print("\nAvailable MCP Tools:\n")
#     search_tool = next(
#         tool
#         for tool in tools
#         if tool.name == "tavily_search"
#     )
#     result = await search_tool.ainvoke(
#         {
#         "query": "Best hotels in Gurgaon"
#         }
#     )
#     print(result)

# asyncio.run(main())

# search_tool = None

# async def initialize_mcp():

#     """
#     Connect to MCP Server and discover tools once.
#     """

#     global search_tool

#     if search_tool is not None:
#         return
    
#     tools = await client.get_tools()

#     print("\nAvaiable MCP Tools")

#     for tool in tools:
#         print(tool.name)

#     search_tool = next(
#         tool
#         for tool in tools
#         if tool.name == "tavily_search"
#     )    

search_tool = None
aviation_tool = {}

async def initialize_mcp():
    global search_tool
    global aviation_tool

    if search_tool is not None and aviation_tool:
        return
    
    tools = await client.get_tools()

    print("\nAvaiable MCP Tools:\n")

    for tool in tools:
        print(tool.name)

    search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

    aviation_tool = {
        tool.name: tool
        for tool in tools
        if tool.name != "tavily_search"
    }


async def tavily_mcp_search(query: str):
    await initialize_mcp()
    result = await search_tool.ainvoke(
        {
            "query": query
        }
    )
    return result


async def aviation_mcp_call( 
        tool_name: str,
        tool_args: dict = None
):
    tools = await client.get_tools()

    tool = next(
        t for t in tools
        if t.name == tool_name
    )
    
    result = await tool.ainvoke(
        tool_args or {}
    )

    return result


async def get_airports():
    await initialize_mcp()
    tool =  aviation_tool.get("list_airports")
    if not tool:
        return "Airport tool unavailable"
    result = await tool.ainvoke({})
    return result


async def get_airlines():
    await initialize_mcp()
    tool = aviation_tool.get("list_airlines")
    if not tool:
        return "Airline tool unavailable"
    result = await tool.ainvoke()
    return result

 
weather_tool = None
forecast_tool = None


async def initialize_weather_tools():

    global weather_tool, forecast_tool

    if weather_tool is not None:
        return

    tools = await client.get_tools()

    weather_tool = next(
        t for t in tools
        if t.name == "get_current_weather"
    )

    forecast_tool = next(
        t for t in tools
        if t.name == "get_forecast"
    )


async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    return await weather_tool.ainvoke(
        {
            "city": city
        }
    )


async def forecast_mcp_search(city: str):

    await initialize_weather_tools()

    return await forecast_tool.ainvoke(
        {
            "city": city
        }
    )


from langchain_groq import ChatGroq

# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

###################################
# Destination Extractor
###################################

def extract_destination(query: str):

    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()


if __name__ == "__main__":
   asyncio.run(main())
   
