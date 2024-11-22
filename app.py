from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import logging

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/todo_app'  # Adjust if using Atlas
app.secret_key = 'your_secret_key'
mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            return User(str(user['_id']), user['username'])
    except Exception as e:
        logging.error(f"Error loading user: {e}")
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        # Check if the username already exists
        if mongo.db.users.find_one({'username': username}):
            # Optionally, you can flash a message to the user that the username is taken
            return redirect(url_for('register'))
        
        # Insert the new user into the database
        mongo.db.users.insert_one({'username': username, 'password': password})
        
        # Redirect to the login page after successful registration
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find the user in the database
        user = mongo.db.users.find_one({'username': username})
        
        # Check if user exists and password is correct
        if user and check_password_hash(user['password'], password):
            user_obj = User(username)
            login_user(user_obj)
            return redirect(url_for('todo'))  # Redirect to the todo page
        
        # Redirect to the register page if login fails
        if not (user and check_password_hash(user['password'], password)):
            flash('Invalid username or password. Please register if you do not have an account.')
            return redirect(url_for('register'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == 'POST':
        task_content = request.form['content']
        mongo.db.todos.insert_one({'content': task_content, 'user': current_user.username})
        return redirect(url_for('todo'))

    tasks = mongo.db.todos.find({'user': current_user.username})
    return render_template('todo.html', tasks=tasks, str=str)

@app.route('/delete/<task_id>')
@login_required
def delete(task_id):
    mongo.db.todos.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('todo'))

# Routes will be defined here later

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)