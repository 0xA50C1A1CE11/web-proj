#imports
from flask import Flask,render_template,session,\
                  request,redirect,url_for,send_from_directory,\
                  send_file,make_response,flash
import flask_login
from werkzeug.utils import secure_filename
import sqlite3,hashlib
import os

#setup
app = Flask(__name__)
app.config.from_envvar('YAFR_SETTINGS')
db = sqlite3.connect(os.path.join(app.config['ROOTDIR'],'database/yafr.db'),
                     check_same_thread=False)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
class User(flask_login.UserMixin):pass

#logic
def getusername():
  if hasattr(flask_login.current_user,'id'):
    return flask_login.current_user.id
  return False

@app.route('/')
def index():
  return render_template("homepage.html",user = getusername())

@app.route('/profile')
@flask_login.login_required
def profile():
  return render_template("profile.html",user = flask_login.current_user.id)

def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in \
         set(['txt', 'pdf', 'png', 'jpg', 'jpeg','zip','mp3','mp4','gif'])

@app.route('/upload',methods=['POST','GET'])
@flask_login.login_required
def upload():
  if request.method == 'POST':
    if 'file' not in request.files:
      return "file missed"
    file = request.files['file']
    if file.filename == '':
      return "file not selected"
    if file and allowed_file(file.filename):
      cur = db.cursor()
      privacy = request.form.get('privacy',1)=='on' and 1 or 0
      description = request.form.get('description','')
      filename = secure_filename(file.filename)
      sdir = cur.execute("SELECT homedir FROM users WHERE username=?",(getusername(),))
      sdir = sdir.fetchone()[0]
      formatt = filename.rsplit('.', 1)[1]
      if os.path.isfile(os.path.join(sdir,filename)):
        return "file already exists"
      cur.execute("INSERT INTO files (filename,\
                                      owner,\
                                      type,\
                                      privacy,\
                                      description) \
                   VALUES(?,?,?,?,?)",(filename,
                                       getusername(),
                                       formatt, #actually format
                                       privacy,
                                       description,))
      db.commit()
      file.save(os.path.join(sdir, filename))
      return redirect(url_for('listfiles'))
    else:
      return "something went wrong"
  else:
    return render_template("upload.html")

@app.route('/listfiles')
@flask_login.login_required
def listfiles():
  cur = db.cursor()
  cur.execute("SELECT filename FROM files WHERE owner=?",(getusername(),))
  return render_template("listfiles.html",
                          seq = cur.fetchall())

@app.route('/download/<path:filename>', methods=['GET'])
@flask_login.login_required
def download(filename):
  cur = db.cursor()
  userdir = cur.execute("SELECT homedir FROM USERS WHERE username=?",(getusername(),))
  userdir = userdir.fetchone()[0]
  redirect_path = os.path.join(getusername(),filename)
  redirect_path = "/download_api/" + redirect_path
  response = make_response("")
  response.headers["X-Accel-Redirect"] = redirect_path
  return response

@app.route('/download_from', methods=['GET'])
@flask_login.login_required
def download_from():
  filename = request.args.get("filename")
  username = request.args.get("username")
  cur = db.cursor()
  userdir = cur.execute("SELECT homedir FROM USERS WHERE username=?",(username,))
  userdir = userdir.fetchone()[0]
  return send_from_directory(userdir,
                             filename=filename,
                             as_attachment=True)

@app.route('/delete/<path:filename>', methods=['GET', 'POST'])
@flask_login.login_required
def delete(filename):
  cur = db.cursor()
  userdir = cur.execute("SELECT homedir FROM USERS WHERE username=?",(getusername(),))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  if os.path.isfile(filepath):
    os.remove(filepath)
    cur = db.cursor()
    cur.execute('DELETE FROM files WHERE filename=?',(filename,))
    db.commit()
    return redirect(url_for('listfiles'))
  else:
    return "file not exists"

@app.route('/browse',methods=['GET','POST'])
@flask_login.login_required
def browse():
  if request.method == 'POST':
    filename = request.form['filename']
    owner = request.form['owner']
    type = request.form['type']
    file_descr = request.form['file_descr']
    if filename=='': filename='%'
    if owner=='': owner='%'
    if type=='': type='%'
    if file_descr=='': file_descr='%'
    cur = db.cursor()
    query = cur.execute("SELECT filename,description,owner FROM files WHERE\
                         filename LIKE ? AND \
                         owner LIKE ? AND \
                         type LIKE ? AND \
                         privacy=0 AND \
                         description LIKE ?",(filename,owner,type,file_descr,))
    query = query.fetchall()
    query =[(i[0],i[2]) for i in query ]
    return render_template('showfiles.html',seq = query)
  else:
    return render_template('searchfiles.html')

@app.route('/preview/<string:filename>')
@flask_login.login_required
def preview(filename):
  cur = db.cursor()
  user = getusername()
  userdir = cur.execute("SELECT homedir FROM users WHERE username=?",(user,))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  extension = filename.rsplit('.',1)[1]
  print(filepath)
  return render_template('preview.html',extension=extension,filepath=filepath)

@app.route('/preview_from',methods=['GET'])
@flask_login.login_required
def preview_from():
  cur = db.cursor()
  user = request.args.get('username')
  filename = request.args.get('filename')
  userdir = cur.execute("SELECT homedir FROM users WHERE username=?",(user,))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  extension = filename.rsplit('.',1)[1]
  return render_template('preview.html',
                          extension=extension,
                          filepath=filepath)

@app.route('/sign_up',methods=['GET', 'POST'])
@flask_login.login_required
def sign_up():
  if request.method == 'POST':
    username,passw = request.form['username'],request.form['password']
    passwh = hashlib.sha224(passw.encode('utf-8')).hexdigest()
    homedir = os.path.join(app.config['FILEDIR'],username)
    cur = db.cursor()
    cur.execute("SELECT count(*) FROM users WHERE username = ?", (username,))
    exists=cur.fetchone()[0]
    if exists:
      return "user {} already exists".format(username)
    else:
      cur.execute("INSERT INTO users (username,passh,homedir) VALUES(?,?,?)",\
                                                  (username,passwh,homedir,))
      db.commit()
    if not os.path.exists(homedir):
      os.makedirs(homedir)
    return redirect(url_for('index'))
  else:
    return render_template("sign_up.html")

@app.route('/login',methods=['GET','POST'])
def login():
  if request.method == 'POST':
    username,passw = request.form['username'],request.form['password']
    passwh = hashlib.sha224(passw.encode('utf-8')).hexdigest()
    cur = db.cursor()
    cur.execute("SELECT count(*) FROM users WHERE username = ? AND passh=?",
                (username,passwh))
    exists=cur.fetchone()[0]
    if exists:
      cur.execute("SELECT uid,username,passh FROM users WHERE username = ? AND passh=?",
                (username,passwh))
      uid,uname,passwhn = cur.fetchone()
      if passwh == passwhn:
        user = User()
        user.id = username
        flask_login.login_user(user)
        return redirect(url_for('index'))
      else:
        return "wrong pass"
    else:
      return "user not exists"
  else:
    return render_template("login.html")

@app.route('/log_out')
@flask_login.login_required
def log_out():
  flask_login.logout_user()
  return redirect(url_for('index'))

@login_manager.user_loader
def user_loader(username):
  cur = db.cursor()
  cur.execute("SELECT count(*) FROM users WHERE username = ?", (username,))
  exists=cur.fetchone()[0]
  if not exists:
    return
  user = User()
  user.id = username
  return user

@login_manager.request_loader
def request_loader(request):
  username = request.form.get('username')
  cur = db.cursor()
  cur.execute("SELECT count(*) FROM users WHERE username = ?", (username,))
  exists=cur.fetchone()[0]
  if not exists:
    return
  cur.execute("SELECT username,passh FROM users WHERE username = ?", (username,))
  uid,passwh1 = cur.fetchone()[0]
  user = User()
  user.id = username
  passwh2 =  hashlib.sha224(request.form['password'].encode('utf-8')).hexdigest()
  user.is_authenticated = passwh1 == passwh2
  return user

@login_manager.unauthorized_handler
def unauthorized_handler():
  return 'Unauthorized'
