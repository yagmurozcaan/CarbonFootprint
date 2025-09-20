# chart_routes.py
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from config import SessionLocal
from models.model import BottleTracking
from os import getenv

# Blueprint tanımı
chart_bp = Blueprint("chart_bp", __name__, url_prefix="/chart")

# API keyleri .env veya ortam değişkeninden al
API_KEYS = getenv("API_KEYS", "").split(",")

# API key kontrol fonksiyonu
def check_api_key():
    key = request.headers.get("x-api-key")
    return key in API_KEYS if key else False

# /chart/chart_data endpoint
@chart_bp.route("/chart_data")
def chart_data():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401

    session_db = SessionLocal()
    try:
        data = session_db.query(
            BottleTracking.bottle_type,
            func.sum(BottleTracking.quantity).label("total_quantity")
        ).group_by(BottleTracking.bottle_type).all()

        return jsonify([{"bottle_type": row.bottle_type, "total_quantity": row.total_quantity} for row in data])
    finally:
        session_db.close()

# /chart/carbon_by_type endpoint
@chart_bp.route("/carbon_by_type")
def carbon_by_type():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401

    session_db = SessionLocal()
    try:
        data = session_db.query(
            BottleTracking.bottle_type,
            func.sum(BottleTracking.carbon_footprint).label("total_carbon")
        ).group_by(BottleTracking.bottle_type).all()

        return jsonify([{"bottle_type": row.bottle_type, "total_carbon": row.total_carbon} for row in data])
    finally:
        session_db.close()
