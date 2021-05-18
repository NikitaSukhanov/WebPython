from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from utils import string_encode, doc_key_error


class User(UserMixin):
    def __init__(self, _id, name, pass_hash, **kwargs):
        self._id = _id
        self.name = str(name)
        self.pass_hash = pass_hash
        self.props = kwargs

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    def pass_check(self, password):
        return check_password_hash(self.pass_hash, password)

    def to_dict(self):
        d = self.__dict__.copy()
        d.update(d.pop('props'))
        return d

    @classmethod
    def from_db_doc(cls, document):
        for field in '_id', 'name', 'pass_hash':
            if document.get(field, None) is None:
                doc_key_error(field)
        return cls(**document)

    @classmethod
    def new_user(cls, name, password, **kwargs):
        _id = string_encode(name)
        pass_hash = generate_password_hash(password)
        return cls(_id=_id, name=name, pass_hash=pass_hash, **kwargs)

    @classmethod
    def dummy_user(cls):
        name = 'Dummy_user'
        password = '123'
        return cls.new_user(name, password, favorite_color='blue')
