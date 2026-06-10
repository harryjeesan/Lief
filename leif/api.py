import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from leif.routers import common_api, chat_api, agent_api, web_agent_api
from leif.database import init_db

# Load environment variables
load_dotenv()

# Initialize the database
init_db()

# Initialize the FastAPI App
app = FastAPI(title="Leif API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the 3-Tier API architecture routers
app.include_router(common_api.router)
app.include_router(chat_api.router)
app.include_router(agent_api.router)
app.include_router(web_agent_api.router)
