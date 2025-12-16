from flask import Flask,render_template,request,g,redirect,url_for
import sqlite3
import os


tables = ["""CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          date DATE
          )
          """
]
app = Flask("app.py")
if not os.path.exists('bd.db'):
    print("Creating database...")
    bd = sqlite3.connect('bd.db')
    curs = bd.cursor()
    for table in tables:
        curs.execute(table)
    bd.commit()
    bd.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("bd.db")
        g.cursor = g.db.cursor()
    return g.db, g.cursor

@app.route('/')
def index():
    bd, curs = get_db()
    curs.execute("SELECT * FROM events")
    events = curs.fetchall()
    events_str = ', '.join(f"{id} - {name} - {date}" for id, name, date in events)
    return render_template('index.html', events=events_str)

@app.route('/listevents',methods=['GET'])
def listevents():
    bd, curs = get_db()
    curs.execute("SELECT * FROM events")
    events = curs.fetchall()
    events_str = ', '.join(f"{id} - {name} - {date}" for id, name, date in events)
    return render_template('index.html', events=events_str)
@app.route('/addevent',methods=['GET','POST'])
def addevent():
    bd, curs = get_db()
    name = request.form['name']
    date = request.form['date']
    curs.execute("INSERT INTO events (name, date) VALUES (?, ?)", (name, date))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/deleteevent',methods=['GET','POST'])
def deleteevent():
    bd, curs = get_db()
    id = request.form['id']
    curs.execute("DELETE FROM events WHERE id = ?", (id,))
    bd.commit()
    return redirect(url_for('index'))
app.run()
