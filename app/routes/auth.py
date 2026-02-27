from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models.voter import Voter
from app.services.ai_auth_service import face_auth_service
from app.services.blockchain_service import generate_wallet_address
from fastapi.responses import RedirectResponse
from app.utils.security import hash_password, create_access_token
from app.core.roles import ROLE_VOTER, ROLE_CANDIDATE

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================= REGISTER =================

@router.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    existing_user = db.query(Voter).filter(Voter.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")


    if role not in [ROLE_VOTER, ROLE_CANDIDATE]:
        role = ROLE_VOTER

    image_bytes = await image.read()
    embedding = face_auth_service.get_embedding(image_bytes)

    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected")

    embedding_json = json.dumps(embedding.tolist())
    wallet_address = generate_wallet_address()

    new_user = Voter(
        full_name=full_name,
        email=email,
        role=role,  # ✅ ajouté proprement
        hashed_password=hash_password(password),
        biometric_embedding=embedding_json,
        wallet_address=wallet_address,
        is_verified=False
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)


# ================= LOGIN =================

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    user = db.query(Voter).filter(Voter.email == email).first()

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "User not found."
        })

    image_bytes = await image.read()
    new_embedding = face_auth_service.get_embedding(image_bytes)

    if new_embedding is None:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "No face detected. Please try again."
        })

    stored_embedding = json.loads(user.biometric_embedding)

    match, similarity = face_auth_service.compare_faces(
        new_embedding,
        stored_embedding
    )

    if not match:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Face not recognized ({similarity:.2f})"
        })

    if not user.is_verified:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Your account is pending admin approval."
        })

    token = create_access_token(data={"sub": user.email})

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response