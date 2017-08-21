import os, json, requests
import sys, time
import urllib

from flask import Flask, request, redirect, url_for, flash
from flask import render_template

from flask import jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, login_required, LoginManager,logout_user

from werkzeug.security import generate_password_hash,check_password_hash

from flask_heroku import Heroku

from forms import Login, Register, Broadcast, Posts_form

app = Flask(__name__)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://tmtfkfkrsfslju:a309076a45cb78b177bb9368b275cfdedf16422d2d01fb8ffc1fee1e7bee604d@ec2-23-23-225-12.compute-1.amazonaws.com:5432/d1g76agkrjaf2o'
heroku = Heroku(app)
db = SQLAlchemy(app)

login_manager= LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

page_id = "268370650303176_"
# Create our database model
class User(db.Model):
    __tablename__ = "login_db"
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

class User_id(db.Model):
    __tablename__ = 'user_id'

    name = db.Column(db.String(30), primary_key=True)
    comment_id = db.Column(db.String(100), nullable=False)
    message_id = db.Column(db.String(100), nullable=False)
    last_msg = db.Column(db.String(50), nullable=False)
    auto_response = db.Column(db.Integer, nullable=False)
    def __init__(self, name, comment_id, message_id, last_msg, auto_response):
        self.name = name
        self.comment_id = comment_id
        self.message_id = message_id
        self.last_msg = last_msg
        self.auto_response = auto_response

    def __repr__(self):
        return '<name {}>'.format(self.name)

class Posts(db.Model):
    __tablename__ = 'posts'

    post_id = db.Column(db.String(100), primary_key=True)

    def __init__(self, post_id):
        self.post_id = post_id
        
    def __repr__(self):
        return '<name {}>'.format(self.post_id)

class Bot_status(db.Model):
    __tablename__ = 'bot_status'

    status = db.Column(db.String(10), primary_key=True)

    def __init__(self, post_id):
        self.status = status
        
    def __repr__(self):
        return '<name {}>'.format(self.status)

@app.route("/")
def index():
    b_status = None  
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    bot_status = Bot_status.query.first()
    if(bot_status.status =="on"):
        b_status = "on"
    return render_template("index.html",bot_status=bot_status.status, b_status=b_status)

@app.route("/bot_on")
def bot_on(): 
    db.session.query(Bot_status).update({"status": u"on"})
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/bot_off")
def bot_off(): 
    db.session.query(Bot_status).update({"status": u"off"})
    db.session.commit()
    return redirect(url_for('index'))
    
@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    form = Login()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        error = 'Invalid username or password. Please try again!'
    return render_template("login.html",form=form,error=error)

@app.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('/'))
    form = Register()
    error = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        bot_status = "on"
        if not db.session.query(User).filter(User.username == username).count():
            reg = User(username,password,bot_status)
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for('login'))
        error = 'User with the same username already exists!'
    return render_template('register.html',title='Register',form=form,error=error)

@app.route('/broadcast', methods=['GET', 'POST'])
def broadcast():
    msg = None
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = Broadcast()
    if form.validate_on_submit():
        message_text = form.broadcast_text.data
        users = User_id.query.all()
        for user in users:
            send_message(user.message_id, message_text)
        msg = "Message broadcasted"

    return render_template("broadcast.html", form=form, msg=msg)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    msg = None
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = Posts_form()
    if form.validate_on_submit():
        post_id = form.post_id.data
        post_id = page_id+post_id
        if not db.session.query(Posts).filter(Posts.post_id == post_id).count():
            add_post = Posts(post_id)
            db.session.add(add_post)
            db.session.commit()
            msg = "Post added"
    return render_template("manage.html", form=form, msg=msg)

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

    return "ok", 200

@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    def generate():
        base_url = "https://graph.facebook.com/v2.8/"
        access_token = os.environ["PAGE_ACCESS_TOKEN"]
        data = request.get_json()
        try:
            if data["object"] == "page":
                if data["entry"][0]["messaging"]:
                    sender_id = data["entry"][0]["messaging"][0]["sender"]["id"]
                    # the facebook ID of the person sending you the message 

                    final_url = base_url+sender_id+"?"+"access_token="+access_token
                    print final_url

                    resp = requests.get(final_url)
                    user_data = resp.json()
                    sender_fname = user_data["first_name"]
                    sender_fname_stripped = sender_fname.split()[0]
                    sender_lname = user_data["last_name"]
                    sender_name = sender_fname+" "+sender_lname

                    # print sender_name
                    u_count = User_id.query.filter_by(name = sender_name).first()
                    log(u_count)
                    if u_count is None:
                        
                        new_time = int(time.time())
                        db_add = User_id(name=sender_name, comment_id="", message_id=sender_id, last_msg=new_time, auto_response=0)
                        db.session.add(db_add)
                        db.session.commit()

                        time.sleep(5)
                        send_state(sender_id)
                        time.sleep(15)

                        message_data = "Hi "+sender_fname_stripped+", just saw your comment.. Less than a year ago I was living in my car, but my life has changed since working with a millionaire mentor who shows me what to do to make money online, $2400 a week at the moment. I feel truly blessed since getting started at http://realendeavors.com/momsworkfromhome since I can now stay at home with my little ones"
                        send_message(sender_id, message_data)

                    else:
                        db.session.query(User_id).filter_by(name=sender_name).update({"message_id": sender_id})
                        db.session.commit()
                        bot_status = Bot_status.query.first()
                        if(bot_status.status =="on"):
                            old_time = int(u_count.last_msg)
                            new_time = int(time.time())
                            if((new_time - old_time)>25):
                                if int(u_count.auto_response)==0:
                                    db.session.query(User_id).update({"last_msg": new_time})
                                    db.session.commit()
                                    db.session.query(User_id).update({"auto_response": 1})
                                    db.session.commit()
                                    time.sleep(3)
                                    send_state(sender_id)
                                    time.sleep(8)
                                    message_data = "I was just about to walk out the door, but I'll be back a little later. Will you be on?"
                                    send_message(sender_id, message_data)
                        else:
                        	db.session.query(User_id).update({"auto_response": 1})
                        	db.session.commit()
                        #send_message(sender_id, "f yeah")
                        #recipient_id = data["entry"][0]["messaging"][0]["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        #message_text = data["entry"][0]["messaging"][0]["message"]["text"]  # the message's text
        except:
            try:   
                if data["entry"][0]["changes"][0]["value"]["item"]=="comment":
                    sender_id = data["entry"][0]["changes"][0]["value"]["sender_id"]
                    comment_id = data["entry"][0]["changes"][0]["value"]["comment_id"]
                    post_id = data["entry"][0]["changes"][0]["value"]["post_id"]
                    message_text = data["entry"][0]["changes"][0]["value"]["message"]
                    sender_name = data["entry"][0]["changes"][0]["value"]["sender_name"]
                    sender_fname = sender_name.split()[0]

                    post_check = Posts.query.filter_by(post_id=post_id).first()
                    time.sleep(15)
                    if post_check is not None: 
                        u_count = User_id.query.filter_by(name = sender_name).first()
                        #log(u_count)
                        if u_count is None:
                            new_time = int(time.time())
                            db_add = User_id(name=sender_name, comment_id=sender_id, message_id="", last_msg="0", auto_response=0)
                            db.session.add(db_add)
                            db.session.commit()
                            
                            #time.sleep(10)

                            message_data = "Hi "+sender_fname+", just saw your comment.. Less than a year ago I was living in my car, but my life has changed since working with a millionaire mentor who shows me what to do to make money online, $2400 a week at the moment. I feel truly blessed since getting started at http://realendeavors.com/momsworkfromhome since I can now stay at home with my little ones"
                            send_comment_message(comment_id, message_data)
            except:
                pass
    return "ok", 200, generate()

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

    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def send_comment_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {  
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "message": message_text
    })
    r = requests.post("https://graph.facebook.com/v2.8/"+recipient_id+"/private_replies", params=params, headers=headers, data=data)
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

def send_status(recipient_id):
    return "ok", 200


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)