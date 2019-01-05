from models import db
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, DateTime, ForeignKey, Text, Float
from sqlalchemy.exc import SQLAlchemyError
from validate_email import validate_email
from library.grab_bag import random_hash, password_hash
from library.errors import ValidationError
import os

default_cost_per_page = float(os.environ.get('DEFAULT_COST_PER_PAGE', '0.10'))

class Account(db.Model):
    __tablename__ = 'account'

    id              = Column(BigInteger, primary_key=True)
    email           = Column(String(255), nullable=False,unique=True,index=True)
    password        = Column(String(64), nullable=False)
    api_key         = Column(String(64), nullable=False,unique=True,index=True)
    credit          = Column(Float, default=0.00)
    base_rate       = Column(Float, default=default_cost_per_page)
    allow_overflow  = Column(SmallInteger, default=0)
    first_name      = Column(String(255))
    last_name       = Column(String(255))
    address         = Column(String(255))
    address2        = Column(String(255))
    city            = Column(String(255))
    state           = Column(String(64))
    zip             = Column(String(24))
    stripe_token    = Column(String(255))
    stripe_card     = Column(String(255))
    last4           = Column(Integer)
    auto_recharge   = Column(SmallInteger, default=0)
    email_success   = Column(SmallInteger, default=1)
    email_fail      = Column(SmallInteger, default=1)
    email_list      = Column(SmallInteger, default=1)
    debug_mode      = Column(SmallInteger, default=0)
    low_priority    = Column(SmallInteger, default=0)
    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)

    def __init__(self, email, password, first_name=None, last_name=None,
            address=None, address2=None, city=None, state=None, zip=None):

        self.create_date    = datetime.now()

        if not email:
            raise ValidationError('ACCOUNTS_MISSING_EMAIL')
        elif not validate_email(email):
            raise ValidationError('ACCOUNTS_BAD_EMAIL')
        else:
            self.email      = email

        if not password:
            raise ValidationError('ACCOUNTS_MISSING_PASSWORD')
        else:
            self.password   = password_hash(password)

        self.api_key        = random_hash("%s%s" % (email, self.password))
        self.first_name     = first_name
        self.last_name      = last_name
        self.address        = address
        self.address2       = address2
        self.city           = city
        self.state          = state
        self.zip            = zip

    def validate(self):

        if not self.email:
            raise ValidationError('ACCOUNTS_MISSING_EMAIL')

        if not validate_email(self.email):
            raise ValidationError('ACCOUNTS_BAD_EMAIL')

        if self.first_name and len(self.first_name) > 255:
            raise ValidationError('ACCOUNTS_BAD_FIRST_NAME')

        if self.last_name and len(self.last_name) > 255:
            raise ValidationError('ACCOUNTS_BAD_LAST_NAME')

        if self.address and len(self.address) > 255:
            raise ValidationError('ACCOUNTS_BAD_ADDRESS')

        if self.address2 and len(self.address2) > 255:
            raise ValidationError('ACCOUNTS_BAD_ADDRESS2')

        if self.city and len(self.city) > 255:
            raise ValidationError('ACCOUNTS_BAD_CITY')

        if self.state and len(self.state) > 64:
            raise ValidationError('ACCOUNTS_BAD_STATE')

        if self.zip and len(self.zip) > 24:
            raise ValidationError('ACCOUNTS_BAD_ZIP')

        if self.email_success and self.email_success != 0 and \
                self.email_success != 1:
            raise ValidationError('ACCOUNTS_BAD_REQUEST')

        if self.email_fail and self.email_fail != 0 and self.email_fail != 1:
            raise ValidationError('ACCOUNTS_BAD_REQUEST')

        if self.email_list and self.email_list != 0 and self.email_list != 1:
            raise ValidationError('ACCOUNTS_BAD_REQUEST')

        return True

    def add_credit(self, amount, session=None):

        if not session:
            session = db.session

        session.query(Account).filter_by(id=self.id).update(
            {Account.credit: Account.credit + amount}
        )
        session.commit()

    def subtract_credit(self, amount, session=None):

        if not session:
            session = db.session

        session.query(Account).filter_by(id=self.id).update(
            {Account.credit: Account.credit - amount}
        )
        session.commit()

    def get_priority(self):

        return "low" if self.low_priority else "default"

    # why have two nearly identical methods doing nearly exactly the same thing?
    # BECAUSE FUCK YOU. that's why.

    def public_data(self):
        """
        Returns a dictionary of fields that are safe to display to the client.
        """

        data = {
            'api_key': self.api_key,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address': self.address,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'credit': self.credit,
            'auto_recharge': self.auto_recharge,
            'has_stripe_token': True if self.stripe_token else False,
            'last4': self.last4,
            'email_success': self.email_success,
            'email_fail': self.email_fail,
            'email_list': self.email_list,
        };

        if len(self.incoming_numbers) > 0:
            data["incoming_number"] = self.incoming_numbers[0].fax_number

        return data;

    @classmethod
    def authorize(cls_obj, api_key, required = False):
        """
        Checks that any given api_key is valid
        """
        if required == False and not api_key:
            return 0 # guest account ID is 0

        accounts = cls_obj.query.filter_by(api_key = api_key)
        return None if accounts.first() == None else accounts.first().id

    def __repr__(self):
        return "<User(id='%s', email='%s')>" % (self.id, self.email)