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

@auth_bp.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization

    if auth:
        user = users.find_one({'username': auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user['password']):
                token = jwt.encode({
                    'user_id': str(user['_id']),  
                    'user': auth.username,
                    'admin':user['admin'],
                    'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
                }, globals.secret_key, algorithm='HS256')

                return make_response(jsonify({'token': token}), 200)
            else:
                return make_response(jsonify({'Message': 'Bad password'}), 401)
        else:
            return make_response(jsonify({'Message': 'Bad username'}), 401)

    return make_response(jsonify({'message': 'Authentication required'}), 401)

#logout

@auth_bp.route('/api/v1.0/logout', methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({'token':token})
    return make_response(jsonify({'message':'Logout successful'}),200)