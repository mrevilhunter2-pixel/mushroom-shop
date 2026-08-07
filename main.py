import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)

# Secret key session ke liye zaroori hai
app.secret_key = 'mushroom_secret_key_123'

# Admin Panel ka Password Yahan Set Karein
ADMIN_PASSWORD = 'Ganesh1234me@711451'

def get_db_connection():
    conn = sqlite3.connect('mushroom_shop.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    mushrooms = conn.execute('SELECT * FROM mushrooms').fetchall()
    conn.close()
    return render_template('index.html', mushrooms=mushrooms)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        item_name = request.form['item_name']
        price = request.form['price']
        customer_name = request.form['customer_name']
        address = request.form['address']
        phone = request.form['phone']

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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Agar pehle se logged in hai
    if session.get('is_admin'):
        conn = get_db_connection()
        mushrooms = conn.execute('SELECT * FROM mushrooms').fetchall()
        conn.close()
        return render_template('admin.html', mushrooms=mushrooms)

    # Jab user password submit kare
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
                <div style="text-align:center; margin-top:50px;">
                    <h3 style="color:red;">Wrong Password!</h3>
                    <a href="/admin">Try Again</a>
                </div>
            '''

    # Direct access karne par password mangna
    return '''
        <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
            <h2>Admin Login Required</h2>
            <form method="post">
                <input type="password" name="password" placeholder="Enter Password" style="padding:10px; width:200px;" required><br><br>
                <button type="submit" style="padding:10px 20px; background:#2e7d32; color:white; border:none; border-radius:5px; cursor:pointer;">Login</button>
            </form>
        </div>
    '''

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
        
