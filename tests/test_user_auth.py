import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.user import UserResponse, GenericErrorModel

@pytest.mark.smoke
class TestUserAuthSmoke:
    
    @qase.id(23)
    def test_user_registration(self, faker):
        """Test successful user registration (POST /users)."""
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
        assert response.status_code in [200, 201], f"Expected 200/201 Created, got {response.status_code}: {response.text}"
        
        # Contract validation
        user_response = UserResponse.model_validate(response.json())
        assert user_response.user.username == username
        assert user_response.user.email == email
        assert user_response.user.token is not None

    @qase.id(24)
    def test_user_login(self, registered_user):
        """Test existing user login (POST /users/login)."""
        payload = {
            "user": {
                "email": registered_user["email"],
                "password": registered_user["password"]
            }
        }
        
        response = requests.post(f"{BASE_URL}/users/login", json=payload)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        user_response = UserResponse.model_validate(response.json())
        assert user_response.user.email == registered_user["email"]
        assert user_response.user.token is not None

    @qase.id(25)
    def test_get_current_user(self, registered_user, auth_headers):
        """Test getting current authenticated user (GET /user)."""
        response = requests.get(f"{BASE_URL}/user", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        user_response = UserResponse.model_validate(response.json())
        assert user_response.user.email == registered_user["email"]
        assert user_response.user.username == registered_user["username"]

    @qase.id(26)
    def test_update_current_user(self, registered_user, auth_headers, faker):
        """Test updating current user information (PUT /user)."""
        new_bio = faker.sentence()
        payload = {
            "user": {
                "bio": new_bio
            }
        }
        
        response = requests.put(f"{BASE_URL}/user", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        user_response = UserResponse.model_validate(response.json())
        assert user_response.user.bio == new_bio


@pytest.mark.regression
class TestUserAuthNegative:
    
    @qase.id(27)
    @pytest.mark.parametrize("field_to_duplicate", ["email", "username"])
    def test_duplicate_registration_error(self, registered_user, faker, field_to_duplicate):
        """Test registration with duplicate email or username returns 422 error."""
        password = faker.password(length=10)
        
        username = registered_user["username"] if field_to_duplicate == "username" else f"dup_{faker.unique.user_name()}"
        email = registered_user["email"] if field_to_duplicate == "email" else f"dup_{faker.random_int(10000, 99999)}@example.com"
        
        payload = {
            "user": {
                "username": username,
                "email": email,
                "password": password
            }
        }
        
        response = requests.post(f"{BASE_URL}/users", json=payload)
        assert response.status_code == 422, f"Expected 422 Unprocessable Entity, got {response.status_code}: {response.text}"
        
        error_model = GenericErrorModel.model_validate(response.json())
        assert "errors" in response.json()
        assert len(error_model.errors) > 0

    @qase.id(32)
    def test_login_invalid_credentials(self, faker):
        """Test login with non-existent or wrong password returns 422 or 401."""
        payload = {
            "user": {
                "email": f"nonexistent_{faker.random_int(1000, 9999)}@example.com",
                "password": "wrongpassword"
            }
        }
        
        response = requests.post(f"{BASE_URL}/users/login", json=payload)
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}: {response.text}"

    @qase.id(34)
    def test_unauthorized_get_user(self):
        """Test getting current user without auth token returns 401 Unauthorized."""
        response = requests.get(f"{BASE_URL}/user")
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @qase.id(30)
    @pytest.mark.parametrize("invalid_payload", [
        {"user": {"email": "invalid-email", "password": "123"}},
        {"user": {"username": "", "email": "test@example.com", "password": "123"}},
        {"user": {"username": "testuser", "password": "123"}}
    ])
    def test_registration_validation_errors(self, invalid_payload):
        """Test registration with invalid data yields 422 validation error."""
        response = requests.post(f"{BASE_URL}/users", json=invalid_payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        error_model = GenericErrorModel.model_validate(response.json())
        assert isinstance(error_model.errors, dict)


@pytest.mark.contract
class TestUserAuthContract:
    
    @qase.id(24)
    def test_user_response_schema_contract(self, registered_user):
        """Validate response contract against Pydantic UserModel and UserResponse models."""
        payload = {
            "user": {
                "email": registered_user["email"],
                "password": registered_user["password"]
            }
        }
        response = requests.post(f"{BASE_URL}/users/login", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        user_resp = UserResponse.model_validate(data)
        
        assert isinstance(user_resp.user.email, str)
        assert isinstance(user_resp.user.token, str)
        assert isinstance(user_resp.user.username, str)
        assert user_resp.user.bio is None or isinstance(user_resp.user.bio, str)
        assert user_resp.user.image is None or isinstance(user_resp.user.image, str)
