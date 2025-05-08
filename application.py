from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Load configuration with OpenSanctions API key
with open("config.json") as f:
    config = json.load(f)

API_KEY = config.get("opensanctions_api_key")
API_URL = "https://api.opensanctions.org/match"

def check_sanctions(name):
    params = {
        "q": name,
        "threshold": 0.7,
        "api_key": API_KEY
    }
    response = requests.get(API_URL, params=params)
    result = response.json()
    return result.get("match", {}).get("score", 0) >= 0.7

@app.route("/api/mt799", methods=["POST"])
def handle_mt799():
    data = request.get_json()  # ← This was the problem
    sender = data.get("sender", "")
    receiver = data.get("receiver", "")
    flagged = check_sanctions(sender) or check_sanctions(receiver)
    return jsonify({"flagged": flagged, "status": "received"})

@app.route("/api/iso20022", methods=["POST"])
def handle_iso20022():
    data = request.get_json()  # ← This was the problem
    debtor = data.get("debtorName", "")
    creditor = data.get("creditorName", "")
    flagged = check_sanctions(debtor) or check_sanctions(creditor)
    return jsonify({"flagged": flagged, "status": "received"})

@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
