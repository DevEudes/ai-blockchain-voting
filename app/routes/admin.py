from fastapi import APIRouter, Request, Depends, Cookie, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models.voter import Voter
from app.models.elections import Election
from app.models.candidate import Candidate
from app.utils.security import decode_token, hash_password
from app.services.blockchain_service import generate_wallet_address
from app.services.ai_auth_service import face_auth_service

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")


# ================= UTIL =================

def get_current_user(access_token, db):
    if not access_token:
        return None

    payload = decode_token(access_token)
    if not payload:
        return None

    return db.query(Voter).filter(
        Voter.email == payload.get("sub")
    ).first()


# ================= ADMIN DASHBOARD =================

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(access_token, db)

    if not user or user.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    users = db.query(Voter).all()
    elections = db.query(Election).all()
    candidates = db.query(Candidate).all()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user,
        "users": users,
        "elections": elections,
        "candidates": candidates,
        "active_page": "admin"
    })


# ================= VERIFY USER =================

@router.get("/verify/{user_id}")
async def verify_user(
    user_id: int,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):

    admin = get_current_user(access_token, db)

    if not admin or admin.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    user = db.query(Voter).filter(Voter.id == user_id).first()

    if user:
        user.is_verified = True
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)


# ================= CREATE USER =================

@router.post("/create-user")
async def create_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    image: UploadFile = File(...),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):

    admin = get_current_user(access_token, db)

    if not admin or admin.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    if role not in ["voter", "candidate", "admin"]:
        role = "voter"

    existing = db.query(Voter).filter(Voter.email == email).first()
    if existing:
        return RedirectResponse("/admin/dashboard", status_code=303)

    # Lecture image biométrique
    image_bytes = await image.read()
    embedding = face_auth_service.get_embedding(image_bytes)

    if embedding is None:
        return RedirectResponse("/admin/dashboard", status_code=303)

    embedding_json = json.dumps(embedding.tolist())

    new_user = Voter(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        biometric_embedding=embedding_json,
        wallet_address=generate_wallet_address(),
        role=role,
        is_verified=True  # admin auto-verify
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)


# ================= CREATE ELECTION =================

from datetime import datetime

@router.post("/create-election")
async def create_election(
    title: str = Form(...),
    description: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    candidate_ids: list[int] = Form([]),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):

    admin = get_current_user(access_token, db)

    if not admin or admin.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    # ✅ Conversion string → datetime
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    now = datetime.utcnow()

    election = Election(
        title=title,
        description=description,
        start_date=start_date_obj,
        end_date=end_date_obj,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    db.add(election)
    db.commit()
    db.refresh(election)

    # Ajouter candidats sélectionnés
    for candidate_id in candidate_ids:

        user = db.query(Voter).filter(
            Voter.id == candidate_id,
            Voter.role == "candidate"
        ).first()

        if user:
            new_candidate = Candidate(
                name=user.full_name,
                manifesto="Manifesto pending update",
                election_id=election.id,
                created_at=now,
                updated_at=now
            )
            db.add(new_candidate)

    db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)

@router.get("/delete-user/{user_id}")
async def delete_user(
    user_id: int,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    admin = get_current_user(access_token, db)

    if not admin or admin.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    user = db.query(Voter).filter(Voter.id == user_id).first()

    if user and user.id != admin.id:
        db.delete(user)
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)

@router.post("/edit-user/{user_id}")
async def edit_user(
    user_id: int,
    full_name: str = Form(...),
    role: str = Form(...),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    admin = get_current_user(access_token, db)

    if not admin or admin.role != "admin":
        return RedirectResponse("/dashboard", status_code=303)

    user = db.query(Voter).filter(Voter.id == user_id).first()

    if user:
        user.full_name = full_name
        user.role = role
        user.updated_at = datetime.utcnow()
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=303)