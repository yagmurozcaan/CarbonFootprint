from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ---------------- Users ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(50), nullable=False)
    user_surname = Column(String(50), nullable=False)
    user_email = Column(String(100), nullable=False, unique=True, index=True)
    user_phone = Column(String(20), nullable=True)
    job_id = Column(Integer, ForeignKey("job_title.id"))

    job = relationship("JobTitle", back_populates="users")
    address = relationship("UserAddress", back_populates="user", uselist=False)
    bottles = relationship("BottleTracking", back_populates="user")
    passwords = relationship("Password", back_populates="user", uselist=False)



# ---------------- User Password ----------------

class Password(Base):
    __tablename__="User_Password"

    id=Column (Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    user_password=Column(String(255), nullable=False)  # hashlenmiş şifre

    
    user = relationship("User", back_populates="passwords")



# ---------------- User Address ----------------

class UserAddress(Base):
    __tablename__ = "user_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    city = Column(String(50), nullable=False)
    district = Column(String(50), nullable=False)
    neighborhood = Column(String(50), nullable=False)

    user = relationship("User", back_populates="address")

# ---------------- Job Title ----------------
class JobTitle(Base):
    __tablename__ = "job_title"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(50), nullable=False, unique=True)

    users = relationship("User", back_populates="job")

# ---------------- Bottle Tracking ----------------
class BottleTracking(Base):
    __tablename__ = "bottle_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bottle_type = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    carbon_footprint = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="bottles")
