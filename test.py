from main import app, db, FRAClaim, DLC, SDLC, GRAM_SABHA
from flask_jwt_extended import create_access_token
from flask import json

# --- Setup app context ---
app.config["TESTING"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # in-memory DB

with app.app_context():
    db.create_all()

    # --- Create users with unique emails ---
    dlc = DLC(f_name="DLC2", l_name="User", email="dlc2@test.com", password="pass")
    sdlc = SDLC(f_name="SDLC2", l_name="User", email="sdlc2@test.com", password="pass", dlc=dlc)
    gram = GRAM_SABHA(f_name="Gram2", l_name="User", email="gram2@test.com", password="pass", sdlc=sdlc)
    db.session.add_all([dlc, sdlc, gram])
    db.session.commit()

    # --- Insert a test claim ---
    claim = FRAClaim(holder_id=1, address="Test Village", land_area="1.0",
                     purpose="कृषि", caste_status="ST")
    db.session.add(claim)
    db.session.commit()
    claim_id = claim.id

    # --- Helper to generate JWT token ---
    def get_token(role, email):
        return create_access_token(identity=email, additional_claims={"role": role})

    with app.test_client() as client:
        print("=== TEST 1: Normal approval workflow ===")
        # 1️⃣ Gram Sabha approves
        gram_token = get_token("gram_sabha", "gram2@test.com")
        resp = client.post(f"/claims/{claim_id}/approve",
                           json={"action": "approve"},
                           headers={"Authorization": f"Bearer {gram_token}"})
        print("Gram Sabha approve:", resp.status_code, resp.get_json())

        # 2️⃣ SDLC approves
        sdlc_token = get_token("sdlc", "sdlc2@test.com")
        resp = client.post(f"/claims/{claim_id}/approve",
                           json={"action": "approve"},
                           headers={"Authorization": f"Bearer {sdlc_token}"})
        print("SDLC approve:", resp.status_code, resp.get_json())

        # 3️⃣ DLC approves
        dlc_token = get_token("dlc", "dlc2@test.com")
        resp = client.post(f"/claims/{claim_id}/approve",
                           json={"action": "approve"},
                           headers={"Authorization": f"Bearer {dlc_token}"})
        print("DLC approve:", resp.status_code, resp.get_json())

        # Check final DB state
        final_claim = db.session.get(FRAClaim, claim_id)
        print("Final approvals:")
        print("Gram Sabha:", final_claim.gram_sabha_approved)
        print("SDLC:", final_claim.sdlc_approved)
        print("DLC:", final_claim.dlc_approved)
        print("Final approved:", getattr(final_claim, "final_approved", False))

        print("\n=== TEST 2: Gram Sabha disapproves ===")
        # Reset claim
        claim2 = FRAClaim(holder_id=2, address="Test Village 2", land_area="1.0",
                          purpose="कृषि", caste_status="ST")
        db.session.add(claim2)
        db.session.commit()
        claim2_id = claim2.id

        # Gram Sabha disapproves
        resp = client.post(f"/claims/{claim2_id}/approve",
                           json={"action": "disapprove"},
                           headers={"Authorization": f"Bearer {gram_token}"})
        print("Gram Sabha disapprove:", resp.status_code, resp.get_json())

        # SDLC tries to approve → should fail
        resp = client.post(f"/claims/{claim2_id}/approve",
                           json={"action": "approve"},
                           headers={"Authorization": f"Bearer {sdlc_token}"})
        print("SDLC attempt after disapproval:", resp.status_code, resp.get_json())

        # DLC tries to approve → should fail
        resp = client.post(f"/claims/{claim2_id}/approve",
                           json={"action": "approve"},
                           headers={"Authorization": f"Bearer {dlc_token}"})
        print("DLC attempt after disapproval:", resp.status_code, resp.get_json())

        # Check final DB state
        final_claim2 = db.session.get(FRAClaim, claim2_id)
        print("Final approvals after disapproval:")
        print("Gram Sabha:", final_claim2.gram_sabha_approved)
        print("SDLC:", final_claim2.sdlc_approved)
        print("DLC:", final_claim2.dlc_approved)
        print("Final approved:", getattr(final_claim2, "final_approved", False))
