import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"  # needed for login sessions

DB_PATH = os.path.join(os.path.dirname(__file__), "foodies.db")


# ---------- DATABASE HELPERS ----------

def get_db():
    """Opens a new database connection if there isn't one for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["name"]
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Run once to create all tables from schema.sql."""
    db = sqlite3.connect(DB_PATH)
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        db.executescript(f.read())
    db.commit()
    db.close()
    print("Database initialized.")


# ---------- PLATFORM STATS (Python + SQL, used across the app) ----------

def get_total_owners():
    """How many restaurants have registered on Foodies."""
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS total FROM owners").fetchone()
    return row["total"]


def get_total_customers():
    """How many customer visits have happened across every restaurant.
    COUNT(*) on an indexed table stays fast even at large scale."""
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS total FROM visits").fetchone()
    return row["total"]


# ---------- HOME PAGE ----------

@app.route("/")
def home():
    stats = {
        "total_owners": get_total_owners(),
        "total_customers": get_total_customers(),
    }
    return render_template("index.html", stats=stats)


# ---------- OWNER: REGISTER ----------

@app.route("/owner/register", methods=["GET", "POST"])
def owner_register():
    if request.method == "POST":
        restaurant_name = request.form["restaurant_name"]
        owner_name = request.form["owner_name"]
        email = request.form["email"]
        password = request.form["password"]
        location = request.form["location"]
        phone = request.form["phone"]

        password_hash = generate_password_hash(password)

        db = get_db()
        try:
            db.execute(
                """INSERT INTO owners (restaurant_name, owner_name, email, password_hash, location, phone)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (restaurant_name, owner_name, email, password_hash, location, phone),
            )
            db.commit()
            return redirect(url_for("owner_login"))
        except sqlite3.IntegrityError:
            return render_template("owner_register.html", error="Email already registered.")

    return render_template("owner_register.html")


# ---------- OWNER: LOGIN ----------

@app.route("/owner/login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        owner = db.execute("SELECT * FROM owners WHERE email = ?", (email,)).fetchone()

        if owner and check_password_hash(owner["password_hash"], password):
            session["owner_id"] = owner["id"]
            session["restaurant_name"] = owner["restaurant_name"]
            return redirect(url_for("owner_dashboard"))
        else:
            return render_template("owner_login.html", error="Invalid email or password.")

    return render_template("owner_login.html")


@app.route("/owner/logout")
def owner_logout():
    session.clear()
    return redirect(url_for("home"))


# ---------- OWNER: DASHBOARD (protected) ----------

@app.route("/owner/dashboard")
def owner_dashboard():
    if "owner_id" not in session:
        return redirect(url_for("owner_login"))

    db = get_db()
    items = db.execute(
        "SELECT * FROM menu_items WHERE restaurant_id = ? ORDER BY category, name",
        (session["owner_id"],),
    ).fetchall()

    return render_template(
        "owner_dashboard.html",
        restaurant_name=session["restaurant_name"],
        items=items,
    )


# ---------- OWNER: ADD A MENU ITEM ----------

@app.route("/owner/menu/add", methods=["POST"])
def owner_menu_add():
    if "owner_id" not in session:
        return redirect(url_for("owner_login"))

    db = get_db()
    db.execute(
        """INSERT INTO menu_items
           (restaurant_id, name, description, price, category, food_type,
            prep_time_minutes, available)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            session["owner_id"],
            request.form["name"],
            request.form.get("description", ""),
            float(request.form["price"]),
            request.form["category"],
            request.form["food_type"],
            int(request.form.get("prep_time_minutes", 10)),
        ),
    )
    db.commit()
    return redirect(url_for("owner_dashboard"))


# ---------- OWNER: DELETE A MENU ITEM ----------

@app.route("/owner/menu/delete/<int:item_id>", methods=["POST"])
def owner_menu_delete(item_id):
    if "owner_id" not in session:
        return redirect(url_for("owner_login"))

    db = get_db()
    # Only delete if it belongs to the logged-in owner's restaurant
    db.execute(
        "DELETE FROM menu_items WHERE id = ? AND restaurant_id = ?",
        (item_id, session["owner_id"]),
    )
    db.commit()
    return redirect(url_for("owner_dashboard"))


# ---------- CUSTOMER: MENU (no login needed) ----------

@app.route("/menu")
def customer_menu():
    restaurant_id = request.args.get("restaurant_id")
    table_number = request.args.get("table", "")

    # Log this as a visit for analytics, only if we know which restaurant it's for
    if restaurant_id:
        db = get_db()
        db.execute(
            "INSERT INTO visits (restaurant_id, table_number) VALUES (?, ?)",
            (restaurant_id, table_number),
        )
        db.commit()

    return render_template("menu.html", restaurant_id=restaurant_id, table_number=table_number)


# ---------- API: MENU DATA (this is the "API link" the frontend JS calls) ----------

@app.route("/api/menu")
def api_menu():
    """
    Returns menu items as JSON for a given restaurant.
    Query params:
      restaurant_id (required)
      food_type = veg | non-veg | both (optional, defaults to both)
    Example: /api/menu?restaurant_id=1&food_type=veg
    """
    restaurant_id = request.args.get("restaurant_id")
    food_type = request.args.get("food_type", "both")

    if not restaurant_id:
        return jsonify({"error": "restaurant_id is required"}), 400

    db = get_db()
    if food_type in ("veg", "non-veg"):
        rows = db.execute(
            """SELECT * FROM menu_items
               WHERE restaurant_id = ? AND food_type = ? AND available = 1
               ORDER BY category, name""",
            (restaurant_id, food_type),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT * FROM menu_items
               WHERE restaurant_id = ? AND available = 1
               ORDER BY category, name""",
            (restaurant_id,),
        ).fetchall()

    items = [dict(row) for row in rows]
    return jsonify({"count": len(items), "items": items})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
