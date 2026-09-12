import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db.session import SessionLocal
from app.models.workflow import Workflow

db = SessionLocal()
rows = db.query(Workflow).filter(Workflow.status == "active").order_by(Workflow.id).all()
for r in rows:
    print(r.id, "|", r.name[:80])
db.close()
print(f"\nTotal: {len(rows)}")
