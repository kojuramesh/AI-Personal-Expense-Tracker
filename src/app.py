from datetime import date

from flask import Flask, redirect, render_template_string, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret-key-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expense_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    expenses = db.relationship(
        "Expense",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    expense_date = db.Column(db.Date, nullable=False, default=date.today)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI-Powered Personal Expense Tracker</title>

            <link
                rel="stylesheet"
                href="{{ url_for('static', filename='style.css') }}"
            >
        </head>

        <body>
            <div class="container">

                <h1>AI-Powered Personal Expense Tracker</h1>

                <p>
                    Track your daily expenses, monitor spending,
                    and improve your personal financial management.
                </p>

                <div class="summary-card">
                    <h2>Initial Prototype</h2>
                    <p>
                        This version includes secure user authentication,
                        expense management, and an SQLite database.
                    </p>
                </div>

                <a class="button" href="/register">
                    Create Account
                </a>

                <br><br>

                <a href="/login">
                    Already have an account? Login
                </a>

            </div>
        </body>
        </html>
        """
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            message = "An account with this email already exists."
        else:
            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
            )

            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for("login"))

    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Register - AI Expense Tracker</title>

            <link
                rel="stylesheet"
                href="{{ url_for('static', filename='style.css') }}"
            >
        </head>

        <body>
            <div class="container">

                <h1>Create Account</h1>
                <p>Create an account to begin tracking your expenses.</p>

                {% if message %}
                    <p style="color:red;">
                        {{ message }}
                    </p>
                {% endif %}

                <form method="POST">
                    <label>Name:</label><br>
                    <input
                        type="text"
                        name="name"
                        placeholder="Enter your full name"
                        required
                    >
                    <br><br>

                    <label>Email:</label><br>
                    <input
                        type="email"
                        name="email"
                        placeholder="Enter your email"
                        required
                    >
                    <br><br>

                    <label>Password:</label><br>
                    <input
                        type="password"
                        name="password"
                        placeholder="Create a password"
                        required
                    >
                    <br><br>

                    <button class="button" type="submit">
                        Register
                    </button>
                </form>

                <br>

                <p>
                    Already have an account?
                    <a href="/login">Login here</a>
                </p>

                <p>
                    <a href="/">
                        ← Back to Home
                    </a>
                </p>

            </div>
        </body>
        </html>
        """,
        message=message,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        message = "Invalid email or password."

    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - AI Expense Tracker</title>

            <link
                rel="stylesheet"
                href="{{ url_for('static', filename='style.css') }}"
            >
        </head>

        <body>
            <div class="container">

                <h1>Login</h1>
                <p>Sign in to access your personal expense dashboard.</p>

                {% if message %}
                    <p style="color:red;">
                        {{ message }}
                    </p>
                {% endif %}

                <form method="POST">
                    <label>Email:</label><br>
                    <input
                        type="email"
                        name="email"
                        placeholder="Enter your email"
                        required
                    >
                    <br><br>

                    <label>Password:</label><br>
                    <input
                        type="password"
                        name="password"
                        placeholder="Enter your password"
                        required
                    >
                    <br><br>

                    <button class="button" type="submit">
                        Login
                    </button>
                </form>

                <br>

                <p>
                    Need an account?
                    <a href="/register">Register here</a>
                </p>

                <p>
                    <a href="/">
                        ← Back to Home
                    </a>
                </p>

            </div>
        </body>
        </html>
        """,
        message=message,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    expenses = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(Expense.expense_date.desc())
        .all()
    )

    total_expenses = sum(expense.amount for expense in expenses)

    return render_template_string(
    """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Expense Tracker</title>

        <link
            rel="stylesheet"
            href="{{ url_for('static', filename='style.css') }}"
        >
    </head>

    <body>
        <div class="container">

            <h1>Personal Expense Dashboard</h1>

            <p>Welcome, {{ current_user.name }}!</p>
            <p>You are securely logged in.</p>

            <div class="summary-card">
                <h2>Expense Summary</h2>
                <p>
                    <strong>Total Expenses:</strong>
                    ${{ "%.2f"|format(total_expenses) }}
                </p>
            </div>

            <a class="button" href="/add-expense">
                Add New Expense
            </a>

            <h2>Your Expenses</h2>

            {% if expenses %}
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Action</th>
                    </tr>

                    {% for expense in expenses %}
                    <tr>
                        <td>{{ expense.expense_date }}</td>
                        <td>{{ expense.category }}</td>
                        <td>{{ expense.description }}</td>
                        <td>${{ "%.2f"|format(expense.amount) }}</td>
                        <td>
                            <form
                                method="POST"
                                action="{{ url_for('delete_expense', expense_id=expense.id) }}"
                            >
                                <button
                                    class="delete-button"
                                    type="submit"
                                >
                                    Delete
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No expenses have been added yet.</p>
            {% endif %}

            <br><br>

            <a href="/logout">Logout</a>

        </div>
    </body>
    </html>
    """,
    expenses=expenses,
    total_expenses=total_expenses,
)
    return render_template_string(
        """
        <h1>Dashboard</h1>

        <p>Welcome, {{ current_user.name }}!</p>
        <p>You are securely logged in.</p>

        <h2>Initial Prototype Status</h2>
        <ul>
            <li>User registration: Working</li>
            <li>Secure password hashing: Working</li>
            <li>User login: Working</li>
            <li>Protected dashboard: Working</li>
        </ul>

        <p><a href="/logout">Logout</a></p>
        """
    )

@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        description = request.form["description"].strip()
        expense_date = date.fromisoformat(request.form["expense_date"])

        new_expense = Expense(
            amount=amount,
            category=category,
            description=description,
            expense_date=expense_date,
            user_id=current_user.id,
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Add Expense - AI Expense Tracker</title>

            <link
                rel="stylesheet"
                href="{{ url_for('static', filename='style.css') }}"
            >
        </head>

        <body>
            <div class="container">

                <h1>Add New Expense</h1>
                <p>Enter the details of your expense below.</p>

                <form method="POST">
                    <label>Amount:</label><br>
                    <input
                        type="number"
                        name="amount"
                        step="0.01"
                        min="0.01"
                        placeholder="Example: 50.00"
                        required
                    >
                    <br><br>

                    <label>Category:</label><br>
                    <select name="category" required>
                        <option value="">Select a category</option>
                        <option value="Food">Food</option>
                        <option value="Housing">Housing</option>
                        <option value="Transportation">
                            Transportation
                        </option>
                        <option value="Utilities">Utilities</option>
                        <option value="Entertainment">
                            Entertainment
                        </option>
                        <option value="Healthcare">Healthcare</option>
                        <option value="Shopping">Shopping</option>
                        <option value="Other">Other</option>
                    </select>
                    <br><br>

                    <label>Description:</label><br>
                    <input
                        type="text"
                        name="description"
                        placeholder="Example: Grocery shopping"
                    >
                    <br><br>

                    <label>Date:</label><br>
                    <input
                        type="date"
                        name="expense_date"
                        required
                    >
                    <br><br>

                    <button class="button" type="submit">
                        Save Expense
                    </button>
                </form>

                <br>

                <a href="/dashboard">
                    ← Back to Dashboard
                </a>

            </div>
        </body>
        </html>
        """
    )
@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user.id,
    ).first_or_404()

    db.session.delete(expense)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)