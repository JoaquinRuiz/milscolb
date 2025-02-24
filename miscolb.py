import requests
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from latch import Latch
import uuid

load_dotenv()
LATCH_APP_ID = os.getenv("LATCH_APP_ID")
LATCH_SECRET_KEY = os.getenv("LATCH_SECRET_KEY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
CONTROL_CAMARA_ID = os.getenv("CONTROL_CAMARA_ID")
HOMEASSISTANT_TOKEN = os.getenv("HOMEASSISTANT_TOKEN")
HOMEASSISTANT_URL_ACTIVATE = os.getenv("HOMEASSISTANT_URL_ACTIVATE")
HOMEASSISTANT_URL_DEACTIVATE = os.getenv("HOMEASSISTANT_URL_DEACTIVATE")
ACCOUNT_ID_FILE = "account_id.txt"

app = Flask(__name__)
latch_api = Latch(LATCH_APP_ID, LATCH_SECRET_KEY)

def load_account_id():
    """Carga el account_id desde un archivo (si existe)"""
    try:
        if os.path.exists(ACCOUNT_ID_FILE):
            with open(ACCOUNT_ID_FILE, "r") as f:
                return f.read().strip()
        return None
    except Exception as e:
        print(f"Error cargando account_id.txt: {e}")
        return None

def save_account_id(account_id):
    """Guarda el account_id en un archivo"""
    with open(ACCOUNT_ID_FILE, "w") as f:
        f.write(account_id)

ACCOUNT_ID = load_account_id()

# Middleware -> Latch
@app.route("/pair", methods=["POST"])
def pair():
    global ACCOUNT_ID 
    data = request.get_json()
    pair_code = data.get("pair_code")

    if not pair_code:
        return jsonify({"error": "Pair code is required"}), 400

    response = latch_api.pair(pair_code)
    if response.error == '' and response.data.get("accountId"):
        ACCOUNT_ID = response.data.get("accountId") 
        save_account_id(ACCOUNT_ID)
        print(f"Cuenta pareada con éxito. Account ID: {ACCOUNT_ID}")
        return jsonify({"status": "paired", "account_id": ACCOUNT_ID})
    else:
        print(f"ERROR pareando cuenta: {response.error}")
        return jsonify({"error": response.error}), 400

# Middleware -> Latch
def lock_latch():
    try:
        response = latch_api.lock(ACCOUNT_ID, CONTROL_CAMARA_ID)

        if response and response.error == '':
            print("Latch bloqueado correctamente")
            return True
        else:
            print(f"ERROR bloqueando Latch: {response.error}")
            return False
    except Exception as e:
        print(f"ERROR crítico en lock_latch(): {e}")
        return False

# Middleware -> Latch
def unlock_latch():
    try:
        response = latch_api.unlock(ACCOUNT_ID, CONTROL_CAMARA_ID)

        if response and response.error == '':
            print("Latch desbloqueado correctamente")
            return True
        else:
            print(f"ERROR desbloqueando Latch: {response.error}")
            return False
    except Exception as e:
        print(f"ERROR crítico en unlock_latch(): {e}")
        return False

# Alexa -> Middleware -> Latch
@app.route("/webhook", methods=["POST"])
def webhook():
    if not ACCOUNT_ID:
        return jsonify({"error": "Latch account not paired"}), 400

    data = request.get_json()
    action = data.get("action")

    if action == "arrived":
        if lock_latch():
            return jsonify({"status": "locked"})
    elif action == "left":
        if unlock_latch():
            return jsonify({"status": "unlocked"})

    return jsonify({"status": "error"}), 500

# Middleware -> HomeAssitant-Alexa-Blink
def trigger_homeassistant_routine(activate):
    """ Activa o desactiva la cámara Blink usando Home Assitant y Alexa """
    url = HOMEASSISTANT_URL_ACTIVATE if activate else HOMEASSISTANT_URL_DEACTIVATE
    
    headers = {
        "Authorization": f"Bearer {HOMEASSISTANT_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "entity_id": "input_boolean.activate_cam", 
    }

    response = requests.post(url, json=body, headers=headers)

    if response.status_code == 200:
        print(f"HA-Alexa ha {'activado' if activate else 'desactivado'} Blink correctamente.")
    else:
        print(f"Error controlando Blink: {response.status_code} - {response.text}")

    return response.json()

# Latch -> Middleware -> Alexa-Blink
@app.route("/latch_webhook", methods=["GET", "POST"])
def latch_webhook():
    """ Latch notifica al Middleware, y este reenvía el evento a Alexa """

    if not ACCOUNT_ID:
        return jsonify({"error": "Latch account not paired"}), 400

    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            print(f"Latch envió un GET de verificación con challenge: {challenge}")
            return challenge, 200 

        print("Latch envió un GET sin challenge (puede ser una prueba)")
        return jsonify({"status": "ok", "message": "Webhook conectado correctamente"}), 200

    elif request.method == "POST":
        try:
            data = request.get_json()
            print(f"Latch envió un POST con este JSON: {data}")

            if "accounts" not in data or ACCOUNT_ID not in data["accounts"]:
                print("Error: JSON no contiene 'accounts' o el 'account_id' esperado")
                return jsonify({"error": "Invalid JSON format"}), 400

            changes = data["accounts"][ACCOUNT_ID]
            if not changes or "new_status" not in changes[0]:
                print("Error: JSON no contiene 'new_status'")
                return jsonify({"error": "Invalid JSON format"}), 400

            new_status = changes[0]["new_status"]

            print(f"Latch ha cambiado de estado: {new_status}")

            if new_status == "off":
                trigger_homeassistant_routine(False)
            elif new_status == "on":
                trigger_homeassistant_routine(True)

            return jsonify({"status": "ok"})
        except Exception as e:
            print(f"Error procesando el POST de Latch: {e}")
            return jsonify({"error": "Invalid request"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
