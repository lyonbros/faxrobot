from controllers.incoming import auto_recharge, delete_number_from_phaxio
from models.account import Account
from models.incoming_number import IncomingNumber
from models.transaction import Transaction
from library.mailer import email_admin, email_deleted_number, \
                           email_pending_deletion_warning
import psycopg2
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

engine = create_engine(os.environ.get('DATABASE_URI').strip())
Session = sessionmaker(bind=engine)
session = Session()

new_price = float(os.environ.get('DEFAULT_COST_PER_PAGE'))

print "NEW PRICE IS %s" % new_price
print "QUERYING USERS WHO HAVE OLD PRICE RATE"
print " "

conn    = psycopg2.connect(os.environ.get('DATABASE_URI'))
query   = (
          "SELECT   id, base_rate, credit, email, create_date, mod_date        "
          "FROM     account                                                    "
          )
cursor  = conn.cursor()
cursor.execute(query, (float(new_price),))

for row in cursor:
    id                      = row[0]
    base_rate               = row[1]
    credit                  = row[2]
    email                   = row[3]

    if not base_rate or not base_rate < new_price:
        continue
    
    print "Found account %s: %s" % (id, email)
    print " - base_rate:  %s" % base_rate
    print " - credit:     %s" % credit
    

conn.commit()
conn.close()

print "ALL DONE!"