from fastapi import APIRouter, Depends, Cookie, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import hashlib
import uuid

from app.database import get_db
from app.models.logs import VoteLog
from app.models.voter import Voter
from app.utils.security import decode_token
from app.services.blockchain_service import record_vote_on_blockchain

router = APIRouter(prefix="/vote")


# =========================
# HELPER
# =========================

def get_current_user(access_token, db):
    if not access_token:
        return None

    payload = decode_token(access_token)
    if not payload:
        return None

    return db.query(Voter).filter(
        Voter.email == payload.get("sub")
    ).first()


# =========================
# CAST VOTE
# =========================

@router.post("/{election_id}/{candidate_id}")
async def cast_vote(
        election_id: int,
        candidate_id: int,
        request: Request,
        access_token: str = Cookie(default=None),
        db: Session = Depends(get_db)
):

    user = get_current_user(access_token, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    # Vérifier si déjà voté pour cette élection
    existing_vote = db.query(VoteLog).filter(
        VoteLog.voter_id == user.id,
        VoteLog.election_id == election_id
    ).first()

    if existing_vote:
        return RedirectResponse(f"/election/{election_id}", status_code=303)

    # ========================
    # Génération vote hash
    # ========================

    raw_vote = f"{user.id}-{candidate_id}-{election_id}-{uuid.uuid4()}"
    vote_hash = hashlib.sha256(raw_vote.encode()).hexdigest()

    # ========================
    # Simulation Blockchain
    # ========================

    tx_hash = record_vote_on_blockchain(
        user.wallet_address,
        candidate_id,
        election_id
    )

    # ========================
    # IP Address
    # ========================

    ip_address = request.client.host

    # ========================
    # Save vote
    # ========================

    vote = VoteLog(
        voter_id=user.id,
        election_id=election_id,
        candidate_id=candidate_id,
        vote_hash=vote_hash,
        blockchain_tx_hash=tx_hash,
        ip_address=ip_address
    )

    db.add(vote)
    db.commit()

    return RedirectResponse(
        f"/election/{election_id}",
        status_code=303
    )