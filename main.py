from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

from werkzeug.utils import secure_filename

# Static Uploads Folder Setup
UPLOAD_FOLDER = os.path.join(base_dir, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "mushroom_super_secret_key"
ADMIN_PASSWORD = "Ganesh1234me@711451"  # <--- यहाँ अपना मनपसंद पासवर्ड लिखें
db_path = os.path.join(base_dir, 'mushroom_shop.db')

MY_UPI_ID = "9057430791@ybl"
MY_SHOP_NAME = "Fresh Mushroom Store"
MY_WHATSAPP_NUMBER = "9057430791"

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS products')
    
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'Fresh',
            original_price INTEGER NOT NULL,
            discount_percent INTEGER NOT NULL,
            final_price INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            mushroom_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_flat INTEGER NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM coupons")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO coupons (code, discount_flat) VALUES ('FIRST10', 10)")

    # Sample Mushrooms
    sample_mushrooms = [
        ("Button Mushroom (200g)", "Fresh", 100, 20, 80, "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400", "Fresh white button mushrooms."),
        ("Oyster Mushroom (200g)", "Fresh", 120, 25, 90, "https://images.unsplash.com/photo-1611105943261-71e84dfa1835?w=400", "Healthy & rich in taste."),
        ("Shiitake Mushroom (100g)", "Fresh", 200, 15, 170, "https://images.unsplash.com/photo-1590779033100-9f60a05a013d?w=400", "Premium gourmet flavor.")
    ]
    cursor.executemany("INSERT INTO products (name, category, original_price, discount_percent, final_price, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_mushrooms)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    search_query = request.args.get("search", "")
    category_filter = request.args.get("category", "")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search_query:
        query += " AND name LIKE ?"
        params.append(f"%{search_query}%")
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
    reviews = cursor.fetchall()

    conn.close()
    return render_template("index.html", products=products, reviews=reviews, whatsapp_no=MY_WHATSAPP_NUMBER)

@app.route("/add-review", methods=["POST"])
def add_review():
    name = request.form.get("name")
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reviews (customer_name, rating, comment) VALUES (?, ?, ?)", (name, rating, comment))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/buy/<int:product_id>", methods=["GET", "POST"])
def buy(product_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    applied_coupon = request.args.get("coupon", "").strip().upper()
    flat_discount = 0

    if applied_coupon:
        cursor.execute("SELECT discount_flat FROM coupons WHERE code = ?", (applied_coupon,))
        c = cursor.fetchone()
        if c:
            flat_discount = int(c[0])

    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        quantity = int(request.form.get("quantity", 1))
        payment_method = request.form.get("payment_method")
        transaction_id = request.form.get("transaction_id", "N/A")
        coupon_used = request.form.get("coupon_used", "").strip().upper()

        cursor.execute("SELECT name, final_price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        discount_amount = 0
        if coupon_used:
            cursor.execute("SELECT discount_flat FROM coupons WHERE code = ?", (coupon_used,))
            c = cursor.fetchone()
            if c:
                discount_amount = int(c[0])

        unit_price = int(product[1])
        total = (unit_price * quantity) - discount_amount
        if total < 0:
            total = 0

        cursor.execute("""
            INSERT INTO orders 
            (customer_name, address, phone, mushroom_name, quantity, total_price, payment_method, transaction_id, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, address, phone, product[0], quantity, total, payment_method, transaction_id, 'Pending'))
        
        conn.commit()
        conn.close()

        return redirect(url_for("orders", phone=phone))

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    # product tuple format: (id, name, category, original_price, discount_percent, final_price, image_url, description)
    return render_template("buy.html", product=product, upi_id=MY_UPI_ID, shop_name=MY_SHOP_NAME, applied_coupon=applied_coupon, flat_discount=flat_discount)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # 1. अगर पहले से लॉग-इन है
    if session.get("is_admin"):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

                if request.method == "POST" and "name" in request.form:
            name = request.form.get("name")
            category = request.form.get("category", "Fresh")
            mrp = int(request.form.get("original_price"))
            discount = int(request.form.get("discount_percent", 0))
            desc = request.form.get("description")
            final_price = int(mrp - (mrp * (discount / 100)))

            # इमेज फाइल को सेव करने का कोड
            image_file = request.files.get("product_image")
            image_url = ""
            if image_file and image_file.filename != "":
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f"/static/uploads/{filename}"

            cursor.execute("INSERT INTO products (name, category, original_price, discount_percent, final_price, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (name, category, mrp, discount, final_price, image_url, desc))
            conn.commit()
            return redirect(url_for("admin"))

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM coupons")
        coupons = cursor.fetchall()
        conn.close()
        return render_template("admin.html", products=products, coupons=coupons)

    # 2. अगर पासवर्ड सबमिट किया गया है
    if request.method == "POST" and "admin_password" in request.form:
        if request.form.get("admin_password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        else:
            return '''
                <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
                    <h3 style="color:red;">गलत पासवर्ड!</h3>
                    <a href="/admin">फिर से कोशिश करें</a>
                </div>
            '''

    # 3. पासवर्ड इनपुट फॉर्म (जब लॉग-इन न हो)
    return '''
        <div style="text-align:center; margin-top:80px; font-family:sans-serif;">
            <h2>Admin Panel Login</h2>
            <form method="post" style="margin-top:20px;">
                <input type="password" name="admin_password" placeholder="Admin Password दर्ज करें" style="padding:10px; width:220px; font-size:16px;" required><br><br>
                <button type="submit" style="padding:10px 20px; background:#2e7d32; color:white; border:none; border-radius:5px; font-size:16px; cursor:pointer;">Login</button>
            </form>
        </div>
    '''


@app.route("/update-price/<int:product_id>", methods=["POST"])
def update_price(product_id):
    mrp = int(request.form.get("new_original_price"))
    discount = int(request.form.get("new_discount_percent", 0))
    final_price = int(mrp - (mrp * (discount / 100)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET original_price = ?, discount_percent = ?, final_price = ? WHERE id = ?", 
                   (mrp, discount, final_price, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/update-order/<int:order_id>", methods=["POST"])
def update_order(order_id):
    admin_pin = request.form.get("admin_pin")
    
    if session.get("is_admin") or admin_pin == ADMIN_PASSWORD:
        new_status = request.form.get("status")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        conn.close()
        
    return redirect(url_for("orders"))
    
@app.route("/cancel-order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'Cancelled ❌' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("orders"))

@app.route("/delete-order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    admin_pin = request.form.get("admin_pin")
    
    # Session लॉग-इन हो या Admin PIN सही हो, दोनों स्थिति में डिलीट होगा
    if session.get("is_admin") or admin_pin == ADMIN_PASSWORD:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        
    return redirect(url_for("orders"))
    
@app.route("/orders", methods=["GET", "POST"])
def orders():
    phone_query = request.args.get("phone", "").strip()
    
    if request.method == "POST":
        phone_query = request.form.get("phone", "").strip()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. अगर Admin लॉगिन है, तो उसको सारे ऑर्डर्स दिखेंगे
    if session.get("is_admin"):
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        all_orders = cursor.fetchall()
        conn.close()
        return render_template("orders.html", orders=all_orders, is_admin=True)

    # 2. अगर कस्टमर ने फ़ोन नंबर दिया है, तो सिर्फ उसके ऑर्डर्स दिखेंगे
    user_orders = []
    if phone_query:
        cursor.execute("SELECT * FROM orders WHERE phone = ? ORDER BY id DESC", (phone_query,))
        user_orders = cursor.fetchall()

    conn.close()
    return render_template("orders.html", orders=user_orders, phone_searched=phone_query, is_admin=False)
    

if __name__ == "__main__":
    app.run(debug=True)
    
