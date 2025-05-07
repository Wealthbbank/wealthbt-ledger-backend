from flask import Flask, request, jsonify
import requests
import json

# Load OpenSanctions API key from config
with open("config.json") as f:
    config = json.load(f)

OPENSANCTIONS_API_KEY = config.get("opensanctions_api_key")

app = Flask(__name__)

# Flagging logic using OpenSanctions
def check_sanctions(name):
    headers = {"Authorization": f"Bearer {OPENSANCTIONS_API_KEY}"}
    url = f"https://api.opensanctions.org/match?q={name}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("match", {}).get("strength", 0) > 0.8
    except Exception as e:
        print(f"Sanctions API error: {e}")
        return False

@app.route("/api/mt799", methods=["POST"])
def process_mt799():
    data = request.json
    flagged = (
        check_sanctions(data.get("sender")) or
        check_sanctions(data.get("receiver"))
    )
    return jsonify({"flagged": flagged, "status": "received"})

@app.route("/api/iso20022", methods=["POST"])
def process_iso20022():
    data = request.json
    flagged = (
        check_sanctions(data.get("debtorName")) or
        check_sanctions(data.get("creditorName"))
    )
    return jsonify({"flagged": flagged, "status": "received"})

if __name__ == "__main__":
    app.run(debug=True)
