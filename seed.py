# seed.py
from app.db.session import SessionLocal, engine, Base
from app import models

# make sure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# create a test user
user = models.User(email="test@example.com", password_hash="hashedpassword123")
db.add(user)
db.commit()
db.refresh(user)

# create a test category
cat = models.Category(name="Food", type="expense", user_id=user.id)
db.add(cat)
db.commit()
db.refresh(cat)

print("✅ User ID:", user.id)
print("✅ Category ID:", cat.id)

db.close()
