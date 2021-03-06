from flask import Flask, render_template, session, redirect, url_for, request, flash, abort, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .. import db
from ..models import Permission, Role, User, Post, Comment, Taxonomy
from ..decorators import admin_required, permission_required

@main.route('/', methods = ['GET', 'POST'])
def index():
	if current_user.can(Permission.WRITE_ARTICLES) and \
			request.method == 'POST':
		post = Post(body=request.form['body'], author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	
	page = request.args.get('page', 1, type=int)
	show_followed = False
	if current_user.is_authenticated:
		show_followed = bool(request.cookies.get('show_followed', ''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
		error_out=False)
	posts = pagination.items
	return render_template('index.html', posts=posts,
	                       show_followed=show_followed, pagination=pagination)







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

@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
	post = Post.query.get_or_404(id)
	if request.method == 'POST':
		comment = Comment(body=request.form['body'], post=post, author=current_user._get_current_object())
		return redirect(url_for('.post', id=post.id, page=-1))
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) / \
			current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items

	return render_template('posts/post.html', posts=[post], id = id, comments=comments, pagination=pagination)


@main.route('/taxonomy', methods=['POST', 'GET'])
def taxonomy():
	if current_user.can(Permission.WRITE_ARTICLES) and request.method == 'POST':
		taxonom = Taxonomy(category=request.form['category'], author=current_user._get_current_object())
		db.session.add(taxonom)
		return redirect(url_for('.taxonomy'))
	taxonomy = Taxonomy.query.order_by(Taxonomy.timestamp.desc()).all()
	return render_template('posts/taxonomy.html', taxonomy=taxonomy)

@main.route('/edit-tax/<int:id>', methods=['POST', 'GET'])
@login_required
def edit_tax(id):
	tax = Taxonomy.query.get_or_404(id)
	if current_user != tax.author and \
		not current_user.can(Permission.ADMINISTER):
		abort(403)
	if request.method == 'POST':
		tax.category = request.form['category']

		db.session.add(tax)
		flash('The category has been updated.')
		return redirect(url_for('.taxonomy', id=tax.id))

	category = tax.category
	return render_template('edit_taxonomy.html', category = category )


@main.route('/del-tax/<int:id>', methods=['GET'])
@login_required
def del_tax(id):
	tax = Taxonomy.query.get_or_404(id)
	if request.method == 'GET':
		db.session.delete(tax)
		flash('The category has been delete.')
		return redirect(url_for('.taxonomy'))





@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and \
			not current_user.can(Permission.ADMINISTER):
		abort(403)

	if request.method == 'POST':
		post.body = request.form['body']

		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('.post', id=post.id))
	body = post.body
	return render_template('edit_post.html', body = body )

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash('You are already following this user.')
		return redirect(url_for('.user', username=username))
	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(url_for('.user', username=username))




@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(
		page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
	follows = [{'user': item.follower, 'timestamp': item.timestamp}
			for item in pagination.items]
	return render_template('followers.html', user=user, title="Followers of",
				endpoint='.followers', pagination=pagination,
				follows=follows)




@main.route('/followed-by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.paginate( page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
	follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
	return render_template('followers.html', user=user, title="Followed by",
			endpoint='.followed_by', pagination=pagination,
			follows=follows)



@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '', max_age=30*24*60*60)
	return resp



@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
	return resp


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		flash('You are not following this user.')
		return redirect(url_for('.user', username=username))
	current_user.unfollow(user)
	flash('You are not following %s anymore.' % username)
	return redirect(url_for('.user', username=username))

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	return redirect(url_for('.moderate',
			page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True
	db.session.add(comment)
	return redirect(url_for('.moderate',
			page=request.args.get('page', 1, type=int)))