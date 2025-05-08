from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app, origins=["https://wealthbt.com"])

# Load config and local flag storage
with open("config.json") as f:
    config = json.load(f)

FLAGGED_FILE = "flagged_messages.json"

def load_flagged():
    try:
        with open(FLAGGED_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_flagged(data):
    with open(FLAGGED_FILE, "w") as f:
        json.dump(data, f)

def check_sanctions(name):
    api_key = config.get("opensanctions_api_key", "")
    url = f"https://api.opensanctions.org/match?api_key={api_key}"
    payload = {"name": name}
    try:
        res = requests.post(url, json=payload, timeout=5)
        res.raise_for_status()
        matches = res.json().get("matches", [])
        return any(match.get("score", 0) >= 0.8 for match in matches)
    except Exception as e:
        print("Error querying OpenSanctions:", e)
        return False

@app.route("/api/mt799", methods=["POST"])
def handle_mt799():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    sender = data.get("sender", "")
    receiver = data.get("receiver", "")

    flagged = check_sanctions(sender) or check_sanctions(receiver)

    if flagged:
        flagged_entries = load_flagged()
        flagged_entries.append({
            "type": "MT799",
            "sender": sender,
            "receiver": receiver,
            "content": data
        })
        save_flagged(flagged_entries)

    return jsonify({"flagged": flagged, "status": "received"})

@app.route("/api/iso20022", methods=["POST"])
def handle_iso20022():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    debtor = data.get("debtorName", "")
    creditor = data.get("creditorName", "")

    flagged = check_sanctions(debtor) or check_sanctions(creditor)

    if flagged:
        flagged_entries = load_flagged()
        flagged_entries.append({
            "type": "ISO20022",
            "debtor": debtor,
            "creditor": creditor,
            "content": data
        })
        save_flagged(flagged_entries)

    return jsonify({"flagged": flagged, "status": "received"})

@app.route("/")
def health_check():
    return "WealthBT Ledger Backend is running."

if __name__ == "__main__":
    app.run()
