from fastapi import APIRouter, Cookie, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.elections import Election
from app.models.voter import Voter
from app.utils.security import decode_token

router = APIRouter(prefix="/candidate", tags=["Candidate"])


def get_current_user(access_token, db):
    if not access_token:
        return None

    payload = decode_token(access_token)
    if not payload:
        return None

    return db.query(Voter).filter(
        Voter.email == payload.get("sub")
    ).first()


@router.post("/apply/{election_id}")
async def apply_candidate(
    election_id: int,
    manifesto: str = Form(...),
    access_token: str = Cookie(default=None),
    db: Session = Depends(get_db)
):

    user = get_current_user(access_token, db)

    if not user:
        return RedirectResponse("/login")

    # 🔒 Vérifier que c’est bien un candidat
    if user.role != "candidate":
        return RedirectResponse("/dashboard")

    # 🔒 Vérifier qu’il n’est pas déjà candidat pour cette élection
    existing = db.query(Candidate).filter(
        Candidate.election_id == election_id,
        Candidate.name == user.full_name
    ).first()

    if existing:
        return RedirectResponse(f"/election/{election_id}")

    # 🔒 Vérifier que l’élection existe
    election = db.query(Election).filter(
        Election.id == election_id
    ).first()

    if not election:
        return RedirectResponse("/dashboard")

    # ✅ Création candidature
    new_candidate = Candidate(
        name=user.full_name,
        manifesto=manifesto,
        election_id=election_id,
    )

    db.add(new_candidate)
    db.commit()

    return RedirectResponse(f"/election/{election_id}", status_code=303)