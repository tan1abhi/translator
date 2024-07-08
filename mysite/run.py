import logging
from flask import Blueprint, request, jsonify, current_app
from api.view1 import webhook_blueprint

from api import create_app
app = create_app()



@app.route('/')
def home():
    return "Hello, Flask!"


if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)