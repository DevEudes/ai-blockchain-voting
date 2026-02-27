from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Blockchain Voting System"

    DATABASE_URL: str = "postgresql://ai_user:securepassword@localhost:5432/ai_voting"

    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    BLOCKCHAIN_RPC_URL: str = ""
    CONTRACT_ADDRESS: str = ""
    PRIVATE_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
