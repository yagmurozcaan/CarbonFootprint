from flask import Blueprint, request, jsonify
from create_database import BottleTrackingDB

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")

db = BottleTrackingDB()

from os import getenv
API_KEYS = getenv("API_KEYS", "").split(",")

def check_api_key():
    key = request.headers.get("x-api-key")
    return key in API_KEYS if key else False

@api_bp.route("/add_bottle", methods=["POST"])
def add_bottle():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401

    data = request.get_json()
    bottle_type = data.get("bottle_type")
    quantity = data.get("quantity")

    if not bottle_type or not quantity:
        return jsonify({"error": "Eksik veri"}), 400

    try:
        db.add_bottle_entry(bottle_type, int(quantity))
        return jsonify({"message": "Kayıt eklendi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/stats")
def stats():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401
    return jsonify(db.get_total_stats())

@api_bp.route("/daily_stats")
def daily_stats():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401
    return jsonify(db.get_daily_stats())

@api_bp.route("/weekly_stats")
def weekly_stats():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401
    return jsonify(db.get_weekly_stats())

@api_bp.route("/all_bottles", methods=["GET"])
def all_bottles():
    if not check_api_key():
        return jsonify({"error": "Geçersiz veya eksik API anahtarı"}), 401
    try:
        bottles = db.get_all_entries() 
        result = []
        for b in bottles:
            result.append({
                "bottle_type": b.bottle_type,
                "quantity": b.quantity,
                "carbon_footprint": b.carbon_footprint,
                "created_at": b.created_at.isoformat()
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
