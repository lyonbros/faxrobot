from models import db
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import SQLAlchemyError

class FailedPayment(db.Model):
    __tablename__ = 'failed_payment'

    id              = Column(BigInteger, primary_key=True)
    account_id      = Column(BigInteger)
    amount          = Column(Float)
    source          = Column(String(10))
    debug           = Column(Text)
    ip_address      = Column(String(255))
    payment_type    = Column(String(64))
    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)

    def __init__(self, amount, account_id=None, source=None, debug=None,
            ip_address=None, payment_type=None):

        self.create_date        = datetime.now()
        self.account_id         = account_id
        self.amount             = amount
        self.source             = source
        self.debug              = debug
        self.ip_address         = ip_address
        self.payment_type       = payment_type

    def __repr__(self):
        return "<FailedPayment(id=%s, account_id=%s, amount=%s, source='%s')>"%\
            (self.id, self.account_id, self.amount, self.source)