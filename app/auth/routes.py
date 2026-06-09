from flask import Blueprint, request, jsonify
from app.db import db
from models.user import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__, url_prefix = '/auth')

@auth_bp.route('/register', methods = ['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'ERROR': 'Missing username or password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'ERROR': 'User already exist'}), 409
    
    new_user = User(username = username)
    new_user.set_password(password)#update -> set -> il setpassword hasha la password stessa
    db.session.add(new_user) #session avvia una transazione col db
    db.session.commit()
    return jsonify({'SUCCESS':'User registered successfully'}), 201

@auth_bp.route('/login', methods = ['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'ERROR': 'Missing username or password'}), 400

    logging_user = User.query.filter_by(username=username).first()
    
    if not logging_user or not logging_user.check_password(password):
        return jsonify({'ERROR': 'Wrong username or password'}), 401

    access_token = create_access_token(identity=str(logging_user.id))
    return jsonify({'access_token': access_token}), 200