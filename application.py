from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime

app = Flask(__name__)

# Load config
with open("config.json") as f:
    CONFIG = json.load(f)

FLAGGED_FILE = "flagged_messages.json"
LOG_FILE = "ledger_log.json"


# Helper: Check OpenSanctions for match
def check_opensanctions(name):
    api_key = CONFIG.get("opensanctions_api_key")
    if not api_key:
        return False

    url = f"https://api.opensanctions.org/match?api_key={api_key}"
    response = requests.post(url, json={"q": name})
    data = response.json()
    return any(r.get("match", False) for r in data.get("results", []))


# Helper: Append to JSON log file
def append_to_log(filename, data):
    try:
        with open(filename, "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    logs.append(data)
    with open(filename, "w") as f:
        json.dump(logs, f, indent=2)


@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok"})


@app.route("/api/mt799", methods=["POST"])
def submit_mt799():
    data = request.form.to_dict()
    data["timestamp"] = datetime.utcnow().isoformat()

    # Sanction check
    flagged = any([
        check_opensanctions(data.get("sender_bic", "")),
        check_opensanctions(data.get("receiver_bic", ""))
    ])
    data["flagged"] = flagged

    append_to_log(LOG_FILE, data)
    if flagged:
        append_to_log(FLAGGED_FILE, data)

    return jsonify({"status": "received", "flagged": flagged})


@app.route("/api/iso20022", methods=["POST"])
def submit_iso20022():
    data = request.form.to_dict()
    data["timestamp"] = datetime.utcnow().isoformat()

    # Sanction check
    flagged = any([
        check_opensanctions(data.get("debtor_name", "")),
        check_opensanctions(data.get("creditor_name", ""))
    ])
    data["flagged"] = flagged

    append_to_log(LOG_FILE, data)
    if flagged:
        append_to_log(FLAGGED_FILE, data)

    return jsonify({"status": "received", "flagged": flagged})


if __name__ == "__main__":
    app.run(debug=True)
