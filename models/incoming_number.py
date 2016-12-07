from models import db
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import SQLAlchemyError

class IncomingNumber(db.Model):
    __tablename__ = 'incoming_number'

    id                      = Column(BigInteger, primary_key=True)
    account_id              = Column(BigInteger, ForeignKey('account.id'))
    account                 = db.relationship('Account', 
                                backref=db.backref('incoming_numbers'))
    fax_number              = Column(String(64), unique=True)
    flagged_for_deletion    = Column(Integer, default=0)
    last_billed             = Column(DateTime)
    create_date             = Column(DateTime)
    mod_date                = Column(DateTime)

    def __init__(self, account_id, fax_number):

        self.create_date        = datetime.now()
        self.last_billed        = datetime.now()
        self.account_id         = account_id
        self.fax_number         = fax_number

    def __repr__(self):
        return "<IncomingNumber(id=%s, account_id=%s, fax_number=%s)>"%\
            (self.id, self.account_id, self.fax_number)