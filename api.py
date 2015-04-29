from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify, Response
from flask.ext.cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db
import sys

app = Flask(__name__)
cors = CORS(app, allow_headers='Content-Type, Origin, Accept')
app.config.from_object('config.Config')
db.init_app(app)

from models.account import Account
from models.job import Job
from models.transaction import Transaction
from models.failed_payment import FailedPayment
from models.password_reset import PasswordReset

with app.app_context():
    db.create_all()

from controllers.jobs import jobs as jobs_module
from controllers.accounts import accounts as accounts_module

app.register_blueprint(jobs_module)
app.register_blueprint(accounts_module)

if __name__ == '__main__':
    if app.config['DEBUG'] == True:
        print >> sys.stderr, 'Running locally in debug mode.'
        app.run('0.0.0.0', 9001)
    else:
        app.run()