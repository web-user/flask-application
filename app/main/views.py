from flask import Flask, render_template, session, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from . import main
from .. import db
from ..models import Permission, Role, User, Post, Comment

@main.route('/', methods = ['GET', 'POST'])
def index():
	if current_user.can(Permission.WRITE_ARTICLES) and \
			request.method == 'POST':
		post = Post(body=request.form['body'], author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	posts = Post.query.order_by(Post.timestamp.desc()).all()
	return render_template('index.html', title = 'Home', posts = posts)

@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', title = 'Profile', user=user, posts=posts)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    
	if request.method == 'POST':
		current_user.name = request.form['name']
		current_user.location = request.form['location']
		current_user.about_me = request.form['about_me']
		db.session.add(current_user)
		flash('Your profile has been updated.')
		return redirect(url_for('.user', username=current_user.username))
	return render_template('edit_profile.html', title = 'Edit')

@main.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	if request.method == 'POST':
		user.email = request.form['email']
		user.username = request.form['username']
		user.confirmed = request.form['confirmed']
		user.role = Role.query.get(request.form['role'])
		user.name = request.form['name']
		user.location = request.form['location']
		user.about_me = request.form['about_me']
		db.session.add(user)
		flash('The profile has been updated.')
		return redirect(url_for('.user', username=user.username))

	# form.email.data = user.email
	# form.username.data = user.username
	# form.confirmed.data = user.confirmed
	# form.role.data = user.role_id
	# form.name.data = user.name
	# form.location.data = user.location
	# form.about_me.data = user.about_me

	form_edit = {
		'email': user.email
	}

	return render_template('edit_profile.html', title = 'Profile Admin', form_edit = form_edit)




















