from flask import Blueprint

api = Blueprint('api', __name__)


@api.route('/')
def get_homepage():
    return "<h1>Welcome to Backend</h1>"



from . import user, error