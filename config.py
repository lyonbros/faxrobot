import os
from distutils.util import strtobool

class Config(object):
    JSON_AS_ASCII = False
    DEBUG = strtobool(os.environ.get('DEBUG', 'false'))
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_POOL_RECYCLE = 60 * 60
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    REDIS_URI = os.environ.get('REDIS_URI')