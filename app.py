from flask import Flask, redirect, url_for, request, jsonify, render_template, flash, session, g
import dotenv
from os import getenv
from models import db, User, Blog
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta

app = Flask(__name__)
dotenv.load_dotenv()

db_username = getenv('DB_USERNAME')
db_password = getenv('DB_PASSWORD')
db_host = getenv('DB_HOST')
db_database = getenv('DB_DATABASE')
db_port = getenv('DB_PORT')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_database}'
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///schema.db"

db.init_app(app)

# set secret key to use flash storage
app.config.from_mapping(
    SECRET_KEY='development',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

with app.app_context():
    db.create_all()


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        user = User.query.filter(User.id == user_id).first()
        g.user = user.to_dict()


@app.route('/')
def index():
    blogs = Blog.query.join(User, Blog.author_id == User.id).all()
    return render_template('blog/index.html', blogs=blogs)


@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            return render_template('auth/login.html')
        flash(error)
    return render_template('auth/register.html')


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        user = User.query.filter_by(email=email).first()
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.to_dict()['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session["user_id"] = user.to_dict()['id']
            return redirect(url_for('index'))
        flash(error)
    return render_template('auth/login.html')

@app.route("/auth/logout", methods=["GET"])
def logout(): 
    session.clear()
    return redirect(url_for('login'))
    
    
@app.route("/blog/create", methods=["POST", "GET"])
def create_blog():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        error = None
        if not title:
            error = "Title must be required"
        if error is None:
            blog = Blog(
                title=title,
                content=content,
                author_id=g.user["id"]
            )
            db.session.add(blog)
            db.session.commit() 
        return redirect(url_for('index'))
    return render_template('blog/create.html')

def get_blog(id):
    blog = Blog.query.filter_by(id=id).first()
    return blog
    
@app.route('/blog/detail/<int:id>', methods=['GET'])
def get_blog_detail(id):
    result = db.session.query(Blog, User).join(User, Blog.author_id == User.id).filter(Blog.id==id).first()
    return render_template('blog/detail.html', result=result)

@app.route("/blog/update/<int:id>", methods=["POST", "GET"])
def update_blog(id):
    blog = get_blog(id)
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        error = None
        if not title:
            error = "Title must be required"
        if error is None:
            new_blog = Blog.query.get(id)
            new_blog.title = title
            new_blog.content = content
            db.session.commit() 
        return redirect(url_for('index'))
    return render_template('blog/update.html', blog=blog)

@app.route('/blog/delete/<int:id>', methods=['POST'])
def delete_blog(id):
    return "oke"
    

@app.route('/health-check')
def health_check():
    return jsonify({'status': 200})
