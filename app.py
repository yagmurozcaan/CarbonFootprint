from flask import Flask, render_template, session, request
from config import SessionLocal
from models.model import Base
from routes.admin_routes import admin_bp
from routes.api_routes import api_bp
from routes.chart_routes import chart_bp
from routes.user_routes import user_bp  
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = "gizli_anahtar"
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per minute"] 
)

# Blueprintleri register et
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chart_bp)
app.register_blueprint(user_bp) 

# Ana sayfa
@app.route("/")
@limiter.limit("20 per minute")  
def index():
    if session.get("user_logged_in"):
        return render_template("index.html", username=session.get("username"))
    return render_template("user_login.html")  # Login ekranı

if __name__ == "__main__":
    session_db = SessionLocal()
    try:
        Base.metadata.create_all(bind=session_db.bind)
    finally:
        session_db.close()

    app.run(host="0.0.0.0", port=1234, debug=True)
