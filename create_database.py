from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date
from models.model import BottleTracking
from config import SessionLocal

class BottleTrackingDB:
    def __init__(self):
        self.Session = SessionLocal
        self.carbon_factors = {
            "cam": 0.5,
            "alüminyum": 0.3,
            "plastik": 0.2
        }

    def add_bottle_entry(self, bottle_type: str, quantity: int):
        if bottle_type not in self.carbon_factors:
            raise ValueError(f"Bilinmeyen şişe tipi: {bottle_type}")

        carbon_footprint = self.carbon_factors[bottle_type] * quantity
        session = self.Session()

        try:
            new_entry = BottleTracking(
                bottle_type=bottle_type,
                quantity=quantity,
                carbon_footprint=carbon_footprint
            )
            session.add(new_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_total_stats(self):
        session = self.Session()
        try:
            result = session.query(
                func.sum(BottleTracking.quantity).label("total_bottles"),
                func.sum(BottleTracking.carbon_footprint).label("total_carbon")
            ).one()
            return {
                "total_bottles": result.total_bottles or 0,
                "total_carbon": result.total_carbon or 0
            }
        finally:
            session.close()

    def get_all_entries(self):
        session = self.Session()
        try:
            return session.query(BottleTracking).order_by(BottleTracking.created_at.desc()).all()
        finally:
            session.close()

    def get_daily_stats(self):
        session = self.Session()
        try:
            today = datetime.utcnow().date()
            result = session.query(
                func.sum(BottleTracking.quantity),
                func.sum(BottleTracking.carbon_footprint)
            ).filter(cast(BottleTracking.created_at, Date) == today).one()
            return {
                "total_quantity": result[0] or 0,
                "total_carbon": result[1] or 0
            }
        finally:
            session.close()

    def get_weekly_stats(self):
        session = self.Session()
        try:
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            result = session.query(
                func.sum(BottleTracking.quantity),
                func.sum(BottleTracking.carbon_footprint)
            ).filter(BottleTracking.created_at >= one_week_ago).one()
            return {
                "total_bottles": result[0] or 0,
                "total_carbon": result[1] or 0
            }
        finally:
            session.close()
