import pytest
import requests
from faker import Faker
from src.config import BASE_URL

@pytest.fixture(scope="session")
def faker():
    return Faker()

@pytest.fixture
def api_client():
    """Returns base URL for API requests."""
    return BASE_URL

@pytest.fixture
def registered_user(faker):
    """Fixture that registers a new random user and returns user info including token."""
    password = faker.password(length=10)
    username = f"user{faker.random_int(100000, 999999)}"
    email = f"{username}@example.com"
    
    payload = {
        "user": {
            "username": username,
            "email": email,
            "password": password
        }
    }
    
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code in [200, 201], f"Failed to register user in fixture: {response.text}"
    
    data = response.json()
    user_data = data["user"]
    user_data["password"] = password
    return user_data

@pytest.fixture
def auth_headers(registered_user):
    """Fixture that provides Authorization header with Token <jwt>."""
    return {
        "Authorization": f"Token {registered_user['token']}"
    }

@pytest.fixture
def target_user(faker):
    """Fixture that registers a second unique user (target user) for follow/unfollow tests."""
    password = faker.password(length=10)
    username = f"target{faker.random_int(100000, 999999)}"
    email = f"{username}@example.com"
    
    payload = {
        "user": {
            "username": username,
            "email": email,
            "password": password
        }
    }
    
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code in [200, 201], f"Failed to register target user in fixture: {response.text}"
    
    data = response.json()
    user_data = data["user"]
    user_data["password"] = password
    return user_data

@pytest.fixture
def other_user(faker):
    """Fixture that registers another independent user for 403 forbidden security tests."""
    password = faker.password(length=10)
    username = f"other{faker.random_int(100000, 999999)}"
    email = f"{username}@example.com"
    
    payload = {
        "user": {
            "username": username,
            "email": email,
            "password": password
        }
    }
    
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code in [200, 201], f"Failed to register other user in fixture: {response.text}"
    
    data = response.json()
    user_data = data["user"]
    user_data["password"] = password
    return user_data

@pytest.fixture
def other_auth_headers(other_user):
    """Fixture that provides Authorization header for other_user."""
    return {
        "Authorization": f"Token {other_user['token']}"
    }

@pytest.fixture
def created_article(auth_headers, faker):
    """Fixture that creates an article for testing and yields article data."""
    title = f"Article {faker.word().capitalize()} {faker.random_int(1000, 9999)}"
    payload = {
        "article": {
            "title": title,
            "description": faker.sentence(),
            "body": faker.text(),
            "tagList": ["reactjs", "pytest"]
        }
    }
    response = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
    assert response.status_code in [200, 201], f"Failed to create article in fixture: {response.text}"
    data = response.json()
    article = data["article"]
    yield article
    try:
        requests.delete(f"{BASE_URL}/articles/{article['slug']}", headers=auth_headers)
    except Exception:
        pass
