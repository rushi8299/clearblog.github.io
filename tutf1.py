from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from datetime import datetime

from werkzeug.utils import redirect

with open("config.json", "r") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key='super-secret-key'


app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT= '465',
    MAIL_USE_SSL= True,
    MAIL_USERNAME= params['gmail-user'],
    MAIL_PASSWORD= params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']

db = SQLAlchemy(app)

class Contacts(db.Model):
    '''
    sno, name, phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline=db.Column(db.String(12),nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    num=int(params['no_of_posts'])
    posts = Posts.query.filter_by().all()[0:num]
    return render_template('index.html', params=params, post=posts)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

# @app.route('/post')
# def post():
#     return render_template('post.html', params=params)

# @app.route('/contact')
# def contact():
#     return render_template('contact.html')

@app.route("/contact", methods = ['GET', 'POST'])

def contact():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name = name, phone_num = phone, msg = message, date = datetime.now(), email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message From " + name,
                          sender = email,
                          recipients = params['gmail-user'],
                          body = "Message is " + message + "\n" + "Phone Number is " + phone
                          )
    return render_template('contact.html', params=params)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method=='POST':
        adminname=request.form.get('uname')
        adminpass=request.form.get('pass')
        if (adminname==params['admin_user'] and adminpass==params['admin_pass']):
            posts=Posts.query.all()
            session['user']=adminname
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            box_title=request.form.get('title')
            box_tagline=request.form.get('tagline')
            box_slug=request.form.get('slug')
            box_content=request.form.get('content')
            box_img=request.form.get('img_file')
            date=datetime.now()

            if sno=='0':
                post=Posts(title=box_title,tagline=box_tagline,slug=box_slug,content=box_content,img_file=box_img,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.tagline=box_tagline
                post.slug=box_slug
                post.content=box_content
                post.img_file=box_img
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, sno=sno,post=post)

@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')
    # return render_template('login.html',params=params)
app.run(debug=True)