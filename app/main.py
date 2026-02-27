from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import models (important pour SQLAlchemy)
from app.models.voter import Voter
from app.models.logs import VoteLog, FraudAlert
from app.models.elections import Election
from app.models.candidate import Candidate
from app.routes import auth, pages, vote, candidate, admin

app = FastAPI(title="AI Blockchain Voting System")

# Static & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(vote.router)
app.include_router(candidate.router)
app.include_router(admin.router)