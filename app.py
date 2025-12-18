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
        event_id INTEGER,
        date DATE,
        FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE todos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        event_id INTEGER,
        FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
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
    if "db" not in g:
        g.db = sqlite3.connect("bd.db")
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def get_articles():
    bd = get_db()
    curs = bd.cursor()
    curs.execute("SELECT * FROM articles")
    articles = curs.fetchall()
    return articles
#ryan
def get_articles_with_stock():
    bd = get_db()
    cur = bd.cursor()
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
    bd = get_db()
    curs = bd.cursor()
    curs.execute("UPDATE articles SET name = ?, categorie = ?, prix = ?, quantite_initiale = ? WHERE id = ?", 
                 (new_name, new_categorie, new_prix, new_quantite_initiale, article_id))
    bd.commit()
@app.route('/')
def index():
    bd = get_db()
    curs = bd.cursor()
    curs.execute("SELECT * FROM events")
    events = curs.fetchall()
    return render_template(
        'index.html',
        events=events,
        articles=get_articles_with_stock(),
        todos=bd.cursor().execute("SELECT * FROM todos").fetchall()
    )

@app.route('/addtask', methods=['GET', 'POST'])
def addtask():
    bd = get_db()
    curs = bd.cursor()
    description = request.form['description']
    event_id = request.form['event_id']
    curs.execute("INSERT INTO todos (description, event_id) VALUES (?, ?)", (description, event_id))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/done_task', methods=['GET', 'POST'])
def done_task():
    bd = get_db()
    curs = bd.cursor()
    task_id = request.form['id']
    curs.execute("DELETE FROM todos WHERE id = ?", (task_id,))
    bd.commit()
    return redirect(url_for('index'))
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
    bd = get_db()
    curs = bd.cursor()
    name = request.form['name']
    date = request.form['date']
    curs.execute("INSERT INTO events (name, date) VALUES (?, ?)", (name, date))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/deleteevent',methods=['GET','POST'])
def deleteevent():
    bd = get_db()
    curs = bd.cursor()
    id = request.form['id']
    curs.execute("DELETE FROM events WHERE id = ?", (id,))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/addarticle',methods=['GET','POST'])
def addarticle():
    bd = get_db()
    curs = bd.cursor()
    name = request.form['name']
    categorie = request.form['categorie']
    prix = request.form['prix']
    quantite_initiale = request.form['quantite_initiale']
    curs.execute("INSERT INTO articles (name, categorie, prix, quantite_initiale) VALUES (?, ?, ?, ?)", (name, categorie, prix, quantite_initiale))
    bd.commit()
    return redirect(url_for('index'))
@app.route('/deletearticle',methods=['GET','POST'])
def deletearticle():
    bd = get_db()
    curs = bd.cursor()
    id = request.form['id']
    curs.execute("DELETE FROM articles WHERE id = ?", (id,))
    bd.commit()
    return redirect(url_for('index'))

@app.route("/addtransaction", methods=["POST"])
def addtransaction():
    db = get_db()
    cur = db.cursor()

    article_id = request.form.get("article_id")
    type_ = request.form.get("type")
    quantity = request.form.get("quantity")
    event_id = request.form.get("event_id")

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
        INSERT INTO transactions (article_id, type, quantity, event_id, date)
        VALUES (?, ?, ?, ?, DATE('now'))
    """, (article_id, type_, quantity, event_id))

    db.commit()
    return redirect(url_for("index"))
@app.route('/getstatsforevent', methods=['POST'])
def getstatsforevent():
    event_id = request.form['event_id']
    db = get_db()
    cur = db.cursor()

    # Event info
    cur.execute("SELECT name, date FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()

    # Total sales & purchases
    cur.execute("""
        SELECT
            SUM(CASE WHEN type='sell' THEN quantity ELSE 0 END),
            SUM(CASE WHEN type='buy' THEN quantity ELSE 0 END)
        FROM transactions
        WHERE event_id = ?
    """, (event_id,))
    total_sold, total_bought = cur.fetchone()

    # Profit
    cur.execute("""
        SELECT
            SUM(CASE WHEN t.type='sell' THEN t.quantity * a.prix ELSE 0 END) -
            SUM(CASE WHEN t.type='buy' THEN t.quantity * a.prix ELSE 0 END)
        FROM transactions t
        JOIN articles a ON a.id = t.article_id
        WHERE t.event_id = ?
    """, (event_id,))
    profit = cur.fetchone()[0] or 0

    # Best products
    cur.execute("""
        SELECT
            a.id,
            a.name,
            SUM(t.quantity) AS quantity_sold
        FROM transactions t
        JOIN articles a ON a.id = t.article_id
        WHERE t.event_id = ? AND t.type = 'sell'
        GROUP BY a.id
        ORDER BY quantity_sold DESC
    """, (event_id,))
    bestproducts = cur.fetchall()

    return render_template(
        "index.html",
        events=db.cursor().execute("SELECT * FROM events").fetchall(),
        articles=get_articles_with_stock(),
        stats={
            "event_name": event[0],
            "event_date": event[1],
            "total_sold": total_sold or 0,
            "total_bought": total_bought or 0
        },
        profit=profit,
        bestproducts=[
            {"id": r[0], "name": r[1], "quantity_sold": r[2]}
            for r in bestproducts
        ]
    )

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

app.run()
