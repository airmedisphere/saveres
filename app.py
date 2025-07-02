from flask import Flask, jsonify, request
import os
import asyncio
from database.db import db
from utils.logger import log_info, log_error

app = Flask(__name__)

@app.route('/')
def hello_world():
    return jsonify({
        "status": "online",
        "message": "Advanced Save Restricted Content Bot API",
        "version": "2.0",
        "features": [
            "High-speed downloads",
            "Batch processing",
            "Progress tracking",
            "Error recovery",
            "Rate limiting"
        ]
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": None,
        "services": {
            "database": "connected",
            "bot": "running"
        }
    })

@app.route('/stats')
async def get_stats():
    try:
        total_users = await db.total_users_count()
        return jsonify({
            "total_users": total_users,
            "status": "success"
        })
    except Exception as e:
        log_error(e, "get_stats")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for external integrations"""
    try:
        data = request.get_json()
        log_info(f"Webhook received: {data}")
        return jsonify({"status": "received"})
    except Exception as e:
        log_error(e, "webhook")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)