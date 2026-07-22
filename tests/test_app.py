import os
import sys

import pytest
from werkzeug.security import check_password_hash

# Allow PyTest to import app.py from the src folder.
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")),
)

from app import Expense, User, app, db


@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        with app.test_client() as test_client:
            yield test_client

        db.session.remove()
        db.drop_all()


def register_user(
    client,
    name="Test User",
    email="test@example.com",
    password="password123",
):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )


def login_user(
    client,
    email="test@example.com",
    password="password123",
):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )


def test_user_registration_and_password_hashing(client):
    response = register_user(client)

    assert response.status_code == 200
    assert b"Login" in response.data

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        assert user is not None
        assert user.name == "Test User"
        assert user.password_hash != "password123"
        assert check_password_hash(user.password_hash, "password123")


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_valid_user_login(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    assert b"Personal Expense Dashboard" in response.data
    assert b"Welcome, Test User!" in response.data


def test_add_expense(client):
    register_user(client)
    login_user(client)

    response = client.post(
        "/add-expense",
        data={
            "amount": "45.50",
            "category": "Food",
            "description": "Family dinner",
            "expense_date": "2026-07-21",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Family dinner" in response.data
    assert b"$45.50" in response.data

    with app.app_context():
        expense = Expense.query.first()

        assert expense is not None
        assert expense.amount == 45.50
        assert expense.category == "Food"
        assert expense.description == "Family dinner"


def test_spending_analysis(client):
    register_user(client)
    login_user(client)

    expenses = [
        {
            "amount": "50.00",
            "category": "Food",
            "description": "Groceries",
            "expense_date": "2026-07-20",
        },
        {
            "amount": "25.00",
            "category": "Food",
            "description": "Lunch",
            "expense_date": "2026-07-21",
        },
        {
            "amount": "40.00",
            "category": "Transportation",
            "description": "Gas",
            "expense_date": "2026-07-21",
        },
    ]

    for expense in expenses:
        client.post(
            "/add-expense",
            data=expense,
            follow_redirects=True,
        )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Food" in response.data
    assert b"$75.00" in response.data
    assert b"Transportation" in response.data
    assert b"$40.00" in response.data
    assert b"Highest Spending Category:" in response.data
    assert b"Your highest spending category is Food" in response.data