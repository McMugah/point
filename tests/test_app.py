import json
from flask import url_for
from app.model import User


#User Registration Test
def test_user_registration_post(client):
    data = {
        'username': 'test user',
        'email': 'test@gmail.com',
        'password': 'password',
        'confirm_password': 'password'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert b"Your Account has been Created Successfully" in response.data


def test_user_registration_get(client):
    response = client.get('/register')
    assert response.status_code == 405
    # assert b'Register' in response.data


#User Login Test
def test_user_login_post(client):
    data = {
        "email": "test@gmail.com",
        "password": "test"
    }
    response = client.post('/login')
    assert response.status_code == 200


def test_user_login_get(client):
    response = client.get('/login')
    assert response.status_code == 405


#User Logout Test
def test_user_logout(client):
    response = client.get('/logout')
    assert response.status_code == 200
    assert b"You are logout Succesfully" in response.data


#Testing for Creating User
def test_new_user(client):
    data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password"
    }
    response = client.post('/users', json= data)
    assert response.status_code == 201
    assert "Location" in response.headers
    new_user_url = response.headers["Location"]


#Testing for getting all users
def test_get_users(client):
    response = client.get('/users')
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)
    for user_data in data:
        assert 'email' in user_data
        assert 'orders' in user_data


#Test for getting userById
def test_get_user(client, authenticated_user):
    user = User(username='test_user', email='test@example.com')
    user.set_password('password123')
    user.save()
    with client:
        authenticated_user(user.username, 'password123')
        response = client.get(url_for('api.get_user', id=user.id))
        assert response.status_code == 200
        assert 'username' in response.json
        assert response.json['username'] == 'test_user'
        assert 'email' in response.json
        assert response.json['email'] == 'test@example.com'