# tests/test_ping.py
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, Base, User, get_db

# Create a test database (SQLite in-memory)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    """Clear database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_ping():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "server running"}


def test_ping1():
    response = client.get("/health1")
    assert response.status_code == 200
    assert response.json() == {"message": "server running nicely"}


# Tests for POST /users
def test_create_user_success():
    """Test successful user creation"""
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "password" not in data  # Password should not be in response


def test_create_user_duplicate_email():
    """Test creating user with duplicate email"""
    user_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "password123"
    }
    # Create first user
    response1 = client.post("/users", json=user_data)
    assert response1.status_code == 200
    
    # Try to create second user with same email
    response2 = client.post("/users", json=user_data)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]


def test_create_user_missing_field():
    """Test creating user with missing required field"""
    user_data = {
        "name": "Bob Smith",
        "email": "bob@example.com"
        # Missing password
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 422  # Validation error


# Tests for GET /users/{user_id}
def test_get_user_success():
    """Test getting user by ID"""
    # First create a user
    user_data = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "password": "password123"
    }
    create_response = client.post("/users", json=user_data)
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert "password" not in data  # Password should not be in response


def test_get_user_not_found():
    """Test getting non-existent user"""
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_user_invalid_id():
    """Test getting user with invalid ID format"""
    response = client.get("/users/invalid_id")
    assert response.status_code == 422  # Validation error