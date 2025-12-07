from flask import Blueprint,request,make_response,jsonify
import jwt
import datetime
from functools import wraps
import bcrypt
import globals  
from decorators import jwt_required,admin_required

auth_bp = Blueprint("auth_bp",__name__)

blacklist = globals.db.blacklist
users = globals.db.users

# login route

@auth_bp.route('/api/v1.0/login', methods=['POST'])
def login():
    data = request.get_json()  # read JSON sent by Angular
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password required'}), 400

    user = users.find_one({'username': data['username']})
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'user': data['username'],
            'admin': user['admin'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
        }, globals.secret_key, algorithm='HS256')
        return jsonify({'token': token})

    return jsonify({'message': 'Bad username or password'}), 401


#logout

@auth_bp.route('/api/v1.0/logout', methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({'token':token})
    return make_response(jsonify({'message':'Logout successful'}),200)