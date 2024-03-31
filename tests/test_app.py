from app.model import User

def test_user_registration(client):
    data = {
        'username': 'test user',
        'email': 'test@gmail.com',
        'password': 'password',
        'confirm_password': 'password'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    
