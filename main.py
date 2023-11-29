import google.auth
from google.cloud import storage
import pathlib
import json
import requests
from flask import Flask, abort, render_template, request, redirect, url_for,make_response,session,render_template_string
from flask_socketio import send, SocketIO,emit
import secrets
import os
from flask_login import LoginManager, UserMixin, login_user, login_required
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "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"
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "1099125049356-31sea0ph813uah2s2nrdien89qu38pcl.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://hatched.tech/callback"
)
credentials,project =google.auth.default()
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.get_bucket("artifacts.hatched-ada56.appspot.com")
blob1 = bucket.get_blob("chat.doc")
blob2 = bucket.get_blob("insti.doc")
blob3 = bucket.get_blob("institute.doc")
blob4 = bucket.get_blob("user.doc")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Gmail SMTP port (SSL)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'hatchedme12@gmail.com'  # Your Gmail email address
app.config['MAIL_PASSWORD'] = 'mwhnokwbqpxjilyo'        # Your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'hatchedme12@gmail.com'
mail = Mail(app)
with blob3.open("r") as file:
    st=file.read()
    st = st.replace("\'", "\"")
    institutes={}
    if st:
        institutes=json.loads(st)
with blob2.open("r") as file:
    rt=file.read()
    rt = rt.replace("\'", "\"")
    on_insti=[]
    if rt:
        on_insti=json.loads(rt)
nt=[]
with blob4.open("r") as file:
    at=file.read()
    at = at.replace("\'", "\"")
    user_list=[]
    if at:
        user_list=json.loads(at)
with blob1.open("r") as file:
    qt=file.read()
    qt = qt.replace("\'", "\"")
    rooms={}
    if qt:
        rooms=json.loads(qt)
user_list2=user_list
class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    return User(username)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if not request.cookies.get('cookie_user_email'):
            return abort(401) 
        else:
            return function() 
    return wrapper

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    resp = make_response(redirect(authorization_url))
    resp.set_cookie("state", state, max_age=60*180)
    return resp


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    resp = make_response(redirect(url_for('index')))
    tok = id_info.get("sub")
    tok1= id_info.get("name")
    tok2=id_info.get("email")
    tok3=id_info.get("picture")
    user = User(id_info.get("name"))
    login_user(user)
    resp.set_cookie("cookie_user_photo", tok3, max_age=60*180)
    resp.set_cookie("cookie_user_email_add",tok2,max_age=60*180)
    resp.set_cookie("cookie_user_email", tok, max_age=60*180)
    resp.set_cookie("cookie_user",tok1,max_age=60*180)
    return resp

@app.route("/logout")
def logout():
    session.clear()
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie("cookie_user_photo", "tok", max_age=0)
    resp.set_cookie("cookie_user_email_add", "tok", max_age=0)
    resp.set_cookie("cookie_user_email", "tok", max_age=0)
    resp.set_cookie("cookie_user","tok1",max_age=0)
    return resp


@app.route('/')
def index():
    if not request.cookies.get('cookie_user'):
        return render_template('index.html',institutes=on_insti,current_user="Blorptangle")
    else:
        k=0
        content={
            "name":request.cookies.get('cookie_user'),
            "query_asked":k,
            "upvote_recieved":k,
            "email":request.cookies.get('cookie_user_email'),
            "upvote_anwser":k,
            "email_address":request.cookies.get('cookie_user_email_add'),
            "photo":request.cookies.get('cookie_user_photo')
        }
        prof = next((m for m in user_list if m['email'] == request.cookies.get('cookie_user_email')), None)
        prof2 = next((m for m in user_list2 if m['email'] == request.cookies.get('cookie_user_email')), None)
        if prof2:
            user_list2.remove(prof2)
            for i in range(len(user_list)):
                if user_list[i] == prof:
                    user_list[i] = prof2
            with blob4.open("w") as file4:
                file4.write(str(user_list))
        if not prof:
            user_list.append(content)
            with blob4.open("w") as file4:
                file4.write(str(user_list))
        return render_template("index.html",institutes=on_insti , current_user=request.cookies.get('cookie_user'),photo=request.cookies.get('cookie_user_photo'))

@app.route('/add_institute', methods=['POST'])
@login_required
def add_institute():
    institute_name = request.form['institute_name']
    on_insti.append(institute_name)
    with blob2.open("w") as file2:
                file2.write(str(on_insti))
    institutes[institute_name] = []
    with blob3.open("w") as file3:
                file3.write(str(institutes))
    return redirect(url_for('view_queries', institute_name=institute_name))

@app.route('/add_query/<institute_name>', methods=['POST'])
@login_required
def add_query(institute_name):
    query = request.form['query']
    prof2 = next((m for m in institutes[institute_name] if m == query), None)
    if prof2:
        return redirect(url_for('chat', institute_name=institute_name,query_index=institutes[institute_name].index(query)))
    institutes[str(institute_name)].append(query)
    with blob3.open("w") as file3:
                file3.write(str(institutes))
    rooms[query] = {"members": 0, "messages": [],"id":request.cookies.get('cookie_user_email_add')}
    with blob1.open("w") as file1:
                file1.write(str(rooms))
    with blob4.open("w") as file4:
                file4.write(str(user_list))
    prof = next((m for m in user_list if m['email'] == request.cookies.get('cookie_user_email')), None)
    if prof:
        prof['query_asked']+=1
    return redirect(url_for('chat', institute_name=institute_name,query_index=institutes[institute_name].index(query)))

@app.route('/queries/<institute_name>')
def view_queries(institute_name):
    qr=[]
    for m in institutes[institute_name]: 
        if not rooms[m]["messages"]: 
            qr.append(m)
    if not request.cookies.get('cookie_user'):
        return render_template('queries.html', unanswered_query=qr,institute_name=institute_name, queries=institutes[str(institute_name)],name="Blorptangle",st=user_list)
    else:
        return render_template('queries.html', unanswered_query=qr,institute_name=institute_name, queries=institutes[str(institute_name)],name=request.cookies.get('cookie_user'),st=user_list,photo=request.cookies.get('cookie_user_photo'))

@app.route('/chat/<institute_name>/<query_index>')
def chat(institute_name, query_index):
    query = institutes[institute_name][int(query_index)]
    room = str(query)
    rooms[room]["messages"]=sorted(rooms[room]["messages"], key=lambda x: x['upvote'], reverse = True)
    if not request.cookies.get('cookie_user'):
        resp=make_response(render_template('chat.html',code=room, institute_name=institute_name,ind=query_index, query=query, messages=rooms[room]["messages"],nt="Blorptangle",name="Blorptangle",ema="jfvngs"))
    else:
        resp=make_response(render_template('chat.html',code=room, institute_name=institute_name,ind=query_index, query=query, messages=rooms[room]["messages"],nt=request.cookies.get('cookie_user'),name=request.cookies.get('cookie_user'),ema=request.cookies.get('cookie_user_email'),photo=request.cookies.get('cookie_user_photo')))
    resp.set_cookie("room", query, max_age=60*180)
    return resp
    
@app.route("/<np>")
@login_required
def profile(np):
    prof = next((m for m in user_list if m['name'] == np), None)
    return render_template("profile.html",user=prof)

@socketio.on("message")
@login_required
def message(data):
    room = request.cookies.get('room')
    if room not in rooms:
        return 
    content = {
        "mss_id":str(secrets.token_urlsafe(4)),
        "name": request.cookies.get('cookie_user'),
        "email": request.cookies.get('cookie_user_email'),
        "message": data["data"],
        "time":data["time"],
        "upvote":data["upvote"],
        "upvoted_users":{}
    }
    if rooms[room].get("id"):
        subject="Hatched"
        recipient=rooms[room].get("id")
        body=render_template_string("""<!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Formal Q&A</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f2f2f2;
                            padding: 20px;
                        }

                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background-color: #ffffff;
                            padding: 20px;
                            border-radius: 5px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        }

                        h1 {
                            color: #333;
                            text-align: center;
                        }

                        .question {
                            font-weight: bold;
                        }

                        .answer {
                            margin-top: 10px;
                        }

                        p {
                            margin-bottom: 10px;
                        }

                        .footer {
                            text-align: center;
                            margin-top: 20px;
                            color: #777;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>You Have Been Answered</h1>
                        <p class="question">Question:   {{request.cookies.get('room')}}</p>
                        <p class="answer">Answer:</p>
                        <p>{{msg}}</p>
                    </div>
                    <div class="footer">
                        Sent via Hatched
                    </div>
                </body>
                </html>
                """,msg=data["data"])
        
        if rooms[room]["id"]!=request.cookies.get('cookie_user_email_add'):
            message = Message(subject=subject,
            recipients=[recipient],
            html=body)
            try:
                mail.send(message)
                print('Email sent successfully!', 'success')
            except Exception as e:
                print(f'An error occurred: {str(e)}', 'danger')
    send(content, to=room)
    rooms[room]["messages"].append(content)
    rooms[room]["messages"]=sorted(rooms[room]["messages"], key=lambda x: x['upvote'], reverse = True)
    with blob1.open("w") as file:
                file.write(str(rooms))
    print(f"{request.cookies.get('cookie_user')} said: {data['data']}")

@socketio.on('upvote')
@login_required
def handle_upvote(message_id):
    room = request.cookies.get('room')
    rooms[room]["messages"]=sorted(rooms[room]["messages"], key=lambda x: x['upvote'], reverse = True)
    if room not in rooms:
        return
    message = next((m for m in rooms[room]["messages"] if m['mss_id'] == message_id), None)
    if message:
        user_id = request.cookies.get('cookie_user_email')
        if user_id in message['upvoted_users']:
            message['upvote'] -= 1
            prof = next((m for m in user_list if m['email'] == request.cookies.get('cookie_user_email')), None)
            prof["upvote_anwser"]-=1
            prof = next((m for m in user_list if m['email'] == message['email']), None)
            prof["upvote_recieved"]-=1
            del message['upvoted_users'][user_id]
            print(user_id+ " has devoted "+message["message"])
        else:
            message['upvote'] += 1
            prof = next((m for m in user_list if m['email'] == request.cookies.get('cookie_user_email')), None)
            prof["upvote_anwser"]+=1
            prof = next((m for m in user_list if m['email'] == message['email']), None)
            prof["upvote_recieved"]+=1
            message['upvoted_users'][user_id] = 1
            print(user_id+ " has upvoted "+message["message"])

        emit('upvote', {'message_id': message['mss_id'], 'upvotes': message['upvote']}, broadcast=True)
        
@socketio.on("delete")
@login_required
def delete(data):
    room = request.cookies.get('room')
    if room not in rooms:
        return
    message3 = next((m for m in rooms[room]["messages"] if m['mss_id'] == data), None)
    rooms[room]["messages"].remove(message3)
    emit('delete', data, broadcast=True)

if __name__ == '__main__':
    os.chdir(os.getcwd())
    app.debug=True
    socketio.run(app)