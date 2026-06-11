from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from db import db
from models.user import create_admin
from auth.a_routes import auth_bp
from ticket_service_api.ts_routes import ticket_service_bp
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secretKey')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

jwt = JWTManager(app)
db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(ticket_service_bp)

with app.app_context():
    db.create_all()
    create_admin()


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.route('/')
def hello_app():
    return jsonify({"msg": "Hello! Check documentation to start using API for Ticket Reservation"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5050)))