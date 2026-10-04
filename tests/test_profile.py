import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.profile import ProfileResponse, ProfileModel
from src.models.user import GenericErrorModel

@pytest.mark.smoke
class TestProfileSmoke:

    @qase.id(40)
    def test_get_profile_anonymously(self, target_user):
        """TC-PROF-SMK-01: Get profile anonymously (GET /api/profiles/{username})."""
        response = requests.get(f"{BASE_URL}/profiles/{target_user['username']}")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        profile_response = ProfileResponse.model_validate(response.json())
        assert profile_response.profile.username == target_user['username']
        assert profile_response.profile.following is False
        assert profile_response.profile.bio is None or isinstance(profile_response.profile.bio, str)
        assert profile_response.profile.image is None or isinstance(profile_response.profile.image, str)

    @qase.id(48)
    def test_get_profile_authenticated(self, target_user, auth_headers):
        """Get profile as authenticated user (GET /api/profiles/{username} with auth)."""
        response = requests.get(f"{BASE_URL}/profiles/{target_user['username']}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        profile_response = ProfileResponse.model_validate(response.json())
        assert profile_response.profile.username == target_user['username']
        assert isinstance(profile_response.profile.following, bool)

    @qase.id(41)
    def test_follow_user(self, target_user, auth_headers):
        """TC-PROF-SMK-02: Follow a user (POST /api/profiles/{username}/follow)."""
        response = requests.post(f"{BASE_URL}/profiles/{target_user['username']}/follow", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        profile_response = ProfileResponse.model_validate(response.json())
        assert profile_response.profile.username == target_user['username']
        assert profile_response.profile.following is True

    @qase.id(42)
    def test_unfollow_user(self, target_user, auth_headers):
        """TC-PROF-SMK-03: Unfollow a user (DELETE /api/profiles/{username}/follow)."""
        # First follow the user
        requests.post(f"{BASE_URL}/profiles/{target_user['username']}/follow", headers=auth_headers)
        
        # Then unfollow
        response = requests.delete(f"{BASE_URL}/profiles/{target_user['username']}/follow", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        profile_response = ProfileResponse.model_validate(response.json())
        assert profile_response.profile.username == target_user['username']
        assert profile_response.profile.following is False


@pytest.mark.regression
class TestProfileNegativeAndBoundary:

    @qase.id(43)
    def test_get_non_existent_profile(self, faker):
        """TC-PROF-NEG-01: Request profile of non-existent user returns 404 or 422."""
        non_existent_username = f"nonexistent_{faker.random_int(100000, 999999)}"
        response = requests.get(f"{BASE_URL}/profiles/{non_existent_username}")
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}: {response.text}"

    @qase.id(44)
    @pytest.mark.parametrize("method, endpoint_suffix", [
        ("POST", "/follow"),
        ("DELETE", "/follow")
    ])
    def test_follow_unfollow_without_token(self, target_user, method, endpoint_suffix):
        """TC-PROF-NEG-02: Follow or unfollow without authorization token returns 401."""
        url = f"{BASE_URL}/profiles/{target_user['username']}{endpoint_suffix}"
        if method == "POST":
            response = requests.post(url)
        else:
            response = requests.delete(url)
            
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @qase.id(46)
    def test_self_follow(self, registered_user, auth_headers):
        """TC-PROF-NEG-04: User attempts to follow themselves."""
        response = requests.post(f"{BASE_URL}/profiles/{registered_user['username']}/follow", headers=auth_headers)
        assert response.status_code in [200, 400, 422], f"Expected 200, 400 or 422, got {response.status_code}: {response.text}"

    @qase.id(49)
    def test_duplicate_follow_idempotency(self, target_user, auth_headers):
        """TC-PROF-MOB-02: Idempotency of duplicate follow requests."""
        url = f"{BASE_URL}/profiles/{target_user['username']}/follow"
        
        # First follow
        res1 = requests.post(url, headers=auth_headers)
        assert res1.status_code == 200
        assert ProfileResponse.model_validate(res1.json()).profile.following is True
        
        # Second follow (duplicate)
        res2 = requests.post(url, headers=auth_headers)
        assert res2.status_code == 200, f"Expected 200 OK for duplicate follow, got {res2.status_code}: {res2.text}"
        
        profile_resp = ProfileResponse.model_validate(res2.json())
        assert profile_resp.profile.username == target_user['username']
        assert profile_resp.profile.following is True

    @qase.id(50)
    def test_duplicate_unfollow_idempotency(self, target_user, auth_headers):
        """TC-PROF-MOB-03: Idempotency of duplicate unfollow requests."""
        url = f"{BASE_URL}/profiles/{target_user['username']}/follow"
        
        # Ensure unfollowed first
        requests.delete(url, headers=auth_headers)
        
        # First unfollow when already unfollowed
        res1 = requests.delete(url, headers=auth_headers)
        assert res1.status_code == 200
        assert ProfileResponse.model_validate(res1.json()).profile.following is False
        
        # Second unfollow (duplicate)
        res2 = requests.delete(url, headers=auth_headers)
        assert res2.status_code == 200, f"Expected 200 OK for duplicate unfollow, got {res2.status_code}: {res2.text}"
        
        profile_resp = ProfileResponse.model_validate(res2.json())
        assert profile_resp.profile.username == target_user['username']
        assert profile_resp.profile.following is False


@pytest.mark.contract
class TestProfileContract:

    @qase.id(51)
    def test_profile_response_schema_contract(self, target_user, auth_headers):
        """Validate profile response contract against ProfileResponse model."""
        response = requests.get(f"{BASE_URL}/profiles/{target_user['username']}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        profile_resp = ProfileResponse.model_validate(data)
        
        assert isinstance(profile_resp.profile.username, str)
        assert isinstance(profile_resp.profile.following, bool)
        assert profile_resp.profile.bio is None or isinstance(profile_resp.profile.bio, str)
        assert profile_resp.profile.image is None or isinstance(profile_resp.profile.image, str)
