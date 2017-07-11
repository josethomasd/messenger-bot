import os, json, requests
import sys, time

from flask import Flask, request, redirect, url_for, flash
from flask import render_template

from flask import jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, login_required, LoginManager,logout_user

from werkzeug.security import generate_password_hash,check_password_hash

from flask_heroku import Heroku

from forms import Login, Register

app = Flask(__name__)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://tmtfkfkrsfslju:a309076a45cb78b177bb9368b275cfdedf16422d2d01fb8ffc1fee1e7bee604d@ec2-23-23-225-12.compute-1.amazonaws.com:5432/d1g76agkrjaf2o'
heroku = Heroku(app)
db = SQLAlchemy(app)

login_manager= LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)


# Create our database model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(200),nullable=False)
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def __repr__(self):
        return '<title {}'.format(self.name)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login_manager.user_loader
    def load_user(username):
        return User.query.filter_by(username=username).first()


@app.route("/")
def index():  
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    form = Login()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print form.username.data
        if user is not None and user.verify_password(form.password.data):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        error = 'Invalid username or password. Please try again!'
    return render_template("login.html",form=form)

@app.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('/'))
    form = Register()
    error = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if not db.session.query(User).filter(User.username == username).count():
            reg = User(username,password)
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for('login'))
        error = 'User with the same email already exists!'
    return render_template('register.html',title='Register',form=form,error=error)

@app.route('/broadcast')
def broadcast():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("broadcast.html")

@app.route('/manage')
def manage():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("manage.html")

@app.route('/signout')
def logout():
    user1 = current_user
    user1.authenticated = False
    db.session.add(user1)
    db.session.commit()
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":
        if data["entry"][0]["messaging"][0]["sender"]:
            for messaging_event in [0]["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message 
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    message_text = '+'.join(message_text.split(" "))

                    send_message(sender_id, "Check check")
                    #send_state(sender_id)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def send_state(recipient_id):

    log("sending state to {recipient}: ".format(recipient=recipient_id))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action":"typing_on"

    })
    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)