from flask import Flask,render_template,request,g,redirect,url_for
import sqlite3
import os


tables = [
    """CREATE TABLE events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date DATE
    )""",
    """CREATE TABLE articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        categorie TEXT,
        prix INTEGER,
        quantite_initiale INTEGER
    )""",
    """CREATE TABLE transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        type TEXT,
        quantity INTEGER,
        date DATE,
        FOREIGN KEY(article_id) REFERENCES articles(id)
    )"""
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
#ryan
def get_articles_with_stock():
    db, cur = get_db()
    cur.execute("""
        SELECT
            a.id,
            a.name,
            a.categorie,
            a.prix,
            (
                a.quantite_initiale
                + IFNULL((
                    SELECT SUM(
                        CASE
                            WHEN type='buy' THEN quantity
                            WHEN type='sell' THEN -quantity
                        END
                    )
                    FROM transactions
                    WHERE article_id = a.id
                ), 0)
            ) AS stock
        FROM articles a
        ORDER BY a.id
    """)
    return cur.fetchall()

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
    return render_template(
        'index.html',
        events=events,
        articles=get_articles_with_stock()
    )

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

@app.route("/addtransaction", methods=["POST"])
def addtransaction():
    db, cur = get_db()

    article_id = request.form.get("article_id")
    type_ = request.form.get("type")
    quantity = request.form.get("quantity")

    if not article_id or not type_ or not quantity:
        return redirect(url_for("index"))

    quantity = int(quantity)
    if type_ == "sell":
        cur.execute("""
            SELECT a.quantite_initiale +
            IFNULL(SUM(
                CASE
                    WHEN t.type='buy' THEN t.quantity
                    WHEN t.type='sell' THEN -t.quantity
                END
            ),0)
            FROM articles a
            LEFT JOIN transactions t ON a.id=t.article_id
            WHERE a.id=?
        """, (article_id,))
        stock = cur.fetchone()[0]

        if quantity > stock:
            return redirect(url_for("index"))

    cur.execute("""
        INSERT INTO transactions (article_id, type, quantity, date)
        VALUES (?, ?, ?, DATE('now'))
    """, (article_id, type_, quantity))

    db.commit()
    return redirect(url_for("index"))

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.commit()
        db.close()

app.run()
