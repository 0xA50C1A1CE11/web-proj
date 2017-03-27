import click,sqlite3,os
from yafr import main

@click.group()
def cli():
  """
  this script is top level script capable of configurating,
  preforming installations
  and running application.
  """
  pass

@cli.command()
@click.option('--db',is_flag = True,
              help='db reference')
def ref(db):
  """project reference documentation"""
  if db:
    print("""at first edit your yafr.cfg, then
for *nix: export YAFR_SETTINGS=/path/to/yafr.cfg
for windows: set YAFR_SETTINGS=\path\\to\yafr.cfg
current db scheme:
  users -> uid int, username text, passh text
  files -> fid int, filename text, owner ref to username""")

@cli.command()
@click.option('--debug',
              is_flag = True,
              help='runs server in debug mode')
@click.option('--vis',
              is_flag = True,
              help='runs server on machine\'s ip')
def run(debug,vis):
  """
  runs server
  """
  main.app.run(debug = debug,
               host = vis and "0.0.0.0" or "127.0.0.1",
               port = 5000)

@cli.command()
def initdb():
  """
  creates database
  """
  db = sqlite3.connect('/home/melancholiac/yafr/database/yafr.db')
  curs = db.cursor()
  try:
    curs.execute('''CREATE TABLE users (uid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        username TEXT NOT NULL,
                                        passh TEXT NOT NULL)''') #passh = password hash
    curs.execute('''CREATE TABLE files (fid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        filename TEXT NOT NULL,
                                        owner TEXT NOT NULL,
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
  db = sqlite3.connect('/home/melancholiac/yafr/database/yafr.db')
  curs = db.cursor()
  curs.execute("DROP TABLE IF EXISTS files")
  curs.execute("DROP TABLE IF EXISTS users")
  db.commit()
  db.close()
  print("database drop sucessfully")
