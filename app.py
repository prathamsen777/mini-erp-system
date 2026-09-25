from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_to_anything"

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="877011",
        database="mini_erp"
    )

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/inventory")
def inventory():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("inventory.html", products=products)

@app.route("/inventory/add", methods=["POST"])
def add_product():
    name = request.form["name"]
    quantity = request.form["quantity"]
    unit_price = request.form["unit_price"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO products (name, quantity, unit_price) VALUES (%s, %s, %s)",
        (name, quantity, unit_price)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("inventory"))

@app.route("/inventory/delete/<int:product_id>")
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("inventory"))

@app.route("/sales")
def sales():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("""
        SELECT sales.id, products.name AS product_name, sales.customer_name,
               sales.quantity, sales.total_price, sales.sale_date
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.id DESC
    """)
    sales_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("sales.html", products=products, sales=sales_list, error=None)

@app.route("/sales/add", methods=["POST"])
def add_sale():
    product_id = request.form["product_id"]
    customer_name = request.form["customer_name"]
    quantity = int(request.form["quantity"])

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product or product["quantity"] < quantity:
        cursor.close()
        db.close()
        return "Not enough stock available. Go back and try again."

    total_price = float(product["unit_price"]) * quantity

    cursor.execute(
        "INSERT INTO sales (product_id, customer_name, quantity, total_price) VALUES (%s, %s, %s, %s)",
        (product_id, customer_name, quantity, total_price)
    )
    cursor.execute(
        "UPDATE products SET quantity = quantity - %s WHERE id = %s",
        (quantity, product_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("sales"))

@app.route("/purchase")
def purchase():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("""
        SELECT purchases.id, products.name AS product_name, purchases.supplier_name,
               purchases.quantity, purchases.total_cost, purchases.purchase_date
        FROM purchases
        JOIN products ON purchases.product_id = products.id
        ORDER BY purchases.id DESC
    """)
    purchases_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("purchase.html", products=products, purchases=purchases_list)

@app.route("/purchase/add", methods=["POST"])
def add_purchase():
    product_id = request.form["product_id"]
    supplier_name = request.form["supplier_name"]
    quantity = int(request.form["quantity"])
    cost_per_unit = float(request.form["cost_per_unit"])
    total_cost = quantity * cost_per_unit

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO purchases (product_id, supplier_name, quantity, total_cost) VALUES (%s, %s, %s, %s)",
        (product_id, supplier_name, quantity, total_cost)
    )
    cursor.execute(
        "UPDATE products SET quantity = quantity + %s WHERE id = %s",
        (quantity, product_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("purchase"))

from datetime import date

@app.route("/hr")
def hr():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    cursor.execute("""
        SELECT attendance.`date`, attendance.status, employees.name AS emp_name
        FROM attendance
        JOIN employees ON attendance.employee_id = employees.id
        ORDER BY attendance.`date` DESC
    """)
    attendance = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("hr.html", employees=employees, attendance=attendance)

@app.route("/hr/add", methods=["POST"])
def add_employee():
    name = request.form["name"]
    role = request.form["role"]
    contact = request.form["contact"]
    joining_date = request.form["joining_date"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO employees (name, role, contact, joining_date) VALUES (%s, %s, %s, %s)",
        (name, role, contact, joining_date)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("hr"))

@app.route("/hr/attendance", methods=["POST"])
def mark_attendance():
    employee_id = request.form["employee_id"]
    status = request.form["status"]
    today = date.today()

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO attendance (employee_id, `date`, status) VALUES (%s, %s, %s)",
        (employee_id, today, status)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("hr"))

if __name__ == "__main__":
    app.run(debug=True)
