from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
from flask_cors import CORS
from pathlib import Path

# --- DSS imports ---
from dss import (
    fetch_lulc_data,
    get_claims_for_district,
    check_scheme_eligibility,
    summarize_scheme_eligibility,
    get_aoi_lulc_stats
)

# --- Flask App Config ---
app = Flask(__name__)
CORS(app)

from pathlib import Path

# --- Flask App Config ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "fra.db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secret"  # ⚠️ Change in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)

# --- Models ---
class DLC(db.Model):
    __tablename__ = "dlc"
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(100))
    l_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(255))
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
    holder_id = db.Column(db.Integer)
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
    dlc_approved = db.Column(db.Boolean, default=None)
    sdlc_approved = db.Column(db.Boolean, default=None)
    gram_sabha_approved = db.Column(db.Boolean, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Helper ---
def get_user_model(role):
    return {"dlc": DLC, "sdlc": SDLC, "gram_sabha": GRAM_SABHA}.get(role)

# --- Auth Resources ---
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
            password=data["password"]
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
        token = create_access_token(identity=user.email, additional_claims={"role": role})
        return {"access_token": token}, 200

# --- Claim Resources ---
class AddClaim(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        claim = FRAClaim(**data)
        db.session.add(claim)
        db.session.commit()
        return {
            "msg": "FRA Claim added successfully",
            "claim": {
                "id": claim.id,
                "holder_id": claim.holder_id,
                "address": claim.address,
                "purpose": claim.purpose,
                "land_area": claim.land_area,
                "caste_status": claim.caste_status
            }
        }, 201

from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from main import FRAClaim

class GetClaims(Resource):
    @jwt_required()
    def get(self):
        claims = FRAClaim.query.all()
        result = []
        for c in claims:
            result.append({
                "id": c.id,
                "source_file": c.source_file,
                "holder_id": c.holder_id,
                "address": c.address,
                "village_details": c.village_details,
                "khasara_no": c.khasara_no,
                "land_area": c.land_area,
                "purpose": c.purpose,
                "caste_status": c.caste_status,
                "forest_block_name": c.forest_block_name,
                "compartment_no": c.compartment_no,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "level": c.level,
                "remark": c.remark,
                "gram_sabha_approved": c.gram_sabha_approved,
                "sdlc_approved": c.sdlc_approved,
                "dlc_approved": c.dlc_approved,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            })
        return jsonify(result)


# --- DSS Endpoints ---
# --- DSS Endpoints ---
class LULC(Resource):
    @jwt_required()
    def get(self, distcode="0831"):
        DISTRICT_TOKEN = "212f217e47242e11e4cee706764bbc23053f9008"  # new token
        year = request.args.get("year", "1112")
        data = fetch_lulc_data(distcode, DISTRICT_TOKEN, year)
        return jsonify(data)

class DistrictClaims(Resource):
    @jwt_required()
    def get(self, district):
        db_path = Path("instance/fra.db")
        claims = get_claims_for_district(db_path, district)
        return jsonify(claims)

class ClaimEligibility(Resource):
    @jwt_required()
    def get(self, claim_id):
        db_path = Path("instance/fra.db")
        district = request.args.get("district", "बारां")
        DISTRICT_TOKEN = "212f217e47242e11e4cee706764bbc23053f9008"  # new token
        distcode = request.args.get("distcode", "0831")
        lulc_data = fetch_lulc_data(distcode, DISTRICT_TOKEN)
        claims = get_claims_for_district(db_path, district)
        claim = next((c for c in claims if c["id"] == int(claim_id)), None)
        if not claim:
            return {"msg": "Claim not found"}, 404
        eligibility = check_scheme_eligibility(claim, lulc_data)
        return jsonify(eligibility)

class DistrictEligibilitySummary(Resource):
    @jwt_required()
    def get(self, district):
        db_path = Path("instance/fra.db")
        DISTRICT_TOKEN = "212f217e47242e11e4cee706764bbc23053f9008"  # new token
        distcode = request.args.get("distcode", "0831")
        lulc_data = fetch_lulc_data(distcode, DISTRICT_TOKEN)
        summary = summarize_scheme_eligibility(db_path, district, lulc_data)
        return jsonify(summary)

class AOILULC(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        geom = data.get("geom")
        AOI_TOKEN = "212f217e47242e11e4cee706764bbc23053f9008"  # new AOI token
        result = get_aoi_lulc_stats(geom, AOI_TOKEN)
        return jsonify(result)
class ApproveClaim(Resource):
    @jwt_required()
    def post(self, claim_id):
        """
        Sequential approval workflow:
        - Gram Sabha → SDLC → DLC
        - Body: { "action": "approve" or "disapprove" }
        """
        user_email = get_jwt_identity()
        role = get_jwt().get("role")  # dlc / sdlc / gram_sabha
        if role not in ["dlc", "sdlc", "gram_sabha"]:
            return {"msg": "Unauthorized role"}, 403

        # Fetch claim
        claim = FRAClaim.query.filter_by(id=claim_id).first()
        if not claim:
            return {"msg": "Claim not found"}, 404

        # Validate action
        action = request.json.get("action")
        if action not in ["approve", "disapprove"]:
            return {"msg": "Invalid action, must be 'approve' or 'disapprove'"}, 400

        # Sequential approval enforcement
        if role == "sdlc" and not claim.gram_sabha_approved:
            return {"msg": "Cannot act, waiting for Gram Sabha approval"}, 403
        if role == "dlc" and (not claim.gram_sabha_approved or not claim.sdlc_approved):
            return {"msg": "Cannot act, waiting for previous approvals"}, 403

        # If someone disapproves, stop further approvals
        if action == "disapprove":
            setattr(claim, f"{role}_approved", False)
            claim.final_approved = False  # optional: mark as rejected
            db.session.commit()
            return {
                "msg": f"Claim disapproved by {role.upper()}",
                "claim_id": claim.id,
                "status": False
            }, 200

        # Approve action
        setattr(claim, f"{role}_approved", True)

        # Check if all three approved → mark final approval
        if claim.gram_sabha_approved and claim.sdlc_approved and claim.dlc_approved:
            claim.final_approved = True

        db.session.commit()

        return {
            "msg": f"Claim approved by {role.upper()}",
            "claim_id": claim.id,
            "status": getattr(claim, f"{role}_approved"),
            "final_approved": getattr(claim, "final_approved", False)
        }, 200


# --- Routes ---
api.add_resource(Register, "/register/<string:role>")
api.add_resource(Login, "/login/<string:role>")
api.add_resource(AddClaim, "/claims")
api.add_resource(GetClaims, "/claims/all")
api.add_resource(LULC, "/lulc/<string:distcode>")
api.add_resource(DistrictClaims, "/claims/district/<string:district>")
api.add_resource(ClaimEligibility, "/eligibility/<int:claim_id>")
api.add_resource(DistrictEligibilitySummary, "/eligibility/summary/<string:district>")
api.add_resource(AOILULC, "/lulc/aoi")
api.add_resource(ApproveClaim,"/claims/<claim_id>/approve")

# --- Run App ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensures tables exist
    app.run(debug=True)
