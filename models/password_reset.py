from models import db
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import SQLAlchemyError
from library.grab_bag import random_hash

class PasswordReset(db.Model):
    __tablename__ = 'password_reset'

    id              = Column(BigInteger, primary_key=True)
    account_id      = Column(BigInteger)
    reset_hash      = Column(String(64),index=True)
    used            = Column(SmallInteger, default=0)
    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)

    def __init__(self, account_id):

        self.create_date = datetime.now()
        self.account_id = account_id
        self.reset_hash = random_hash("%s%s"%(account_id,str(self.create_date)))

    def __repr__(self):
        return "<FailedPayment(id=%s, account_id=%s, used=%s)>"%\
            (self.id, self.account_id, self.used)