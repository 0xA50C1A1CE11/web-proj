#imports
from flask import Flask,render_template,session,\
                  request,redirect,url_for,g,send_from_directory
from werkzeug.utils import secure_filename
import sqlite3,hashlib
import os

#setup
app = Flask(__name__)
app.config.from_envvar('YAFR_SETTINGS')
db = sqlite3.connect('/home/melancholiac/yafr/database/yafr.db',
                     check_same_thread=False)


#logic
@app.route('/')
def index():
  return render_template("homepage.html",user=session.get('username',False))

@app.route('/profile')  
def profile():
  if not 'username' in session:return redirect(url_for('index'))
  return render_template("profile.html",user=session.get('username',False))


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in \
         set(['txt', 'pdf', 'png', 'jpg', 'jpeg','zip','mp3','mp4','gif'])

@app.route('/upload',methods=['POST','GET'])
def upload():
  if not 'username' in session:return redirect(url_for('index'))
  if request.method == 'POST':
    if 'file' not in request.files:
      return "file missed"
    file = request.files['file']
    if file.filename == '':
      return "file not selected"
    if file and allowed_file(file.filename):
      cur = db.cursor()
      filename = secure_filename(file.filename)
      sdir = '/home/melancholiac/yafr/files/{}'.format(session['username'])
      if os.path.isfile(os.path.join(sdir,filename)):
        return "file already exists"
      cur.execute("INSERT INTO files (filename,owner) VALUES(?,?)",\
                                                (filename,session['username'],))
      db.commit()
      file.save(os.path.join(sdir, filename))
      print("user {} uploaded file {} to {}".format(session['username'],
                                                    filename,
                                                    sdir))
      return "file {} saved".format(filename)
    else:
      return "something went wrong"
  else:
    return render_template("upload.html")

@app.route('/listfiles')
def listfiles():
  if not 'username' in session:return redirect(url_for('index'))
  cur = db.cursor()
  cur.execute("SELECT filename FROM files WHERE owner=?",(session['username'],))
  return render_template("listfiles.html",
                          seq = cur.fetchall())

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
  if not 'username' in session:return redirect(url_for('index'))
  print("user {} uploaded file {}".format(session['username'],filename))
  return send_from_directory(directory='/home/melancholiac/yafr/files/{}'.format(session['username']),
                               filename=filename,
                               as_attachment=True)

@app.route('/delete/<path:filename>', methods=['GET', 'POST'])
def delete(filename):
  if not 'username' in session:return redirect(url_for('index'))
  filepath = os.path.join('/home/melancholiac/yafr/files/{}'.format(session['username']),
                          filename)
  if os.path.isfile(filepath):
    os.remove(filepath)
    cur = db.cursor()
    cur.execute('DELETE FROM files WHERE filename=?',(filename,))
    db.commit()
    print("user {} delted file {}".format(session['username'],filename))
    return redirect(url_for('listfiles'))
  else:
    return "file not exists"

@app.route('/sign_up',methods=['GET', 'POST'])
def sign_up():
  if request.method == 'POST':
    username,passw = request.form['username'],request.form['password']
    passwh = hashlib.sha224(passw.encode('utf-8')).hexdigest()
    cur = db.cursor()
    cur.execute("SELECT count(*) FROM users WHERE username = ?", (username,))
    exists=cur.fetchone()[0]
    if exists:
      return "user {} already exists".format(username)
    else:
      cur.execute("INSERT INTO users (username,passh) VALUES(?,?)",\
                                                  (username,passwh,))
      db.commit()
    session['username'] = username
    sdir = '/home/melancholiac/yafr/files/{}'.format(username)
    if not os.path.exists(sdir):
      os.makedirs(sdir)
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
      session['username'] = username
      return redirect(url_for('index'))
    else:
      return "wrong username/pass"
  else:
    return render_template("login.html")

@app.route('/log_out')
def log_out():
  if not 'username' in session:return redirect(url_for('index'))
  del session['username']
  return redirect(url_for('index'))
