from flask import Flask,render_template,request,g,redirect,url_for
import sqlite3
import os


tables = ["""CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          date DATE
          )
          """,
          """CREATE TABLE articles(id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          categorie TEXT,
          prix INTEGER,
          quantite_initiale INTEGER
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
def get_articles():
    bd, curs = get_db()
    curs.execute("SELECT * FROM articles")
    articles = curs.fetchall()
    return articles
def edit_article(article_id, new_name, new_categorie, new_prix, new_quantite_initiale):
    bd, curs = get_db()
    curs.execute("UPDATE articles SET name = ?, categorie = ?, prix = ?, quantite_initiale = ? WHERE id = ?", 
                 (new_name, new_categorie, new_prix, new_quantite_initiale, article_id))
    bd.commit()
@app.route('/')
def index():
    bd, curs = get_db()
    curs.execute("SELECT * FROM events")
    events = curs.fetchall()
    return render_template('index.html', events=events, articles=get_articles())

@app.route('/editarticle', methods=['GET', 'POST'])
def editarticle():
    article_id = request.form['id']
    new_name = request.form['name']
    new_categorie = request.form['categorie']
    new_prix = request.form['prix']
    new_quantite_initiale = request.form['quantite_initiale']
    edit_article(article_id, new_name, new_categorie, new_prix, new_quantite_initiale)
    return redirect(url_for('index'))

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
@app.route('/addarticle',methods=['GET','POST'])
def addarticle():
    bd, curs = get_db()
    name = request.form['name']
    categorie = request.form['categorie']
    prix = request.form['prix']
    quantite_initiale = request.form['quantite_initiale']
    curs.execute("INSERT INTO articles (name, categorie, prix, quantite_initiale) VALUES (?, ?, ?, ?)", (name, categorie, prix, quantite_initiale))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/deletearticle',methods=['GET','POST'])
def deletearticle():
    bd, curs = get_db()
    id = request.form['id']
    curs.execute("DELETE FROM articles WHERE id = ?", (id,))
    bd.commit()
    return redirect(url_for('index'))
app.run()
