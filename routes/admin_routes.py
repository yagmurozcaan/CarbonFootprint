from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify,send_file
from functools import wraps
from config import SessionLocal
from models.model import BottleTracking
from create_database import BottleTrackingDB
from sqlalchemy import func
import io
import pandas as pd
from datetime import datetime, timedelta
from os import getenv



admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

db = BottleTrackingDB()

API_KEYS = getenv("API_KEYS", "").split(",")

def check_api_key():
    key = request.headers.get("x-api-key")
    return key in API_KEYS if key else False

# Admin giriş decorator
def admin_login_required(f):
    @wraps(f)  # decorator fonksiyonunun orijinal kimliğini korumak için
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_bp.admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Admin giriş
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    from os import getenv

    ADMIN_USERNAME = getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = getenv("ADMIN_PASSWORD", "admin123")

    # Eğer admin zaten giriş yaptıysa direkt dashboard'a yönlendir
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.dashboard"))

    # Eğer normal kullanıcı giriş yaptıysa admin login sayfasına gelirse kullanıcı ekranına yönlendir
    if session.get("user_logged_in"):
        return render_template("admin_login.html") # veya senin kullanıcı dashboard route'un

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_bp.dashboard"))
        return render_template("admin_login.html", error="Kullanıcı adı veya şifre hatalı.")

    return render_template("admin_login.html")

@admin_bp.route("/logout")
@admin_login_required
def admin_logout():
    session.clear()
    #admin çıkış yapmasına rağmen kullanıcı giriş yaparsa admin ekranına geçebiliyor bundan dolayı session temizleme denendi-çalıştı 
    #session.pop("admin_logged_in", None)
    return redirect(url_for("admin_bp.admin_login"))

# Admin dashboard
@admin_bp.route("/dashboard")
@admin_login_required
def dashboard():
    session_db = db.Session()
    try:
        # Yılları al
        years_query = session_db.query(func.extract('year', BottleTracking.created_at)).distinct().all()
        years = sorted([int(y[0]) for y in years_query if y[0] is not None], reverse=True)

        # Tüm şişe kayıtlarını al
        all_entries = session_db.query(BottleTracking).all()
        all_bottles = [{
            "bottle_type": b.bottle_type,
            "quantity": b.quantity,
            "carbon": float(b.carbon_footprint),
            "date": b.created_at.strftime("%Y-%m-%d")
        } for b in all_entries]

        # Toplam, günlük ve haftalık
        total_bottles = sum(b['quantity'] for b in all_bottles)
        total_carbon = sum(b['carbon'] for b in all_bottles)

        today = datetime.today().date()
        week_ago = today - timedelta(days=7)

        daily_bottles = sum(b['quantity'] for b in all_bottles if b['date'] == today.strftime("%Y-%m-%d"))
        weekly_bottles = sum(b['quantity'] for b in all_bottles if week_ago <= datetime.strptime(b['date'], "%Y-%m-%d").date() <= today)

    finally:
        session_db.close()

    return render_template(
        "admin_dashboard.html",
        years=years,
        all_bottles=all_bottles,
        total_bottles=total_bottles,
        total_carbon=total_carbon,
        daily_bottles=daily_bottles,
        weekly_bottles=weekly_bottles
    )

@admin_bp.route("/dashboard_home")
def dashboard_home():
    if not session.get("admin_logged_in"):  
        return redirect(url_for("login"))  
    return render_template("index.html")  

# Aylık istatistikler
@admin_bp.route("/monthly_stats")
@admin_login_required
def monthly_stats():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return jsonify({"error": "Yıl ve ay parametreleri gereklidir."}), 400

    session_db = db.Session()
    try:
        result = session_db.query(
            BottleTracking.bottle_type,
            func.sum(BottleTracking.quantity).label("total_quantity"),
            func.sum(BottleTracking.carbon_footprint).label("total_carbon")
        ).filter(
            func.year(BottleTracking.created_at) == year,   
            func.month(BottleTracking.created_at) == month  
        ).group_by(
            BottleTracking.bottle_type
        ).all()

        result_list = [
            {
                "bottle_type": row.bottle_type,
                "total_quantity": row.total_quantity,
                "total_carbon": row.total_carbon
            } for row in result
        ]
        return jsonify(result_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session_db.close()

# Excel rapor indir
@admin_bp.route("/download_monthly_report")
@admin_login_required
def download_monthly_report():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return "Yıl ve ay parametreleri gereklidir.", 400

    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

    session_db = db.Session()
    try:
        #Ay bazında toplamlar
        totals_query = session_db.query(
            BottleTracking.bottle_type,
            func.sum(BottleTracking.quantity).label("total_quantity"),
            func.sum(BottleTracking.carbon_footprint).label("total_carbon")
        ).filter(
            BottleTracking.created_at.between(start_date, end_date)
        ).group_by(BottleTracking.bottle_type).all()

        df_totals = pd.DataFrame([{
            "Şişe Türü": r.bottle_type,
            "Toplam Adet": r.total_quantity,
            "Toplam Karbon Ayak İzi": r.total_carbon
        } for r in totals_query])

        #Gün ve saat bazlı tüm kayıtlar db.get_all_entries() kullanılarak
        all_entries = db.get_all_entries() 
        records = []
        for b in all_entries:
            created = b.created_at
            if start_date <= created <= end_date:
                records.append({
                    "Şişe Türü": b.bottle_type,
                    "Adet": b.quantity,
                    "Karbon Ayak İzi": b.carbon_footprint,
                    "Tarih & Saat": created
                })
        df_records = pd.DataFrame(records)

        # Excel oluşturuluyor
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_totals.to_excel(writer, index=False, sheet_name="Aylık Toplamlar")
            df_records.to_excel(writer, index=False, sheet_name="Gün ve Saat Bazlı Kayıtlar")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{year}_{month}_aylik_rapor.xlsx"
        )
    finally:
        session_db.close()

#çalışma mantıgı 
#Kullanıcı /dashboard'e gider
#           │
#           ▼
#   admin_login_required çalışır
#           │
#           ▼
#  session["admin_logged_in"] var mı?
#         /         \
#      Hayır        Evet
#       /             \
#redirect           dashboard() fonksiyonu çalışır
#(login sayfasına)