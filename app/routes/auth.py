from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import json
import numpy as np

from app.database import get_db
from app.models.voter import Voter
from app.services.ai_auth_service import face_auth_service
from app.services.blockchain_service import generate_wallet_address
from app.utils.security import hash_password, create_access_token
from app.core.roles import ROLE_VOTER, ROLE_CANDIDATE

router = APIRouter(prefix="/auth", tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")


# ================= HELPERS =================

def _find_duplicate_face(embedding, db: Session, exclude_email: str = None, threshold=0.6):
    """
    Compare embedding against all stored faces.
    Returns (voter, similarity) if a match is found, else (None, 0).
    """
    query = db.query(Voter).filter(Voter.biometric_embedding.isnot(None))
    if exclude_email:
        query = query.filter(Voter.email != exclude_email)

    for voter in query.all():
        stored = json.loads(voter.biometric_embedding)
        match, similarity = face_auth_service.compare_faces(embedding, stored, threshold)
        if match:
            return voter, similarity
    return None, 0.0


def _identify_face(embedding, db: Session, threshold=0.6):
    """
    Search ALL verified users to find the best matching face.
    Returns (voter, similarity) of the best match above threshold, else (None, 0).
    """
    voters = db.query(Voter).filter(
        Voter.biometric_embedding.isnot(None)
    ).all()

    best_voter = None
    best_sim   = 0.0

    emb = np.array(embedding)

    for voter in voters:
        stored = json.loads(voter.biometric_embedding)
        _, similarity = face_auth_service.compare_faces(emb, stored)
        if similarity > best_sim:
            best_sim   = similarity
            best_voter = voter

    if best_sim > threshold and best_voter:
        return best_voter, best_sim

    return None, best_sim


# ================= REGISTER =================

@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    def error(msg: str):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": msg
        })

    existing_user = db.query(Voter).filter(Voter.email == email).first()
    if existing_user:
        return error("This email is already registered.")

    if role not in [ROLE_VOTER, ROLE_CANDIDATE]:
        role = ROLE_VOTER

    image_bytes = await image.read()
    embedding = face_auth_service.get_embedding(image_bytes)

    if embedding is None:
        return error("No face detected in the capture. Please retry in good lighting.")

    # Check for duplicate face across all existing users
    dup_voter, _ = _find_duplicate_face(embedding, db)
    if dup_voter:
        return error(
            "This face is already registered under another account. "
            "Each person can only have one account."
        )

    embedding_json = json.dumps(embedding.tolist())
    wallet_address = generate_wallet_address()

    new_user = Voter(
        full_name=full_name,
        email=email,
        role=role,
        hashed_password=hash_password(password),
        biometric_embedding=embedding_json,
        wallet_address=wallet_address,
        is_verified=False
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)


# ================= FACE SCAN (FaceID-style — face only) =================

@router.post("/face-scan")
async def face_scan(
    frame: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Called repeatedly by the JS scanner (~every 1.5s).
    Compares the face against ALL users — no email needed.
    Returns JSON.

    Status values:
      "no_face"      — no face in this frame (keep scanning)
      "scanning"     — face found but no match yet (keep scanning)
      "not_verified" — matched but account pending (hard stop)
      "success"      — matched, cookie set, redirect
    """
    image_bytes = await frame.read()
    new_embedding = face_auth_service.get_embedding(image_bytes)

    if new_embedding is None:
        return JSONResponse({"status": "no_face", "message": "Position your face in the frame"})

    # Search across all users for the best match
    voter, similarity = _identify_face(new_embedding, db)

    if not voter:
        return JSONResponse({
            "status": "scanning",
            "message": f"Scanning... ({similarity:.0%})",
            "similarity": round(similarity, 3)
        })

    if not voter.is_verified:
        return JSONResponse({
            "status": "not_verified",
            "message": "Account pending admin approval."
        })

    # Match — set auth cookie
    token = create_access_token(data={"sub": voter.email})
    response = JSONResponse({
        "status": "success",
        "message": "Identity verified",
        "redirect": "/dashboard",
        "user_name": voter.full_name
    })
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


# ================= LOGOUT =================

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
