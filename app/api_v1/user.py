from flask import url_for, redirect, request, jsonify, json
from ..model import User
from flask_login import current_user, login_user,logout_user,login_required
from . import api
from app import db
from ..decorators import json



#Registration
@api.route('/register', methods=['POST'])
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

#User Login
@api.route('/login', methods=['POST'])
def login ():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify("message:","Login Successful")
        else:
            return jsonify("message:","Invalid Credentials")
    return jsonify({"message": "Method Not Allowed"}), 405

#User Logout
@api.route('/logout')
def logout():
    logout_user()
    return jsonify('message:', "You are logout Succesfully")




#Creating User
@api.route('/users', methods=['POST'])
@json
def new_user():
    user = User()
    user.import_data(request.json)
    if 'password' in request.json:
        user.set_password(request.json['password'])
    else:
        return {"error": "Password is required"}, 400
    db.session.add(user)
    db.session.commit()
    return {}, 201, {"Location": user.get_url()}



#Retriving All Users from the Database
@api.route('/users', methods=['GET'])
@json
def get_users():
    users = User.query.all()
    return [user.export_data() for user in users]


#Get userById
@api.route('/users/<int:id>', methods=['GET'])
@login_required
@json
def get_user(id):
    return User.get_or_404(id)


#Update User
@api.route('/users/<int:id>', methods=['PUT'])
@login_required
@json
def update_user(id):
    user = User.query.get_or_404(id)
    user.import_data(request.json)
    db.session.commit()
    return jsonify(user.export_data())


#Delete User
@api.route('/users/<int:id>', methods=["DELETE"])
@login_required
@json
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(user.export_data())


#Get Orders of a user
@api.route('/users/<int:id>/orders', methods=['GET'])
@json
def get_user_orders(id):
    user = User.query.get_or_404(id)
    orders = user.orders
    return [order.export_data() for order in orders]

















#update user{}
#get_all users
#get userById
#delete user
