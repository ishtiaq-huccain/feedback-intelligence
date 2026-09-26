from sqlalchemy import text
from backend.database.database import SessionLocal

def test_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        tables = db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"
        )).fetchall()
        print("✅ DB connection OK")
        print("📦 Tables:", [t[0] for t in tables])
    except Exception as e:
        print("❌ Database error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
