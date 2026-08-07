import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)

# Session setup
app.secret_key = 'mushroom_secret_key_123'
ADMIN_PASSWORD = 'Ganesh1234me@711451'  # <--- अपना पासवर्ड यहाँ बदलें

def get_db_connection():
    conn = sqlite3.connect('mushroom_shop.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database tables अपने आप बनाने का फंक्शन (जो एरर दूर करेगा)
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mushrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            original_price REAL NOT NULL,
            discount REAL NOT NULL,
            selling_price REAL NOT NULL,
            image_url TEXT,
            description TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            customer_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

# App चालू होते ही DB setup चलेगा
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    mushrooms = conn.execute('SELECT * FROM mushrooms').fetchall()
    conn.close()
    return render_template('index.html', mushrooms=mushrooms)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        item_name = request.form.get('item_name', '')
        price = request.form.get('price', 0)
        customer_name = request.form.get('customer_name', '')
        address = request.form.get('address', '')
        phone = request.form.get('phone', '')

        conn = get_db_connection()
        conn.execute('INSERT INTO orders (item_name, price, customer_name, address, phone, status) VALUES (?, ?, ?, ?, ?, ?)',
                     (item_name, price, customer_name, address, phone, 'Pending'))
        conn.commit()
        conn.close()
        return redirect(url_for('orders'))

    item_name = request.args.get('item_name', '')
    price = request.args.get('price', '')
    return render_template('buy.html', item_name=item_name, price=price)

@app.route('/orders')
def orders():
    conn = get_db_connection()
    orders_list = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('orders.html', orders=orders_list)

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    status = request.form.get('status', 'Pending')
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('orders'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('is_admin'):
        conn = get_db_connection()
        mushrooms = conn.execute('SELECT * FROM mushrooms').fetchall()
        conn.close()
        return render_template('admin.html', mushrooms=mushrooms)

    if request.method == 'POST':
        entered_password = request.form.get('password')
        if entered_password == ADMIN_PASSWORD:
            session['is_admin'] = True
            conn = get_db_connection()
            mushrooms = conn.execute('SELECT * FROM mushrooms').fetchall()
            conn.close()
            return render_template('admin.html', mushrooms=mushrooms)
        else:
            return '''
                <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
                    <h3 style="color:red;">Wrong Password!</h3>
                    <a href="/admin">Try Again</a>
                </div>
            '''

    return '''
        <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
            <h2>Admin Login Required</h2>
            <form method="post">
                <input type="password" name="password" placeholder="Enter Password" style="padding:10px; width:200px;" required><br><br>
                <button type="submit" style="padding:10px 20px; background:#2e7d32; color:white; border:none; border-radius:5px; cursor:pointer;">Login</button>
            </form>
        </div>
    '''

@app.route('/add_mushroom', methods=['POST'])
def add_mushroom():
    if not session.get('is_admin'):
        return redirect(url_for('admin'))

    name = request.form.get('name', '')
    original_price = float(request.form.get('original_price', 0))
    discount = float(request.form.get('discount', 0))
    selling_price = original_price - (original_price * discount / 100)
    image_url = request.form.get('image_url', '')
    description = request.form.get('description', '')

    conn = get_db_connection()
    conn.execute('INSERT INTO mushrooms (name, original_price, discount, selling_price, image_url, description) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, original_price, discount, selling_price, image_url, description))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/update_discount/<int:item_id>', methods=['POST'])
def update_discount(item_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))

    new_price = float(request.form.get('original_price', 0))
    new_discount = float(request.form.get('discount', 0))
    new_selling_price = new_price - (new_price * new_discount / 100)

    conn = get_db_connection()
    conn.execute('UPDATE mushrooms SET original_price = ?, discount = ?, selling_price = ? WHERE id = ?',
                 (new_price, new_discount, new_selling_price, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_mushroom/<int:item_id>', methods=['POST'])
def delete_mushroom(item_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    conn.execute('DELETE FROM mushrooms WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
                                     
