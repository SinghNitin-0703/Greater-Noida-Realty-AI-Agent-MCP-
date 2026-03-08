from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.tools.sql import SQLTools

from config import DB_PATH, AZURE_DEPLOYMENT, AZURE_API_VERSION
from tools import AzureMapsTools, MarketAnalysisTools

def create_agent(session_id: str, user_id: str) -> Agent:
    db             = SqliteDb(db_file=DB_PATH)
    memory_manager = MemoryManager(db=db)
    azure_maps     = AzureMapsTools()
    analysis       = MarketAnalysisTools(DB_PATH)

    return Agent(
        model=AzureOpenAI(
            id=AZURE_DEPLOYMENT,
            api_version=AZURE_API_VERSION,
            temperature=0,
        ),
        session_id=session_id,
        db=db,
        memory_manager=memory_manager,
        enable_user_memories=True,
        add_history_to_context=True,
        num_history_runs=5,
        tools=[
            azure_maps.find_nearby_amenity,
            analysis.evaluate_deal,
            SQLTools(db_url=f"sqlite:///{DB_PATH}"),
        ],
        instructions=[
            "You are a top-tier Real Estate Broker for Greater Noida. ",
            "Clearly distinguish between Finding Housing, Evaluating Deals, and Finding Amenities.",
            "### GOAL CLASSIFICATION",
            "- GOAL A: FIND HOUSING → keywords: rent, flat, BHK, budget → use SQLTools",
            "- GOAL B: EVALUATE DEAL → keywords: overpriced, good deal, fair price → use evaluate_deal",
            "- GOAL C: FIND AMENITIES → keywords: school, hospital, mall → use find_nearby_amenity",
            "### SQL RULES",
            "- Table: nobroker_cleaned. Columns: apartment_type (INT), society_name (TEXT), Locality (TEXT), rent (INT), area_sqft (INT), link (TEXT).",
            "- NEVER use strict equality for locality names; always use LIKE with wildcards.",
            "- Translate Arabic numerals to Roman: chi 5 → LIKE '%Chi%V%', pi 2 → LIKE '%Pi%II%'.",
            "- For noisy society names use split LIKE: society_name LIKE '%Godrej%' AND society_name LIKE '%Crest%'.",
            "- BHK filter: apartment_type = 2 for 2 BHK.",
            "### RESPONSE FORMAT",
            "- Housing: Markdown table with columns Society | Locality | BHK | Rent | Area | Link.",
            "- Amenities: Bullet list with name and distance.",
            "- Deal: Bold the exact string returned by evaluate_deal.",
            "### MEMORY",
            "Apply remembered budget / BHK / locality constraints automatically in SQL queries.",
        ],
        markdown=True,
        debug_mode=False,
    )