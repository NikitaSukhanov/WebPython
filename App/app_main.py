from flask import Flask, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import json

from mongo_manager import MongoCollectionManager
from quizzes import Question, Quiz
from users import User

app = Flask(__name__)
app.secret_key = 'very secret secret key'
login_manager = LoginManager(app)
login_manager.init_app(app)
# login_manager.login_view = 'login'

questions_collection = MongoCollectionManager(db_name='quiz_db', collection_name='questions')
quizzes_collection = MongoCollectionManager(db_name='quiz_db', collection_name='quizzes')
users_collection = MongoCollectionManager(db_name='quiz_db', collection_name='users')


def dummy_test():
    dummy_question = Question.dummy_question()
    questions_collection.insert(dummy_question.to_dict(player_view=False), dummy_question.qid, replace=True)
    dummy_quiz = Quiz.dummy_quiz()
    quizzes_collection.insert(dummy_quiz.to_dict_db(), dummy_quiz.qid, replace=True)
    dummy_user = User.dummy_user()
    users_collection.insert(dummy_user.to_dict(), dummy_user.get_id(), replace=True)


def extract_quiz(qid):
    quiz_clip = quizzes_collection[qid]
    if not quiz_clip:
        return None
    questions_docs = questions_collection.find_by_id_list(quiz_clip['questions'])
    questions = [Question.from_db_doc(q) for q in questions_docs]
    # if len(questions) != len(quiz_clip['questions']):
    #     pass
    return Quiz.from_db_doc(quiz_clip, questions)


@login_manager.user_loader
def load_user(user_id):
    user_db = users_collection[user_id]
    if not user_db:
        return None
    return User.from_db_doc(user_db)


@app.route('/users', methods=['POST'])
def register():
    name = request.args.get('name', None)
    password = request.args.get('password', None)
    if name is None or password is None:
        return "'name' or 'password' args are missing", 400
    existing_user = users_collection.collection.find_one({"name": name})
    if existing_user:
        return 'This username already exists', 400
    user = User.new_user(name=name, password=password)
    existing_user = users_collection[user.get_id()]
    if existing_user:
        user.props['original_id'] = user.get_id()
        user._id = str(len(users_collection) + 1)
    users_collection.insert(user.to_dict(), user.get_id())
    return 'Registration succeeded'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return 'Already logged in'
    name = request.args.get('name', None)
    password = request.args.get('password', None)
    if name is None or password is None:
        return "'name' or 'password' args is missing", 400
    user_db = users_collection.collection.find_one({"name": name})
    if not user_db:
        return 'User not found', 404
    user = User.from_db_doc(user_db)
    if not user.pass_check(password):
        return 'Invalid password', 400
    login_user(user)
    return 'Logged in successfully'


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    # return redirect(url_for('/'))
    return "You have been logged out"


@app.route('/quizzes/', methods=['GET'])
def get_quiz():
    qid = request.args.get('_id', None)
    if qid is None:
        quizzes = {}
        for q in quizzes_collection:
            qid = q.pop('_id')
            quizzes[qid] = q
        if not quizzes:
            return 'Quizzes list is empty', 404
        return quizzes

    quiz = extract_quiz(qid)
    if not quiz:
        return 'Quiz not found', 404
    player_view = request.args.get('player_view', str(True))
    if player_view not in (str(True), str(False)):
        return "'player_view' must be 'True' or 'False', but it is {}".format(player_view), 400
    player_view = player_view == str(True)
    access_type = Quiz.prop_names.player_access if player_view else Quiz.prop_names.full_access
    access, msg = quiz.check_access(current_user, access_type)
    if access:
        return quiz.to_dict(player_view=player_view)
    else:
        return msg, 401


@app.route('/quizzes/check', methods=['GET', 'POST'])
def check_answers():
    qid = request.args.get('_id', None)
    answers = request.args.get('answers', None)
    if qid is None or answers is None:
        return "'_id' or 'answers' args are missing", 400

    quiz = extract_quiz(qid)
    if not quiz:
        return 'Quiz not found', 404
    access, msg = quiz.check_access(current_user, Quiz.prop_names.player_access)
    if not access:
        return msg, 401

    answers = json.loads(answers)
    result = {}
    for question_id in quiz.question_ids:
        if question_id not in answers.keys():
            result[question_id] = False
        else:
            result[question_id] = quiz[question_id].check(answers[question_id])
    return result


@app.route('/')
def default_handler():
    return 'Hi there'


dummy_test()
if __name__ == '__main__':
    app.run()
