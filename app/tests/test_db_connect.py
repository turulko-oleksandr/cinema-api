from sqlalchemy import create_engine
from database.models.base import Base

engine = create_engine("postgresql://admin:admin@localhost:5432/cinema_api")

print("Creating metadata...")
Base.metadata.create_all(engine)
print("✅ Tables created successfully")