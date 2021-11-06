from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'swordfish'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'fernando'
app.config['MYSQL_PASSWORD'] = 'r!p2Pjedka'
app.config['MYSQL_DB'] = 'auth_db'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE usuario = %s AND senha = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['usuario']
            # Redirect to home page
            return redirect(url_for('inicio'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Usuário e/ou senha incorretos!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

    # http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('usuario', None)

   # Redirect to login page
   return redirect(url_for('login'))

   # http://localhost:5000/cadastro - this will be the registration page, we need to use both GET and POST requests
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Verifique se a conta existe usando MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE usuario = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Essa conta já existe!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Endereço de e-mail inválido!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'O nome de usuário deve conter apenas caracteres e números!'
        elif not username or not password or not email:
            msg = 'Por favor, preencha o formulário!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO contas VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'Cadastro realizado com sucesso!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Por favor, preencha o formulário!'
    # Show registration form with message (if any)
    return render_template('cadastro.html', msg=msg)

# http://localhost:5000/inicio - this will be the home page, only accessible for loggedin users
@app.route('/inicio')
def inicio():
    # Verifica se o usuário está logado
    if 'loggedin' in session:
        # Usuário está logado, exibe a página inicial
        return render_template('inicio.html', username=session['username'])
    # Usuário não está logado, redirecionar para a página de login
    return redirect(url_for('login'))

# http://localhost:5000/perfil - this will be the profile page, only accessible for loggedin users
@app.route('/perfil')
def perfil():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM contas WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('perfil.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


