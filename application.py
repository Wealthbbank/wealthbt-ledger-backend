from flask import Flask, request, jsonify
import uuid, json, os
from datetime import datetime
import requests

app = Flask(__name__)
LOG_FILE = "ledger_log.json"
FLAGGED_FILE = "flagged_messages.json"

def check_opensanctions(name):
    try:
        with open("config.json") as f:
            key = json.load(f)["opensanctions_api_key"]
        res = requests.get(
            f"https://api.opensanctions.org/match?q={name}",
            headers={"Authorization": f"ApiKey {key}"}
        )
        data = res.json()
        if data.get("match") and data["match"].get("score", 0) > 0.85:
            return data["match"]["entity"]["name"]
    except Exception as e:
        print("Sanctions check failed:", e)
    return None

def log_to_file(entry):
    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            data = json.load(f)
    data.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/ledger-core/api/mt799", methods=["POST"])
def mt799():
    data = request.form
    flagged = []
    for field in ["sender", "receiver"]:
        res = check_opensanctions(data.get(field, ""))
        if res:
            flagged.append(f"{field}: {res}")
    entry = {
        "id": str(uuid.uuid4()),
        "type": "MT799",
        "timestamp": datetime.utcnow().isoformat(),
        "data": data.to_dict(),
        "flags": ["OpenSanctions"] if flagged else [],
        "matches": flagged
    }
    log_to_file(entry)
    return jsonify({"message": "MT799 logged", "screening": flagged}), 200

@app.route("/ledger-core/api/iso20022", methods=["POST"])
def iso20022():
    data = request.form
    flagged = []
    for field in ["debtorName", "creditorName"]:
        res = check_opensanctions(data.get(field, ""))
        if res:
            flagged.append(f"{field}: {res}")
    entry = {
        "id": str(uuid.uuid4()),
        "type": "ISO20022",
        "timestamp": datetime.utcnow().isoformat(),
        "data": data.to_dict(),
        "flags": ["OpenSanctions"] if flagged else [],
        "matches": flagged
    }
    log_to_file(entry)
    return jsonify({"message": "ISO20022 logged", "screening": flagged}), 200

@app.route("/")
def index():
    return "WealthBT Ledger Backend Online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
