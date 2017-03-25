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
@click.option('--debug',is_flag = True,
              help='runs server in debug mode')
def run(debug):
  """
  runs server
  """
  main.app.run(debug = debug)

@cli.command()
@click.option('--supersede',is_flag = True,
            help='drops database first, if it already exists')
def initdb(supersede):
  """
  creates database
  """
  msg=""
  db = sqlite3.connect('database/yafr.db')
  curs = db.cursor()
  if supersede: 
    curs.execute("DROP TABLE users")
    msg+="database dropped sucessfully\n"

  try:
    curs.execute('''CREATE TABLE users (uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        username TEXT NOT NULL,
                                        passh TEXT NOT NULL)''') #passh = password hash
    msg+="database initialized sucessfully"
  except:
    msg+="database already exists"

  db.commit()
  db.close()
  print(msg)
