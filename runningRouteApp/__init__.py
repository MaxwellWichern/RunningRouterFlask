from flask import Blueprint

bp = Blueprint('runner', __name__, template_folder='templates')

from . import views