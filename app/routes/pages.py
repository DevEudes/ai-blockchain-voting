from fastapi import APIRouter, Request, Depends, Cookie, Form, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.voter import Voter
from app.models.elections import Election
from app.models.candidate import Candidate
from app.models.logs import VoteLog
from app.utils.security import decode_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_current_user(access_token, db):
    if not access_token:
        return None

    payload = decode_token(access_token)
    if not payload:
        return None

    return db.query(Voter).filter(
        Voter.email == payload.get("sub")
    ).first()

def require_admin(user):
    return user and user.role == "admin"


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    access_token: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not access_token:
        return templates.TemplateResponse("login.html", {"request": request})

    payload = decode_token(access_token)
    if not payload:
        return templates.TemplateResponse("login.html", {"request": request})

    email = payload.get("sub")
    user = db.query(Voter).filter(Voter.email == email).first()

    if not user:
        return templates.TemplateResponse("login.html", {"request": request})

    elections = db.query(Election).all()

    # Vérifier candidatures utilisateur
    user_candidates = db.query(Candidate).filter(
        Candidate.name == user.full_name
    ).all()

    user_candidate_election_ids = [
        c.election_id for c in user_candidates
    ]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "elections": elections,
        "user_candidate_election_ids": user_candidate_election_ids,
        "active_page": "dashboard"
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    access_token: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not access_token:
        return RedirectResponse("/login")

    payload = decode_token(access_token)
    if not payload:
        return RedirectResponse("/login")

    email = payload.get("sub")
    user = db.query(Voter).filter(Voter.email == email).first()

    if not user:
        return RedirectResponse("/login")

    elections = db.query(Election).all()

    # Vérifier candidatures utilisateur
    user_candidates = db.query(Candidate).filter(
        Candidate.name == user.full_name
    ).all()

    user_candidate_election_ids = [
        c.election_id for c in user_candidates
    ]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "elections": elections,
        "user_candidate_election_ids": user_candidate_election_ids
    })

@router.get("/elections", response_class=HTMLResponse)
async def elections_page(request: Request,
                        access_token: str = Cookie(default=None),
                        db: Session = Depends(get_db)):

    user = get_current_user(access_token, db)
    if not user:
        return RedirectResponse("/login")

    elections = db.query(Election).all()

    user_candidates = db.query(Candidate).filter(
        Candidate.name == user.full_name
    ).all()

    user_candidate_election_ids = [
        c.election_id for c in user_candidates
    ]

    for election in elections:
        is_already_candidate = db.query(Candidate).filter(
            Candidate.election_id == election.id,
            Candidate.name == user.full_name
        ).first()

    election.is_candidate = True if is_already_candidate else False

    return templates.TemplateResponse("elections.html", {
        "request": request,
        "user": user,
        "elections": elections,
        "user_candidate_election_ids": user_candidate_election_ids,
        "active_page": "elections"
    })


@router.get("/election/{election_id}", response_class=HTMLResponse)
async def election_detail(election_id: int,
                        request: Request,
                        access_token: str = Cookie(default=None),
                        db: Session = Depends(get_db)):

    user = get_current_user(access_token, db)
    if not user:
        return RedirectResponse("/login")

    election = db.query(Election).filter(Election.id == election_id).first()
    candidates = db.query(Candidate).filter(Candidate.election_id == election_id).all()

    votes = db.query(VoteLog).filter(
        VoteLog.election_id == election_id
    ).all()

    total_votes = len(votes)

    for candidate in candidates:
        candidate_votes = len([
            v for v in votes if v.candidate_id == candidate.id
        ])
        if total_votes > 0:
            candidate.vote_percentage = round(
                (candidate_votes / total_votes) * 100, 2
            )
        else:
            candidate.vote_percentage = 0

    return templates.TemplateResponse("election_detail.html", {
        "request": request,
        "user": user,
        "election": election,
        "candidates": candidates,
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request,
                access_token: str = Cookie(default=None),
                db: Session = Depends(get_db)):

    user = get_current_user(access_token, db)
    if not user:
        return RedirectResponse("/login")

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "active_page": "profile"
    })


@router.get("/history", response_class=HTMLResponse)
async def history(request: Request,
                access_token: str = Cookie(default=None),
                db: Session = Depends(get_db)):

    user = get_current_user(access_token, db)
    if not user:
        return RedirectResponse("/login")

    votes = db.query(VoteLog).filter(VoteLog.voter_id == user.id).all()

    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": user,
        "votes": votes,
        "active_page": "history"
    })

# @router.post("/candidate/apply/{election_id}")
# async def apply_candidate(election_id: int,
#                             access_token: str = Cookie(None),
#                             db: Session = Depends(get_db)):

#     user = get_current_user(access_token, db)

#     if user.role != "candidate":
#         return RedirectResponse("/")

#     candidate = Candidate(
#         name=user.full_name,
#         manifesto="Pending manifesto",
#         election_id=election_id
#     )

#     db.add(candidate)
#     db.commit()

#     return RedirectResponse(f"/election/{election_id}")

# router = APIRouter(prefix="/admin")

# @router.get("/dashboard")
# async def admin_dashboard(request: Request,
#                             access_token: str = Cookie(None),
#                             db: Session = Depends(get_db)):

#     user = get_current_user(access_token, db)

#     if not user or user.role != "admin":
#         return RedirectResponse("/")

#     voters = db.query(Voter).all()
#     elections = db.query(Election).all()

#     return templates.TemplateResponse("admin_dashboard.html", {
#         "request": request,
#         "voters": voters,
#         "elections": elections
#     })
    
# @router.get("/verify/{user_id}")
# async def verify_user(user_id: int,
#                         access_token: str = Cookie(None),
#                         db: Session = Depends(get_db)):

#     admin = get_current_user(access_token, db)

#     if admin.role != "admin":
#         return RedirectResponse("/")

#     user = db.query(Voter).filter(Voter.id == user_id).first()
#     user.is_verified = True

#     db.commit()

#     return RedirectResponse("/admin/dashboard")

# @router.post("/create-election")
# async def create_election(
#     title: str = Form(...),
#     description: str = Form(...),
#     db: Session = Depends(get_db),
#     access_token: str = Cookie(None)
# ):

#     admin = get_current_user(access_token, db)

#     if admin.role != "admin":
#         return RedirectResponse("/")

#     election = Election(
#         title=title,
#         description=description,
#         is_active=True
#     )

#     db.add(election)
#     db.commit()

#     return RedirectResponse("/admin/dashboard")