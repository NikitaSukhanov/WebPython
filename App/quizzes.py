from copy import deepcopy
from collections import namedtuple
from enum import Enum

from utils import string_encode, doc_key_error


class Question:

    def __init__(self, _id, text, variants, ans, **kwargs):
        self._id = _id
        self.text = str(text)
        self.variants = list(map(str, variants))
        self.ans = ans
        if not 0 <= self.ans < len(self.variants):
            raise IndexError("'ans' must be a valid index on 'variants': "
                             "ans = {}, len(variants) = {}.".format(ans, len(variants)))
        self.props = kwargs

    def __str__(self):
        return str(self.__dict__)

    @property
    def qid(self):
        return self._id

    def check(self, ans):
        return self.ans == ans

    def to_dict(self, player_view=True):
        d = deepcopy(self.__dict__)
        props = d.pop('props')
        if player_view:
            d.pop('ans')
        else:
            d.update(props)
        return d

    @classmethod
    def from_db_doc(cls, document):
        for field in '_id', 'text', 'variants', 'ans':
            if document.get(field, None) is None:
                doc_key_error(field)
        return cls(**document)

    @classmethod
    def new_question(cls, text, variants, ans, **kwargs):
        _id = string_encode(text)
        return cls(_id=_id, text=text, variants=variants, ans=ans, **kwargs)

    @classmethod
    def dummy_question(cls):
        text = 'Is this dummy question?'
        variants = ['Yes', 'No', 'Maybe']
        ans = 0
        return cls.new_question(text, variants, ans, category='dummy')


class Quiz:
    class AccessTypes(Enum):
        ANONYMOUS = 'anonymous'
        BLACKLIST = 'blacklist'
        WHITELIST = 'whitelist'

    _PropNames = namedtuple('_PropNames', ['player_access', 'full_access'])
    prop_names = _PropNames(player_access='player_access', full_access='full_access')

    def __init__(self, _id, name, questions, **kwargs):
        self._id = _id
        self.name = str(name)
        self.questions = {q.qid: deepcopy(q) for q in questions}
        self.props = deepcopy(kwargs)

        bl_str = Quiz.AccessTypes.BLACKLIST.value
        wl_str = Quiz.AccessTypes.WHITELIST.value

        player_access = self.props.setdefault(Quiz.prop_names.player_access, {bl_str: list()})
        full_access = self.props.setdefault(Quiz.prop_names.full_access, {wl_str: list()})
        for d in player_access, full_access:
            if wl_str in d.keys():
                d.pop(bl_str, None)

    def __len__(self):
        return len(self.questions)

    def __iter__(self):
        return self.questions

    def __getitem__(self, question_id):
        return self.questions.get(question_id)

    @property
    def qid(self):
        return self._id

    @property
    def question_ids(self):
        return self.questions.keys()

    def to_dict(self, player_view=True):
        d = deepcopy(self.__dict__)
        props = d.pop('props')
        if not player_view:
            d.update(props)
        questions = {}
        for qid, q in d['questions'].items():
            q = q.to_dict(player_view)
            _id = q.pop('_id')
            if _id != qid:
                raise KeyError('ID mismatch')
            questions[qid] = q
        d['questions'] = questions
        return d

    def to_dict_db(self):
        d = deepcopy(self.__dict__)
        d.update(d.pop('props'))
        d['questions'] = list(self.question_ids)
        return d

    def check_access(self, user, access_type):
        access = self.props.get(access_type, None)
        if access and Quiz.AccessTypes.ANONYMOUS.value not in access.keys():
            if user.is_anonymous:
                return False, 'This content is only for authorized users'
            if Quiz.AccessTypes.WHITELIST.value in access.keys():
                if user.get_id() not in access[Quiz.AccessTypes.WHITELIST.value]:
                    return False, 'You must be in whitelist for this content'
            if Quiz.AccessTypes.BLACKLIST.value in access.keys():
                if user.get_id() in access[Quiz.AccessTypes.BLACKLIST.value]:
                    return False, 'You are in blacklist for this content'
        return True, 'Access granted'

    @classmethod
    def from_db_doc(cls, document, questions):
        for field in '_id', 'name':
            if document.get(field, None) is None:
                doc_key_error(field)
        document['questions'] = questions
        return cls(**document)

    @classmethod
    def new_quiz(cls, name, questions, **kwargs):
        _id = string_encode(name)
        return cls(_id=_id, name=name, questions=questions, **kwargs)

    @classmethod
    def dummy_quiz(cls):
        name = 'Dummy quiz'
        questions = [Question.dummy_question()]
        player_access = {Quiz.AccessTypes.ANONYMOUS.value: []}
        full_access = {Quiz.AccessTypes.BLACKLIST.value: []}
        kwargs = {'category': 'dummy', Quiz.prop_names.player_access: player_access,
                  Quiz.prop_names.full_access: full_access}
        return cls.new_quiz(name, questions, **kwargs)
