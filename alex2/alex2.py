# -*- coding: utf-8 -*-
"""
	alex2
	~~~~~~~~

	A microblogging application written with Flask and sqlite3.

	:copyright: (c) 2015 by Armin Ronacher.
	:license: BSD, see LICENSE for more details.
"""

import time
import json
import os
import random
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
	 render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room, \
	close_room, rooms, disconnect

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

# configuration
DATABASE = os.getcwd() + '/alex2.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
PROBLEM_TESTS_FOLDER = os.getcwd() + '/alex2/problem_tests'
ALEX = "Alex"

# create our little application :)
app = Flask('alex2')
app.config.from_object(__name__)
app.config.from_envvar('alex2_SETTINGS', silent=True)

socketio = SocketIO(app, async_mode=async_mode)
thread = None

################## set up #################
def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	top = _app_ctx_stack.top

	if not hasattr(top, 'sqlite_db'):
		top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
		top.sqlite_db.row_factory = sqlite3.Row
	return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
	"""Closes the database again at the end of the request."""
	top = _app_ctx_stack.top
	if hasattr(top, 'sqlite_db'):
		top.sqlite_db.close()


def init_db():
	"""Initializes the database."""
	db = get_db()
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

# def seed_smart_ass():

# 	db = get_db()
# 	db.execute('''insert into user (
# 		username, email, pw_hash) values (?, ?, ?)''',
# 		['jennie', 'jli488@gatech.edu',
# 		generate_password_hash('jennie')])

# 	for problem_id in range(1, 10):

# 		db.execute('''insert into user_problem_solution (user_id, problem_id, submittedAt, passed, score) values (?, ?, ?, ?, ?)''',
# 			[1, problem_id, time.time(), True, 1.0])
# 		Problem.incr(problem_id, 'num_users')
# 		Problem.incr(problem_id, 'num_users_passed')
# 	db.commit()


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	init_db()
	print('Initialized the database.')

def seed_db():
	"""Seeds the database."""
	db = get_db()
	with app.open_resource('seed.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()
	# seed_smart_ass()

@app.cli.command('seeddb')
def seeddb_command():
	"""Seeds the database tables."""
	seed_db()
	print('Seeded the database.')

def query_db(query, args=(), one=False):
	"""Queries the database and returns a list of dictionaries."""
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	return (rv[0] if rv else None) if one else rv

def format_datetime(timestamp):
	"""Format a timestamp for display."""
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

def gravatar_url(email, size=80):
	"""Return the gravatar image for the given email address."""
	return 'https://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
		(md5(email.strip().lower().encode('utf-8')).hexdigest(), size)
 
################## models ##########################
class User:

	@classmethod
	def get_user_id(cls, username):
		"""Convenience method to look up the id for a username."""
		rv = query_db('select user_id from user where username = ?',[username], one=True)
		return rv['user_id'] if rv else None
	   
	@classmethod
	def get(cls, user_id):
		return query_db('select * from user where user_id = ?', [user_id], one=True)
 
	@classmethod
	def select_a_problem_for_user(cls, user_id):

		all_problems = UserProblemSolution.get_by_user(user_id)
		if not all_problems:
			problem_id = 1
			UserProblemSolution.create(user_id, problem_id)
		else:
			failed_problems = [problem for problem in all_problems if not problem['submittedAt'] or not problem['passed']]
			if failed_problems:
				problem_id = failed_problems[0]['problem_id']
				#audit 
			else:
				problem = Problem.get_next(all_problems[-1]['problem_id'])
				if problem:
					UserProblemSolution.create(user_id, problem['problem_id'])
				return problem
		return Problem.get(problem_id)

class UserProblemSolution:

	@classmethod
	def create(cls, user_id, problem_id):
		db = get_db()
		db.execute('''insert into user_problem_solution (user_id, problem_id) values (?, ?)''',
			[user_id, problem_id])
		db.commit()
		Problem.incr(problem_id, 'num_users')

	@classmethod
	def get_by_user(cls, user_id):
		return query_db('select * from user_problem_solution where user_id = ?',[user_id])

	@classmethod
	def get_by_user_and_problem(cls, user_id, problem_id):
		return query_db('select * from user_problem_solution where user_id = ? and problem_id = ?',[user_id, problem_id], one=True)	
	
	@classmethod
	def update(cls, user_id, problem_id, passed, score):
		with_study_buddy = session.has_key('room')
		db = get_db()
		db.execute('''update user_problem_solution 
			set submittedAt = datetime(), passed = ?, score = ?, with_study_buddy = ?
			where user_id = ? and problem_id = ? ''',
			[passed, score, with_study_buddy, user_id, problem_id])
		db.commit()

		if passed:
			Problem.incr(problem_id, 'num_users_passed')
		else:
			Problem.incr(problem_id, 'num_users_failed')

	@classmethod
	def get_tutor(cls, problem_id):
		return query_db('select * from user_problem_solution where user_id = ? and problem_id = ?',[user_id, problem_id], one=True)	
	

class UserTestSolution:

	@classmethod
	def create(cls, user_id, problem_id, test_id, passed, score):
		with_study_buddy = session.has_key('room')
		db = get_db()
		db.execute('''insert into user_test_solution (user_id, problem_id, test_id, passed, score, with_study_buddy) values (?, ?, ?, ?, ?, ?)''',
			[user_id, problem_id, test_id, passed, score, with_study_buddy])
		db.commit()

class Problem:

	name = ""
	description = ""
	func_prefix = ""
	level = 0

	@classmethod
	def get(cls, problem_id):
		return query_db('select * from problem where problem_id = ?', [problem_id], one=True)

	@classmethod
	def get_all(cls):
		return query_db('select * from problem')

	@classmethod
	def get_next(cls, problem_id):
		try:
			return query_db('select * from problem where problem_id = ?', [problem_id + 1], one=True)
		except TypeError:
			return None

	@classmethod
	def incr(cls, problem_id, fieldname):
		db = get_db()
		update = 'update problem set {} = {} + 1 where problem_id = ?'.format(fieldname, fieldname)
		db.execute(update,[problem_id])
		db.commit()



class Test:
	@classmethod
	def get(cls, filename):
		with open ("{}/{}".format(PROBLEM_TESTS_FOLDER, filename), "r") as myfile:
			data = json.load(myfile)

		return data


class UserProblemStudyBuddy:

	@classmethod
	def create(cls, student_id, problem_id, room):
		db = get_db()
		db.execute('''insert into user_problem_study_buddy (student_id, problem_id, room) values (?, ?, ?)''',
			[student_id, problem_id, room])
		db.commit()

	@classmethod
	def update_open_room_teacher(cls, id, teacher_id):
		db = get_db()
		db.execute('''update user_problem_study_buddy set teacher_id =? where id = ?''',
			[teacher_id, id])
		db.commit()

	@classmethod
	def leave_room_teacher(cls, id):
		db = get_db()
		db.execute('''update user_problem_study_buddy set teacher_id =NULL where id = ?''',
			[id])
		db.commit()

	@classmethod
	def get_open_room(cls, problem_id):
		return query_db('select * from user_problem_study_buddy where problem_id = ? and teacher_id is NULL order by createdAt ASC', [problem_id], one=True)


	@classmethod
	def get_first_in_queue_open_room(cls):
		return query_db('select * from user_problem_study_buddy where teacher_id is NULL order by createdAt ASC', one=True)

	@classmethod
	def get_my_open_room(cls, student_id, problem_id):
		return query_db('select * from user_problem_study_buddy where problem_id = ? and student_id =? and teacher_id is NULL order by createdAt ASC', [problem_id, student_id], one=True)



################### auth #############################

@app.before_request
def before_request():
	g.user = None
	if 'user_id' in session:
		g.user = User.get(session['user_id'])
		if g.user:
			session['username'] = g.user['username']

@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	error = None
	if request.method == 'POST':
		user = query_db('''select * from user where
			username = ?''', [request.form['username']], one=True)
		if user is None:
			error = 'Invalid username'
		elif not check_password_hash(user['pw_hash'],
									 request.form['password']):
			error = 'Invalid password'
		else:
			flash('You were logged in')
			session['user_id'] = user['user_id']
			return redirect(url_for('problem'))
	return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers the user."""
	if g.user:
		return redirect(url_for('problem'))
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['email'] or \
				'@' not in request.form['email']:
			error = 'You have to enter a valid email address'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif User.get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			db = get_db()
			db.execute('''insert into user (
			  username, email, pw_hash) values (?, ?, ?)''',
			  [request.form['username'], request.form['email'],
			   generate_password_hash(request.form['password'])])
			db.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)

@app.route('/logout')
def logout():
	"""Logs the user out."""
	flash('You were logged out')
	session.pop('user_id', None)

	return redirect(url_for('public'))

################ route ######################

@app.route('/public')
def public():
	"""Displays the latest messages of all users."""
	problems = Problem.get_all()
	return render_template('public.html', problems =problems)

@app.route('/')
def problem():
	"""
	"""
	if not g.user:
		return redirect(url_for('public'))

	problem = User.select_a_problem_for_user(session['user_id'])
	if not problem:
		return render_template('all_done.html')
	return render_template('problem.html', problem=problem)

@app.route("/solutions/<problem_id>", methods=['POST'])
def post_solution(problem_id):

	if not g.user:
		return redirect(url_for('public'))

	solution = request.form['solution']

	problem = Problem.get(problem_id)
	user_problem_solution = UserProblemSolution.get_by_user_and_problem(session['user_id'], problem_id)

	# To-DO: Security

	try:
		code = compile(request.form['solution'], "", "exec")
		exec(code)
	except (IndentationError, SyntaxError) as e:
		return render_template('problem.html', problem=problem, 
			solution=solution, exception=e.message)

	tests_results = []

	passed = 0

	for idx, test in enumerate(Test.get(problem['tests_filename'])):
		test_result = {}
		try: 
			output = func(**test['input'])
			if output == test['output']:
				UserTestSolution.create(session['user_id'], problem_id, idx, True, 100)
				test_result['status'] = "pass"
				passed += 1
			else:
				UserTestSolution.create(session['user_id'], problem_id, idx, False, 0)
				test_result['status'] ="failed"
			
		except Exception, e:
			UserTestSolution.create(session['user_id'], problem_id, idx, False, 0)
			test_result['status'] ="failed"

		test_result['output'] = output
		test_result['hint'] = test['hint']
		tests_results.append(test_result)
			
	UserProblemSolution.update(session['user_id'], problem_id, (passed == idx+1), passed/(idx+1))

	show_chat = False
	show_hint = False
	# all passed
	if passed == idx+1:
		flash('Woohoo! All Correct!')
		result = UserProblemStudyBuddy.get_first_in_queue_open_room()
		if result:
			# ask to permission to help another student
			return redirect(url_for('chat', problem_id=result['problem_id']))
		else:
			return redirect(url_for('problem'))
	else:
		# random_factor = random.randint(1, 100)
		# show_chat = (random_factor % 3 == 0) 
		show_chat = (g.user['user_id'] % 3 == 0)
		show_hint = not show_chat

	return render_template('problem.html', problem=problem, 
		solution=solution, tests_results=tests_results, show_chat=show_chat, show_hint=show_hint)

@app.route("/chat/<problem_id>")
def chat(problem_id):
	problem = Problem.get(problem_id)
	return render_template('chat.html', problem=problem)

################ SocketIO ######################
@socketio.on('join_as_student', namespace='/test')
def join_as_student(message):
	problem_id = message['problem_id']
	student_id = message['student_id']

	result = UserProblemStudyBuddy.get_my_open_room(student_id, problem_id)

	if not result:
		now = time.time()
		room = '{}_{}_{}'.format(student_id, problem_id, now)
		UserProblemStudyBuddy.create(student_id, problem_id, room)
	else:
		room = result['room']

	session['room'] = room

	join_room(room)
	emit('my_response',
	     {'data': 'Hey, {}. I\'m inviting a study buddy to join this chat. Please wait.'.format(session['username']),
	      'username': ALEX})

@socketio.on('join_as_teacher', namespace='/test')
def join_as_teacher(message):
	problem_id = message['problem_id']
	teacher_id = message['teacher_id']
	result = UserProblemStudyBuddy.get_open_room(int(problem_id))
	if result:
		UserProblemStudyBuddy.update_open_room_teacher(result['id'], teacher_id)
		session['room'] = result['room']
		student = User.get(result['student_id'])

		join_room(result['room'])
		# session['receive_count'] = session.get('receive_count', 0) + 1
		emit('my_response',
	     {'data': 'Hey, {}. Thanks for being a study buddy!'.format(session['username']),
	      'username': ALEX})
		emit('my_response',
			 {'data': 'Hey, {}. You are now connected with your study buddy {}. Say Hi and happy hacking!'.format(student['username'], session['username']),
			  'username': ALEX},room=session['room'])

@socketio.on('leave_as_student', namespace='/test')
def leave_as_student(message):
	emit('my_response',
		 {'data': 'Hey, unfortunately {} has left the chat.'.format(session['username']),
		  'username': ALEX},
		  room=session['room'])
	session.pop('room')

@socketio.on('leave_as_teacher', namespace='/test')
def leave_as_teacher(message):
	problem_id = message['problem_id']
	UserProblemStudyBuddy.leave_room_teacher(problem_id)
	emit('my_response',
		 {'data': 'Hey, unfortunately {} has left the chat. I\'m connecting you with someone else'.format(session['username']),
		  'username': ALEX},
		  room=session['room'])
	emit('redirect', {'url': url_for('problem')})
	session.pop('room')


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
	if session.has_key('room'):
		emit('my_response',
			{'data': message['data'], 'username': session['username']},
			room=session['room'])

# @socketio.on('leave', namespace='/test')
# def leave(message):
# 	leave_room(message['room'])
# 	session['receive_count'] = session.get('receive_count', 0) + 1
# 	emit('my_response',
# 		 {'data': 'In rooms: ' + ', '.join(rooms()),
# 		  'count': session['receive_count']})


# @socketio.on('close_room', namespace='/test')
# def close(message):
# 	session['receive_count'] = session.get('receive_count', 0) + 1
# 	emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
# 						 'count': session['receive_count']},
# 		 room=message['room'])
# 	close_room(message['room'])


# @socketio.on('disconnect_request', namespace='/test')
# def disconnect_request():
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'Disconnected!', 'count': session['receive_count']})
#     disconnect()


# @socketio.on('my_ping', namespace='/test')
# def ping_pong():
#     emit('my_pong')


# @socketio.on('connect', namespace='/test')
# def test_connect():
#     global thread
#     if thread is None:
#         thread = socketio.start_background_task(target=background_thread)
#     emit('my_response', {'data': 'Connected', 'count': 0})


# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected', request.sid)

# @app.route('/<username>')
# def user_timeline(username):
#     """Display's a users tweets."""
#     profile_user = query_db('select * from user where username = ?',
#                             [username], one=True)
#     if profile_user is None:
#         abort(404)
#     followed = False
#     if g.user:
#         followed = query_db('''select 1 from follower where
#             follower.who_id = ? and follower.whom_id = ?''',
#             [session['user_id'], profile_user['user_id']],
#             one=True) is not None
#     return render_template('timeline.html', messages=query_db('''
#             select message.*, user.* from message, user where
#             user.user_id = message.author_id and user.user_id = ?
#             order by message.pub_date desc limit ?''',
#             [profile_user['user_id'], PER_PAGE]), followed=followed,
#             profile_user=profile_user)


# @app.route('/<username>/follow')
# def follow_user(username):
#     """Adds the current user as follower of the given user."""
#     if not g.user:
#         abort(401)
#     whom_id = get_user_id(username)
#     if whom_id is None:
#         abort(404)
#     db = get_db()
#     db.execute('insert into follower (who_id, whom_id) values (?, ?)',
#               [session['user_id'], whom_id])
#     db.commit()
#     flash('You are now following "%s"' % username)
#     return redirect(url_for('user_timeline', username=username))


# @app.route('/<username>/unfollow')
# def unfollow_user(username):
#     """Removes the current user as follower of the given user."""
#     if not g.user:
#         abort(401)
#     whom_id = get_user_id(username)
#     if whom_id is None:
#         abort(404)
#     db = get_db()
#     db.execute('delete from follower where who_id=? and whom_id=?',
#               [session['user_id'], whom_id])
#     db.commit()
#     flash('You are no longer following "%s"' % username)
#     return redirect(url_for('user_timeline', username=username))


# @app.route('/add_message', methods=['POST'])
# def add_message():
#     """Registers a new message for the user."""
#     if 'user_id' not in session:
#         abort(401)
#     if request.form['text']:
#         db = get_db()
#         db.execute('''insert into message (author_id, text, pub_date)
#           values (?, ?, ?)''', (session['user_id'], request.form['text'],
#                                 int(time.time())))
#         db.commit()
#         flash('Your message was recorded')
#     return redirect(url_for('timeline'))



# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url
