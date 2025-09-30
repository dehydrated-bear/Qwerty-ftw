from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
from flask_cors import CORS
import os

# --- Flask App Config ---
app = Flask(__name__)
CORS(app)

# Use SQLite for now (easy for testing)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fra.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secret"  # change in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)


# --- Models with relationships ---
class DLC(db.Model):
    __tablename__ = "dlc"
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(100))
    l_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))

    # One DLC can have many SDLCs
    sdlcs = db.relationship("SDLC", backref="dlc", cascade="all, delete-orphan")


class SDLC(db.Model):
    __tablename__ = "sdlc"
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(100))
    l_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))

    dlc_id = db.Column(db.Integer, db.ForeignKey("dlc.id"), nullable=False)
    
    # One SDLC can have many Gram Sabhas
    gram_sabhas = db.relationship("GRAM_SABHA", backref="sdlc", cascade="all, delete-orphan")


class GRAM_SABHA(db.Model):
    __tablename__ = "gram_sabha"
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(100))
    l_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))

    sdlc_id = db.Column(db.Integer, db.ForeignKey("sdlc.id"), nullable=False)


class FRAClaim(db.Model):
    __tablename__ = "fra_claims"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_file = db.Column(db.String(255))
    holder_id = db.Column(db.Integer, autoincrement = True)
    address = db.Column(db.String(255))
    village_details = db.Column(db.String(255), nullable=True)
    khasara_no = db.Column(db.String(255))
    land_area = db.Column(db.String(255))
    purpose = db.Column(db.String(255))
    caste_status = db.Column(db.String(255))
    forest_block_name = db.Column(db.String(255))
    compartment_no = db.Column(db.String(255))
    latitude = db.Column(db.String(255))
    longitude = db.Column(db.String(255))
    level = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    approved=db.Column(db.Boolean(),default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
# --- Helper function for role-based tables --- 

def get_user_model(role):
    if role == "dlc":
        return DLC
    elif role == "sdlc":
        return SDLC
    elif role == "gram_sabha":
        return GRAM_SABHA
    else:
        return None


# --- Resources (API Endpoints) ---
class Register(Resource):
    def post(self, role):
        data = request.get_json()
        model = get_user_model(role)
        if not model:
            return {"msg": "Invalid role"}, 400

        if model.query.filter_by(email=data["email"]).first():
            return {"msg": "User already exists"}, 400

        user = model(
            f_name=data.get("f_name"),
            l_name=data.get("l_name"),
            email=data["email"],
            phone=data.get("phone"),
            password=data["password"],  # ⚠️ hash in production
        )
        db.session.add(user)
        db.session.commit()
        return {"msg": "User registered successfully"}, 201


class Login(Resource):
    def post(self, role):
        data = request.get_json()
        model = get_user_model(role)
        if not model:
            return {"msg": "Invalid role"}, 400

        user = model.query.filter_by(email=data["email"]).first()
        if not user or user.password != data["password"]:
            return {"msg": "Invalid credentials"}, 401

        # FIX: identity must be string, role in additional_claims
        access_token = create_access_token(
            identity=user.email,
            additional_claims={"role": role}
        )
        return {"access_token": access_token}, 200


class AddClaim(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        claim = FRAClaim(
            source_file=data.get("source_file"),
            holder_id=data.get("holder_id"),
            address=data.get("address"),
            village_details=data.get("village_details"),
            khasara_no=data.get("khasara_no"),
            land_area=data.get("land_area"),
            purpose=data.get("purpose"),
            caste_status=data.get("caste_status"),
            forest_block_name=data.get("forest_block_name"),
            compartment_no=data.get("compartment_no"),
            gps_addr=data.get("gps_addr"),
        )
        db.session.add(claim)
        db.session.commit()
        return {"msg": "FRA Claim added successfully"}, 201


class GetClaims(Resource):
    @jwt_required()
    def get(self):
        claims = FRAClaim.query.all()
        return [{
            "id": c.id,
            "source_file": c.source_file,
            "address": c.address,
            "village_details": c.village_details,
            "khasara_no": c.khasara_no,
            "land_area": c.land_area,
            "purpose": c.purpose,
            "caste_status": c.caste_status,
            "forest_block_name": c.forest_block_name,
            "compartment_no": c.compartment_no,
            "gps_addr": c.gps_addr,
        } for c in claims], 200


# --- Routes ---
api.add_resource(Register, "/register/<string:role>")
api.add_resource(Login, "/login/<string:role>")
api.add_resource(AddClaim, "/claims")
api.add_resource(GetClaims, "/claims/all")


# --- Run App ---
if __name__ == "__main__":
    # Ensure DB and tables exist
    with app.app_context():
        db.create_all()
        print("Database and tables created (if not existed).")

    app.run(debug=True)
