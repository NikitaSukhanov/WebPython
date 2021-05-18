import requests
import json

host = 'http://localhost'


def response_print(r):
    print('Request URL: {}'.format(r.request.path_url))
    print('Response text: {}'.format(r.text))
    print('Status code: {}\n'.format(r.status_code))


# get all quizzes
response_print(requests.get(host + '/quizzes'))

# get quiz by wrong id
response_print(requests.get(host + '/quizzes', params={"_id": 'wrong_id'}))

# get player view of quiz
r = requests.get(host + '/quizzes')
quizzes = json.loads(r.text)
quiz_id = list(quizzes.keys())[0]
response_print(requests.get(host + '/quizzes', params={"_id": quiz_id, 'player_view': True}))

# check quiz answers
r = requests.get(host + '/quizzes', params={"_id": quiz_id, 'player_view': True})
quiz = json.loads(r.text)
quiz_id = quiz['_id']
questions = quiz['questions']
answers = {qid: len(q['text']) % len(q['variants']) for qid, q in questions.items()}
answers = json.dumps(answers)
response_print(requests.get(host + '/quizzes/check', params={"_id": quiz_id, 'answers': answers}))

# one more try
answers = {qid: 0 for qid, q in questions.items()}
answers = json.dumps(answers)
response_print(requests.get(host + '/quizzes/check', params={"_id": quiz_id, 'answers': answers}))

# get full view of quiz
response_print(requests.get(host + '/quizzes', params={"_id": quiz_id, 'player_view': False}))

# incorrect player_view
response_print(requests.get(host + '/quizzes', params={"_id": quiz_id, 'player_view': 'Hello'}))

# register new user
username = 'New_user'
password = 'password1234'
response_print(requests.post(host + '/users', params={'name': username, 'password': password}))

# login
response_print(requests.get(host + '/login', params={'name': username, 'password': password}))

# login with incorrect password
response_print(requests.get(host + '/login', params={'name': username, 'password': 'wrong_pass'}))

# logout
response_print(requests.get(host + '/logout'))
