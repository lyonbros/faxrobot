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
from library.grab_bag import o

engine = create_engine(os.environ.get('DATABASE_URI').strip())
Session = sessionmaker(bind=engine)
session = Session()

def charge_subscribers():

    o("QUERYING INCOMING FAX NUMBERS FOR PAYMENT PROCESSING!")
    o(" ")

    conn    = psycopg2.connect(os.environ.get('DATABASE_URI'))
    query   = (
              "SELECT   id, account_id, fax_number, flagged_for_deletion,      "
              "         last_billed, create_date, mod_date                     "
              "FROM     incoming_number                                        "
              "WHERE    (                                                      "
              "             mod_date IS NULL                                   "
              "             OR                                                 "
              "             mod_date < now() - \'7 days\'::interval            "
              "         )                                                      "
              "AND      (                                                      "
              "             last_billed IS NULL                                "
              "             OR                                                 "
              "             last_billed < now() - \'30 days\'::interval        "
              "         )                                                      "
              )
    
    cursor  = conn.cursor()
    cursor.execute(query)

    for row in cursor:
        id                      = row[0]
        account_id              = row[1]
        fax_number              = row[2]
        flagged_for_deletion    = row[3]
        last_billed             = row[4]

        account = session.query(Account).get(account_id)
        incoming_number = session.query(IncomingNumber).get(id)

        account_status = "SUCCESS"

        o("Fax number %s for account %s" % (fax_number, account_id))

        if account.credit < 6 and not account.allow_overflow:

            o(" - account credit below threshold")

            if account.stripe_card and account.auto_recharge:
                if not auto_recharge(account, "localhost", session) == True:
                    account_status = "DECLINE"
                    o(" - CARD DECLINED :(")
                else:
                    o(" - payment succeeded :)")
            else:
                account_status = "NO_FUNDS"
                o(" - AUTO-CHARGED DISABLED AND NO FUNDS IN ACCOUNT :(")

        if not account_status == "SUCCESS" and flagged_for_deletion:

            o(" - number is already marked for deletion >_<")

            session.delete(incoming_number)
            session.commit()

            if not delete_number_from_phaxio(fax_number):
                email_admin("Failed to delete Phaxio number: %s" % fax_number)

            email_deleted_number(account)

            o(" - deleted number and emailed customer.")

        elif not account_status == "SUCCESS" and not flagged_for_deletion:

            incoming_number.mod_date = datetime.now()
            incoming_number.flagged_for_deletion = 1
            session.commit()

            email_pending_deletion_warning(account, account_status, fax_number)

            o(" - flagged number for deletion, emailed warning to customer.")

        else:

            o(" - account successfully charged. hooray!")

            incoming_number.mod_date = datetime.now()
            incoming_number.last_billed = datetime.now()
            incoming_number.flagged_for_deletion = 0
            session.commit()

            data = {
                'account_id':       account.id,
                'amount':           -6.00,
                'source':           "phaxio",
                'source_id':        fax_number,
                'ip_address':       "localhost",
                'initial_balance':  account.credit,
                'trans_type':       "incoming_autopay"
            }
            trans = Transaction(**data)
            session.add(trans)
            session.commit()

            account.subtract_credit(6, session)

        o(" ")

    conn.commit()
    conn.close()

    email_admin("YAY!", "Payments cron job success!")

    o("ALL DONE!")
    return "lulz"
