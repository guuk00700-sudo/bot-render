import os
from datetime import datetime
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

def send_telegram_message(chat_id, text):
    try:
        r = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        if r.status_code != 200:
            print("Telegram error:", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        print("Exception:", e)
        return False

def build_receipt(order):
    items = order.get("items", [])
    total = order.get("total", 0)
    tag = order.get("telegramTag", "не указан")
    dt = order.get("datetime", datetime.now().strftime("%d.%m.%Y %H:%M"))
    lines = [
        "🧾 <b>НОВЫЙ ЗАКАЗ — NIKOSHOP</b>",
        "",
        f"👤 <b>Тег клиента:</b> {tag}",
        f"📅 <b>Дата:</b> {dt}",
        "",
        "<b>Состав заказа:</b>",
    ]
    for i in items:
        n = i.get('name','?'); q = i.get('qty',1); p = i.get('price',0)
        lines.append(f"• {n} — {q} шт × {p} ₽ = {q*p} ₽")
    lines += ["", f"💰 <b>Итого: {total} ₽</b>"]
    return "\n".join(lines)

@app.route("/api/order", methods=["POST", "OPTIONS"])
def receive_order():
    if request.method == "OPTIONS":
        return "", 200
    try:
        order = request.get_json(force=True)
    except Exception as e:
        print("JSON error:", e)
        return jsonify({"ok": False, "error": "invalid json"}), 400
    if not order or not order.get("items"):
        return jsonify({"ok": False, "error": "empty order"}), 400
    receipt = build_receipt(order)
    sent = send_telegram_message(ADMIN_ID, receipt)
    return jsonify({"ok": sent}), (200 if sent else 500)

@app.route("/", methods=["GET"])
def index():
    return "NIKOSHOP backend is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
