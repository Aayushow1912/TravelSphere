# Travel with MCP Server

TravelSphere is a Streamlit travel-planning app powered by a LangGraph multi-agent pipeline. It combines flight guidance, hotel search, weather data, and itinerary generation through MCP tools and Groq-hosted LLM calls.

## Agents

- `flight_agent`: builds flight guidance from AviationStack MCP data.
- `hotel_agent`: searches hotels with Tavily MCP and summarizes results into markdown.
- `weather_agent`: fetches current weather and forecast from a local MCP server.
- `itinerary_agent`: combines flight, hotel, weather, and budget context into the final plan.

## Setup

1. Create and activate a Python virtual environment.

```powershell
git submodule update --init --recursive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
pip install -r aviationstack-mcp\requirements.txt
pip install -e aviationstack-mcp
```

3. Copy the environment template and fill in your values.

```powershell
Copy-Item .env.example .env
```

Required variables:

- `AVIATIONSTACK_API_KEY`
- `GROQ_API_KEY`
- `TAVILY_API_KEY`
- `OPENWEATHER_API_KEY`

Optional variables:

- `DATABASE_URL`: Postgres connection string for persistent LangGraph checkpoints.
- `USE_POSTGRES_CHECKPOINTER`: set to `true` only when `DATABASE_URL` is reachable from the app host.
- `AVIATION_MCP_PYTHON`: Python executable used to run the aviation and weather MCP servers.
- `WEATHER_MCP_SCRIPT`: path to `weather_mcp_server.py` if you move it.

## Run

```powershell
streamlit run frontend.py
```

## Notes

- `.env`, virtual environments, caches, and generated `travel_plans/` files are ignored by Git.
- The app uses in-memory LangGraph checkpointing by default. Enable Postgres with `USE_POSTGRES_CHECKPOINTER=true`.
- If you accidentally exposed real API keys before pushing, rotate them before publishing the repository.
