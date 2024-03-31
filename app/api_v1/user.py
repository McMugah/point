from flask import url_for, redirect, request, jsonify
from ..model import User
from flask_login import current_user,login_required
from . import api
from app import db



#Registration{post, get}
@api.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return jsonify("message:", "Passwords do not match. Please try again.")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify("message:","Email already Registered, Please login")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify("message:","Your Account has been Created Successfully")
    return jsonify({"message": "Method Not Allowed"}), 405








#user login {post, get}
#update user{}
#get_all users
#get userById
#delete user
