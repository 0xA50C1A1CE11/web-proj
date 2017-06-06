#imports
from flask import Flask,render_template,session,\
                  request,redirect,url_for,send_from_directory,\
                  send_file,make_response
from werkzeug.utils import secure_filename
import sqlite3,hashlib
import os

#setup
app = Flask(__name__)
app.config.from_envvar('YAFR_SETTINGS')
db = sqlite3.connect(os.path.join(app.config['ROOTDIR'],'database/yafr.db'),
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
      privacy = request.form.get('privacy',1)=='on' and 1 or 0
      description = request.form.get('description','')
      filename = secure_filename(file.filename)
      sdir = cur.execute("SELECT homedir FROM users WHERE username=?",(session['username'],))
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
                                       session['username'],
                                       formatt, #actually format
                                       privacy,
                                       description,))
      db.commit()
      file.save(os.path.join(sdir, filename))
      print("user {} uploaded file {}\n\
             to: {} \n\
             type: {}\n\
             privacy: {} \n\
             description: {}".format(session['username'],
                                    filename,
                                    sdir,
                                    formatt,
                                    privacy,
                                    description))
      return redirect(url_for('listfiles'))
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

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
  if not 'username' in session:return redirect(url_for('index'))
  cur = db.cursor()
  userdir = cur.execute("SELECT homedir FROM USERS WHERE username=?",(session['username'],))
  userdir = userdir.fetchone()[0]
  print("user {} downloaded file {}".format(session['username'],filename))
  redirect_path = os.path.join(session['username'],filename)
  redirect_path = "/download_api/" + redirect_path
  print(redirect_path)
  response = make_response("")
  response.headers["X-Accel-Redirect"] = redirect_path
  return response

@app.route('/download_from', methods=['GET'])
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
def delete(filename):
  if not 'username' in session:return redirect(url_for('index'))
  cur = db.cursor()
  userdir = cur.execute("SELECT homedir FROM USERS WHERE username=?",(session['username'],))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  if os.path.isfile(filepath):
    os.remove(filepath)
    cur = db.cursor()
    cur.execute('DELETE FROM files WHERE filename=?',(filename,))
    db.commit()
    print("user {} delted file {}".format(session['username'],filename))
    return redirect(url_for('listfiles'))
  else:
    return "file not exists"

@app.route('/browse',methods=['GET','POST'])
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
    print('filename ',filename,
          '\nowner ',owner,
          '\ntype ',type,
          '\ndescr',file_descr)
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
def preview(filename):
  cur = db.cursor()
  user = session['username']
  userdir = cur.execute("SELECT homedir FROM users WHERE username=?",(user,))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  extension = filename.rsplit('.',1)[1]
  return render_template('preview.html',extension=extension,filepath=filepath)

@app.route('/preview_from',methods=['GET'])
def preview_from():
  cur = db.cursor()
  user = request.args.get('username')
  filename = request.args.get('filename')
  userdir = cur.execute("SELECT homedir FROM users WHERE username=?",(user,))
  userdir = userdir.fetchone()[0]
  filepath = os.path.join(userdir,filename)
  print(filename)
  extension = filename.rsplit('.',1)[1]
  return render_template('preview.html',
                          extension=extension,
                          filepath=filepath)

@app.route('/sign_up',methods=['GET', 'POST'])
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
    session['username'] = username
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
