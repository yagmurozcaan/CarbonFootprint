from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.model import User, UserAddress, JobTitle, Password 
from config import SessionLocal
import random
from utils.email_utils import send_reset_email
from os import getenv

# Blueprint tanımı
user_bp = Blueprint("user", __name__, url_prefix="/user", template_folder="../../templates")

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    # Admin bilgileri (env değişkenlerinden)
    ADMIN_USERNAME = getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = getenv("ADMIN_PASSWORD", "admin123")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # --- 1. Admin kontrolü ---
        if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["username"] = "Admin"
            return redirect(url_for("admin_bp.dashboard"))

        # --- 2. Normal kullanıcı kontrolü ---
        session_db = SessionLocal()
        try:
            result = (
                session_db.query(User, Password)
                .join(Password, User.id == Password.user_id)
                .filter(User.user_email == email)
                .first()
            )

            if result:
                user, user_pass = result

                # Debug: hash kontrolünü gör
                # print("DB hash:", user_pass.user_password, "Girdi şifre:", password)

                # Şifre kontrolü
                if check_password_hash(user_pass.user_password, password):
                    session["user_logged_in"] = True
                    session["username"] = user.user_name
                    return redirect(url_for("index"))
                else:
                    error = "Şifre yanlış."
            else:
                error = "Bu e-posta ile kullanıcı bulunamadı."
        finally:
            session_db.close()

    return render_template("user_login.html", error=error)

# --- Register ---
@user_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        surname = request.form.get("surname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        job_name = request.form.get("job")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        city = request.form.get("city")
        district = request.form.get("district")
        neighborhood = request.form.get("neighborhood")

        session_db = SessionLocal()
        try:
            existing_user = session_db.query(User).filter_by(user_email=email).first()
            if existing_user:
                error = "Bu e-posta zaten kayıtlı."
            elif password != password_confirm:
                error = "Şifreler eşleşmiyor."
            else:
                job = session_db.query(JobTitle).filter_by(job_name=job_name).first()
                if not job:
                    job = JobTitle(job_name=job_name)
                    session_db.add(job)
                    session_db.commit()

                new_user = User(
                    user_name=username,
                    user_surname=surname,
                    user_phone=phone,
                    user_email=email,
                    job_id=job.id
                )
                session_db.add(new_user)
                session_db.commit()

                new_password = Password(
                    user_id=new_user.id,
                    user_password=generate_password_hash(password)
                )
                session_db.add(new_password)

                user_address = UserAddress(
                    user_id=new_user.id,
                    city=city,
                    district=district,
                    neighborhood=neighborhood
                )
                session_db.add(user_address)

                session_db.commit()

                flash("Hesap başarıyla oluşturuldu.", "success")
                return redirect(url_for("user.login"))
        finally:
            session_db.close()

    return render_template("register.html", error=error)

import random

@user_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    message = None
    code_sent = False

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        reset_code_input = request.form.get("reset_code")

        session_db = SessionLocal()
        try:
            user = session_db.query(User).filter_by(user_email=email).first()
            if not user:
                message = "Bu e-posta kayıtlı değil."
            else:
                # Eğer kullanıcı kod girmediyse, kod oluştur ve mail gönder
                if not reset_code_input:
                    code = str(random.randint(100000, 999999))
                    session["reset_code"] = code
                    session["reset_email"] = email
                    if send_reset_email(email, code):
                        message = "Şifre sıfırlama kodu e-posta adresinize gönderildi."
                        code_sent = True
                    else:
                        message = "E-posta gönderilemedi."
                else:
                    # Kullanıcı kodu girdi, doğrula
                    if reset_code_input.strip() == str(session.get("reset_code")):
                        print("Kod doğru, update_password sayfasına yönlendiriliyor.")
                        return redirect(url_for("user.update_password"))
                    else:
                        message = "Kod yanlış, tekrar deneyin."
        finally:
            session_db.close()

    return render_template("forgot_password.html", message=message, code_sent=code_sent)
# --- Update Password ---

@user_bp.route("/update_password", methods=["GET", "POST"])
def update_password():
    message = None
    email = session.get("reset_email")  # Kod doğruysa burada email olacak

    if not email:
        return redirect(url_for("user.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        if not password or not password_confirm:
            message = "Lütfen tüm alanları doldurun."
        elif password != password_confirm:
            message = "Şifreler eşleşmiyor."
        else:
            session_db = SessionLocal()
            try:
                user = session_db.query(User).filter_by(user_email=email).first()
                if user:
                    user_pass = session_db.query(Password).filter_by(user_id=user.id).first()
                    if user_pass:
                        try:
                            user_pass.user_password = generate_password_hash(password)
                            session_db.commit()
                            print(f"{email} için şifre başarıyla güncellendi.")
                            # Session temizle
                            session.pop("reset_email", None)
                            session.pop("reset_code", None)
                            flash("Şifreniz başarıyla güncellendi.", "success")
                            return redirect(url_for("user.login"))
                        except Exception as e:
                            session_db.rollback()
                            message = f"Şifre güncellenirken bir hata oluştu: {e}"
                            print(" Hata:", e)
                    else:
                        message = "Şifre güncellenirken bir hata oluştu. Kayıt bulunamadı."
                        print("user_pass None döndü")
                else:
                    message = "Kullanıcı bulunamadı."
                    print("user None döndü")
            finally:
                session_db.close()

    return render_template("update_password.html", message=message)


# --- Logout ---
@user_bp.route("/logout")
def logout():
    session.pop("user_logged_in", None)
    session.pop("username", None)
    return redirect(url_for("user.login"))
