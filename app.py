import os, sqlite3
from contextlib import contextmanager
from flask import Flask, jsonify, request, render_template
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=32768

# Optional local API token; production mode rejects unauthenticated API requests.
import hmac

@app.before_request
def require_api_auth():
    if not request.path.startswith('/api/') or request.path == '/api/health':
        return None
    token = os.getenv('API_TOKEN')
    if os.getenv('APP_ENV') != 'production' and not token:
        return None
    if not token:
        return jsonify(error='API authentication must be configured in production'), 503
    if not hmac.compare_digest(request.headers.get('X-API-Token', ''), token):
        return jsonify(error='Unauthorized'), 401
    return None


@contextmanager
def dbconn():
    db=sqlite3.connect(os.getenv('DATABASE_PATH','app.db'));db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
    try:yield db;db.commit()
    finally:db.close()
with dbconn() as db:db.executescript("""CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,email TEXT);CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,sku TEXT NOT NULL UNIQUE,name TEXT NOT NULL,stock INTEGER NOT NULL DEFAULT 0,unit_cost_cents INTEGER NOT NULL DEFAULT 0);CREATE TABLE IF NOT EXISTS purchase_orders(id INTEGER PRIMARY KEY,supplier_id INTEGER NOT NULL REFERENCES suppliers(id),status TEXT NOT NULL DEFAULT 'ordered',created_at TEXT DEFAULT CURRENT_TIMESTAMP);CREATE TABLE IF NOT EXISTS purchase_lines(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES purchase_orders(id),product_id INTEGER NOT NULL REFERENCES products(id),quantity INTEGER NOT NULL,unit_cost_cents INTEGER NOT NULL);""")
def rows(sql,args=()):
    with dbconn() as db:return [dict(r) for r in db.execute(sql,args).fetchall()]
@app.errorhandler(ValueError)
def bad_request(e):return jsonify(error=str(e)),400
@app.errorhandler(sqlite3.IntegrityError)
def conflict(e):return jsonify(error=str(e)),409
@app.get('/')
def home():return render_template('index.html')
@app.get('/api/suppliers')
def suppliers():return jsonify(rows('SELECT * FROM suppliers ORDER BY id DESC'))
@app.post('/api/suppliers')
def create_supplier():
    d=request.get_json(force=True);name=str(d.get('name','')).strip()
    if not name:raise ValueError('Supplier name required')
    with dbconn() as db:c=db.execute('INSERT INTO suppliers(name,email) VALUES(?,?)',(name,d.get('email')));return jsonify(id=c.lastrowid),201
@app.get('/api/products')
def products():return jsonify(rows('SELECT * FROM products ORDER BY id DESC'))
@app.post('/api/products')
def create_product():
    d=request.get_json(force=True)
    if not d.get('sku') or not d.get('name'):raise ValueError('SKU and name required')
    cost=int(d.get('unit_cost_cents',0))
    if cost<0:raise ValueError('Cost cannot be negative')
    with dbconn() as db:c=db.execute('INSERT INTO products(sku,name,unit_cost_cents) VALUES(?,?,?)',(d['sku'],d['name'],cost));return jsonify(id=c.lastrowid),201
@app.get('/api/purchase-orders')
def orders():return jsonify(rows('SELECT po.*,s.name supplier FROM purchase_orders po JOIN suppliers s ON s.id=po.supplier_id ORDER BY po.id DESC'))
@app.post('/api/purchase-orders')
def create_order():
    d=request.get_json(force=True);lines=d.get('lines',[])
    if not lines:raise ValueError('At least one line required')
    parsed=[]
    for line in lines:
        pid,qty,cost=int(line['product_id']),int(line['quantity']),int(line['unit_cost_cents'])
        if qty<=0 or cost<0:raise ValueError('Invalid quantity or cost')
        parsed.append((pid,qty,cost))
    with dbconn() as db:
        c=db.execute('INSERT INTO purchase_orders(supplier_id) VALUES(?)',(int(d['supplier_id']),))
        db.executemany('INSERT INTO purchase_lines(order_id,product_id,quantity,unit_cost_cents) VALUES(?,?,?,?)',[(c.lastrowid,*x) for x in parsed])
        return jsonify(id=c.lastrowid),201
@app.post('/api/purchase-orders/<int:order_id>/receive')
def receive(order_id):
    with dbconn() as db:
        r=db.execute('SELECT status FROM purchase_orders WHERE id=?',(order_id,)).fetchone()
        if not r:return jsonify(error='Order not found'),404
        if r['status']=='received':return jsonify(error='Already received'),409
        lines=db.execute('SELECT product_id,quantity FROM purchase_lines WHERE order_id=?',(order_id,)).fetchall()
        for line in lines:db.execute('UPDATE products SET stock=stock+? WHERE id=?',(line['quantity'],line['product_id']))
        db.execute("UPDATE purchase_orders SET status='received' WHERE id=?",(order_id,))
        return jsonify(received=True)

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    return response
@app.get('/api/health')
def health():
    return jsonify(status='ok')
@app.get('/api/insights')
def insights():
    with dbconn() as db:
        return jsonify(suppliers=db.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0],products=db.execute('SELECT COUNT(*) FROM products').fetchone()[0],open_orders=db.execute("SELECT COUNT(*) FROM purchase_orders WHERE status != 'received'").fetchone()[0],inventory_value_cents=db.execute('SELECT COALESCE(SUM(stock*unit_cost_cents),0) FROM products').fetchone()[0])

if __name__=='__main__':app.run(debug=os.getenv('FLASK_DEBUG') == '1')


@app.get('/api/export/products.csv')
def export_products_csv():
    """Download a read-only snapshot of the local demo dataset."""
    from flask import Response
    from data_export import serialize_csv
    with dbconn() as connection:
        cursor = connection.execute("SELECT id,sku,name,stock,unit_cost_cents FROM products ORDER BY id")
        columns = [column[0] for column in cursor.description]
        content = serialize_csv(cursor.fetchall(), columns)
    response = Response(content, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="products.csv"'
    response.headers['Cache-Control'] = 'no-store'
    return response
