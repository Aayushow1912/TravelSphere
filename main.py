import os
from typing import TypedDict, Annotated
import operator
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

# from tools.tavily_tool import tavily_search
# from tools.flight_tool import search_flights

import asyncio

from mcp_client import (
    tavily_mcp_search,
    aviation_mcp_call,
    get_airports,
    get_airlines,
    weather_mcp_search,
    forecast_mcp_search,
    extract_destination
)


from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES_CHECKPOINTER = os.getenv("USE_POSTGRES_CHECKPOINTER", "").lower() in {
    "1",
    "true",
    "yes",
}
CHECKPOINTER_WARNING = ""

llm = ChatGroq(
    model = "llama-3.3-70b-versatile"
)

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int
    weather_results: str

#Flight Agent
# def flight_agent(state: TravelState):
#     query = state["user_query"] 
#     flight_data = search_flights(query)
#     return {
#         "flight_results": flight_data,
#         "messages": [
#             AIMessage(content = f"Flight results fetched")
#         ],
#         "llm_calls" : state.get("llm_calls", 0) + 1
#     }

# Flight Tool Router Prompt
FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""


#Flight Agent
def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }





#Hotel Agent with MCP server
def hotel_agents(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    try:
        raw_hotel_result = asyncio.run(
            tavily_mcp_search(query)
        )

        response = llm.invoke([
            SystemMessage(
                content="You are a travel hotel specialist. Convert raw hotel search data "
                "into concise, traveler-friendly markdown. Do not return JSON, Python lists, "
                "tool payloads, raw dictionaries, or code blocks."
            ),
            HumanMessage(
                content=f"""
                User trip request:
                {state['user_query']}

                Raw hotel search results:
                {str(raw_hotel_result)[:6000]}

                Create a clean hotel recommendation section with:
                - 3 to 5 hotel or area recommendations
                - why each option fits the trip
                - budget/location notes when available
                - booking advice
                """
            )
        ])

        hotel_result = response.content

    except Exception as e:
        hotel_result = f"Hotel recommendations unavailable: {str(e)}"

    return{
        "hotel_results": hotel_result,
        "messages": [
            AIMessage(content = "Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

#Weather Agent
def weather_agent(state: TravelState):

    city = extract_destination(state["user_query"])

    try:
        weather_data = asyncio.run(
            weather_mcp_search(city)
        )

        forecast_data = asyncio.run(
            forecast_mcp_search(city)
        )

        response = llm.invoke([
            SystemMessage(
                content="You are a travel weather advisor. Convert raw weather tool data "
                "into clean, concise markdown for travelers. Do not return JSON, raw "
                "dictionaries, Python lists, tool payloads, or code blocks."
            ),
            HumanMessage(
                content=f"""
                Destination:
                {city}

                User trip request:
                {state['user_query']}

                Current weather raw data:
                {str(weather_data)[:3000]}

                Forecast raw data:
                {str(forecast_data)[:5000]}

                Create a weather section with:
                - current conditions
                - forecast summary
                - what to pack
                - travel timing or activity advice
                """
            )
        ])

        weather_result = response.content

    except Exception as e:
        weather_result = f"Weather information unavailable for {city}: {str(e)}"

    return {
        "weather_results": weather_result,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def itinerary_agent(state: TravelState):

    prompt = f"""
    Create a travel itinerary.
    User Query:
    {state['user_query']}

    Flight Results:
    {state['flight_results']}

    Hotel Results:
    {state['hotel_results']}

    Weather Information:
    {state['weather_results']}

    Budget Constraint:
    Preserve and explicitly summarize any budget or spending limit mentioned in the user query.

    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner. Create a detailed itinerary "
            "that explicitly includes: flight information, hotel recommendations, "
            "weather/forecast details, total budget or budget constraint, and a day-by-day plan. "
            "Do not omit any of these sections."
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


graph = StateGraph(TravelState) #create the graph

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agents)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)


def build_checkpointer():
    global CHECKPOINTER_WARNING

    if not USE_POSTGRES_CHECKPOINTER:
        CHECKPOINTER_WARNING = (
            "Using in-memory LangGraph checkpointing. Set USE_POSTGRES_CHECKPOINTER=true "
            "with a valid DATABASE_URL to enable Postgres checkpointing."
        )
        return MemorySaver()

    if not DATABASE_URL:
        CHECKPOINTER_WARNING = (
            "USE_POSTGRES_CHECKPOINTER is enabled, but DATABASE_URL is not set; "
            "using in-memory LangGraph checkpointing."
        )
        return MemorySaver()

    try:
        import psycopg
        from langgraph.checkpoint.postgres import PostgresSaver

        conn = psycopg.connect(
            DATABASE_URL,
            autocommit=True
        )
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()
        return checkpointer
    except Exception as e:
        CHECKPOINTER_WARNING = f"Postgres checkpointing unavailable; using in-memory checkpointing. Details: {e}"
        return MemorySaver()


app = graph.compile(checkpointer=build_checkpointer())

if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        } 
    }

    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)



