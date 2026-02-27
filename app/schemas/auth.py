from pydantic import BaseModel, EmailStr
from app.services.blockchain_service import generate_wallet_address


class RegisterResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
