                    import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
db_path = os.path.join(base_dir, 'mushroom_shop.db')

MY_UPI_ID, MY_SHOP_NAME, MY_WHATSAPP_NUMBER = "9057430791@ybl", "Fresh Mushroom Store", "9057430791"

def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS products')
        cursor.execute('CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT DEFAULT "Fresh", original_price INTEGER, discount_percent INTEGER, final_price INTEGER, image_url TEXT, description TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, address TEXT, phone TEXT, mushroom_name TEXT, quantity INTEGER, total_price INTEGER, payment_method TEXT, transaction_id TEXT, status TEXT DEFAULT "Pending")')
        cursor.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, rating INTEGER, comment TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS coupons (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, discount_flat INTEGER)')
        
        cursor.execute("SELECT COUNT(*) FROM coupons")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO coupons (code, discount_flat) VALUES ('FIRST10', 10)")

        sample_mushrooms = [
            ("Button Mushroom (200g)", "Fresh", 100, 20, 80, "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400", "Fresh white button mushrooms."),
            ("Oyster Mushroom (200g)", "Fresh", 120, 25, 90, "https://images.unsplash.com/photo-1611105943261-71e84dfa1835?w=400", "Healthy & rich in taste."),
            ("Shiitake Mushroom (100g)", "Fresh", 200, 15, 170, "https://images.unsplash.com/photo-1590779033100-9f60a05a013d?w=400", "Premium gourmet flavor.")
        ]
        cursor.executemany("INSERT INTO products (name, category, original_price, discount_percent, final_price, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_mushrooms)

init_db()

@app.route("/")
def home():
    s, c = request.args.get("search", ""), request.args.get("category", "")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        q, params = "SELECT * FROM products WHERE 1=1", []
        if s: q += " AND name LIKE ?"; params.append(f"%{s}%")
        if c: q += " AND category = ?"; params.append(c)
        cursor.execute(q, params)
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
        reviews = cursor.fetchall()
    return render_template("index.html", products=products, reviews=reviews, whatsapp_no=MY_WHATSAPP_NUMBER)

@app.route("/add-review", methods=["POST"])
def add_review():
    with sqlite3.connect(db_path) as conn:
        conn.cursor().execute("INSERT INTO reviews (customer_name, rating, comment) VALUES (?, ?, ?)", 
                             (request.form.get("name"), int(request.form.get("rating", 5)), request.form.get("comment")))
    return redirect(url_for("home"))

@app.route("/buy/<int:product_id>", methods=["GET", "POST"])
def buy(product_id):
    applied_coupon = request.args.get("coupon", "").strip().upper()
    flat_discount = 0
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        if applied_coupon:
            cursor.execute("SELECT discount_flat FROM coupons WHERE code = ?", (applied_coupon,))
            res = cursor.fetchone()
            if res: flat_discount = int(res[0])

        if request.method == "POST":
            coupon_used = request.form.get("coupon_used", "").strip().upper()
            cursor.execute("SELECT name, final_price FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            
            disc = 0
            if coupon_used:
                cursor.execute("SELECT discount_flat FROM coupons WHERE code = ?", (coupon_used,))
                c = cursor.fetchone()
                if c: disc = int(c[0])

            qty = int(request.form.get("quantity", 1))
            total = max(0, (int(product[1]) * qty) - disc)
            
            cursor.execute("INSERT INTO orders (customer_name, address, phone, mushroom_name, quantity, total_price, payment_method, transaction_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')",
                         (request.form.get("customer_name"), request.form.get("address"), request.form.get("phone"), product[0], qty, total, request.form.get("payment_method"), request.form.get("transaction_id", "N/A")))
            return redirect(url_for("orders"))

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
    return render_template("buy.html", product=product, upi_id=MY_UPI_ID, shop_name=MY_SHOP_NAME, applied_coupon=applied_coupon, flat_discount=flat_discount)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        if request.method == "POST":
            mrp, disc = int(request.form.get("original_price")), int(request.form.get("discount_percent", 0))
            final = int(mrp - (mrp * (disc / 100)))
            cursor.execute("INSERT INTO products (name, category, original_price, discount_percent, final_price, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (request.form.get("name"), request.form.get("category", "Fresh"), mrp, disc, final, request.form.get("image_url"), request.form.get("description")))
            return redirect(url_for("admin"))

        cursor.execute("SELECT * FROM products"); products = cursor.fetchall()
        cursor.execute("SELECT * FROM coupons"); coupons = cursor.fetchall()
    return render_template("admin.html", products=products, coupons=coupons)

@app.route("/update-price/<int:product_id>", methods=["POST"])
def update_price(product_id):
    mrp, disc = int(request.form.get("new_original_price")), int(request.form.get("new_discount_percent", 0))
    final = int(mrp - (mrp * (disc / 100)))
    with sqlite3.connect(db_path) as conn:
        conn.cursor().execute("UPDATE products SET original_price = ?, discount_percent = ?, final_price = ? WHERE id = ?", (mrp, disc, final, product_id))
    return redirect(url_for("admin"))

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    with sqlite3.connect(db_path) as conn:
        conn.cursor().execute("DELETE FROM products WHERE id = ?", (product_id,))
    return redirect(url_for("admin"))

@app.route("/update-order/<int:order_id>", methods=["POST"])
def update_order(order_id):
    with sqlite3.connect(db_path) as conn:
        conn.cursor().execute("UPDATE orders SET status = ? WHERE id = ?", (request.form.get("status"), order_id))
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        all_orders = cursor.fetchall()
    return render_template("orders.html", orders=all_orders)

if __name__ == "__main__":
    app.run(debug=True)
        
