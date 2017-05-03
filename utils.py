import click,sqlite3,os


@click.group()
def cli():
  """
  top level script for server running,configuring,db managment,
  and quick reference
  """
  pass

@cli.command('db-ref')
def dbref():
  """
  shows database reference
  """
  print("""current db scheme:
  users -> uid int primary
           username text not null
           passh text not null
           homedir text not null
           
  files -> fid int primary
           filename text not null
           owner ref to username not null
           type text not null
           privacy integer not null
           description text
           """)
@cli.command('logo')
def logo():
  """
  displays fancy logo
  """
  print('\n__   __ _    _____ ____\n\
\ \ / // \  |  ___|  _ \ \n\
 \ V // _ \ | |_  | |_) |\n\
  | |/ ___ \|  _| |  _ < \n\
  |_/_/   \_\_|   |_| \_\\\n\
Yet Another File Repository\n')
@cli.command('db-seek')
@click.option('--n',default=-1,help='number of matches')
@click.option('--db',type=click.Choice(['users', 'files']),
               default='users',help='choose db to seek in, users is deault')
@click.option('--username',default='%')
@click.option('--filename',default='%')
@click.option('--owner',default='%')
@click.option('--type',default='%')
@click.option('--desc',default='%')
def dbbrowse(n,db,username,filename,owner,type,desc):
  """
  allow u to browse database and search records
  """
  dbase = sqlite3.connect('database/yafr.db')
  curs = dbase.cursor()
  if db=='users':
    curs.execute("SELECT * FROM users WHERE username LIKE ?",(username,))
    result = curs.fetchall()
    for userinfo in [{'uid':user[0],\
                      'username':user[1],\
                      'homedir':user[3]} for user in result]:
      print(userinfo)
      
  else:
    curs.execute("SELECT * FROM files WHERE filename LIKE ? AND \
                                            owner LIKE ?  AND \
                                            type LIKE ? AND \
                                            description LIKE ?",(filename,\
                                                                   owner,\
                                                                   type,\
                                                                   desc,))
    result = curs.fetchall()
    for fileinfo in [{'fid':fil3[0],
                      'filename':fil3[1],
                      'owner':fil3[2],
                      'type':fil3[3],
                      'privacy':fil3[4],
                      'desc':fil3[5]}
                      for fil3 in result]:
      print(fileinfo)
  dbase.close()
@cli.command('cfg-ref')
def cfgref():
  """
  show configuration reference
  """
  print("""configuration done through editing yafr.cfg file
environmental variable YAFR_SETTINGS used to pass path to yafr.cfg to app
for *nix: export YAFR_SETTINGS=/path/to/yafr.cfg
for windows: set YAFR_SETTINGS=\path\\to\yafr.cfg""")

@cli.command()
@click.option('--debug',
              is_flag = True,
              help='runs server in debug mode')
@click.option('--vis',
              is_flag = True,
              help='runs server on machine\'s ip')
@click.option('--port',
              default=5000,
              help='runs server on certaion port')
def run(debug,vis,port):
  """
  runs server
  """
  '''from yafr import main
  main.app.run(debug = debug,
               host = vis and "0.0.0.0" or "127.0.0.1",
               port = port)'''
  os.system('uwsgi --socket 127.0.0.1:3031 --wsgi-file wsgi.py --callable app --processes 4 --threads 2')

@cli.command()
def initdb():
  """
  creates database
  """
  db = sqlite3.connect('database/yafr.db')
  curs = db.cursor()
  try:
    curs.execute('''CREATE TABLE users (uid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        username TEXT NOT NULL,
                                        passh TEXT NOT NULL,
                                        homedir TEXT NOT NULL)''')
    curs.execute('''CREATE TABLE files (fid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        filename TEXT NOT NULL,
                                        owner TEXT NOT NULL,
                                        type TEXT NOT NULL,
                                        privacy INT NOT NULL,
                                        description text,
                                        FOREIGN KEY(owner) REFERENCES users(username))''')
    print("database initialized sucessfully")
  except:
    print("database already exists")
  db.commit()
  db.close()

def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

@cli.command()
@click.option('--yes', 
              is_flag=True,
              callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to drop the db?')
def dropdb():
  """drops databse"""
  db = sqlite3.connect('database/yafr.db')
  curs = db.cursor()
  curs.execute("DROP TABLE IF EXISTS files")
  curs.execute("DROP TABLE IF EXISTS users")
  db.commit()
  db.close()
  import os,glob,shutil
  dirs = glob.glob('yafr/files/*')
  for d in dirs: shutil.rmtree(d)
  print("database drop sucessfully")
