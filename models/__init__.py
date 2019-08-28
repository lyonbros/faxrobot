from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def initialize_database(app):
    from models.account import Account
    from models.job import Job
    from models.transaction import Transaction
    from models.failed_payment import FailedPayment
    from models.password_reset import PasswordReset
    from models.incoming_number import IncomingNumber
    from models.incoming_fax import IncomingFax
    import psycopg2
    import os

    with app.app_context():
        try:
            db.create_all()
            account = Account.query.get(0)
            if not account:
                # insert guest account if needed.
                conn    = psycopg2.connect(os.environ.get('DATABASE_URI'))
                query   = ("INSERT INTO account (id, email, password, api_key) "
                           "VALUES (%s, %s, %s, %s);")
                data    = (0, 'anon@faxrobot.internal', 'trol', 'lol')
                cursor  = conn.cursor()
                cursor.execute(query, data)
                conn.commit()
                conn.close()
        except:
            print("ERROR: COULD NOT AUTO-GENERATE DATABASE TABLES")
            print("Make sure your SQLALCHEMY_DATABASE_URI environment is set!")