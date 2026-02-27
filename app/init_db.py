from app.database import engine, Base

# Import all models so that they are registered
from app.models.voter import Voter
from app.models.elections import Election
from app.models.candidate import Candidate
from app.models.logs import VoteLog
from app.models.logs import FraudAlert


def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


if __name__ == "__main__":
    init_db()
