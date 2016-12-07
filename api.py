from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify, Response
from flask.ext.cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db, initialize_database
import sys

app = Flask(__name__)
cors = CORS(app, allow_headers='Content-Type, Origin, Accept')
app.config.from_object('config.Config')
db.init_app(app)
initialize_database(app)

from controllers.jobs import jobs as jobs_module
from controllers.accounts import accounts as accounts_module
from controllers.incoming import incoming as incoming_module

app.register_blueprint(jobs_module)
app.register_blueprint(accounts_module)
app.register_blueprint(incoming_module)

if __name__ == '__main__':
    if app.config['DEBUG'] == True:
        print >> sys.stderr, 'Running locally in debug mode.'
        app.run('0.0.0.0', 9001)
    else:
        app.run()