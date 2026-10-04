import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.article import SingleArticleResponse

@pytest.mark.smoke
class TestFavoritesSmoke:

    @qase.id(83)
    def test_favorite_article(self, auth_headers, created_article):
        """TC-FAV-SMK-01: Favorite an article successfully."""
        slug = created_article["slug"]
        initial_count = created_article["favoritesCount"]

        response = requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.favorited is True
        assert article_resp.article.favoritesCount == initial_count + 1

        # Cleanup by unfavoriting
        requests.delete(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)

    @qase.id(84)
    def test_unfavorite_article(self, auth_headers, created_article):
        """TC-FAV-SMK-02: Unfavorite an article successfully."""
        slug = created_article["slug"]
        
        # First favorite
        requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)

        # Then unfavorite
        response = requests.delete(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.favorited is False


@pytest.mark.regression
class TestFavoritesNegativeAndEdge:

    @qase.id(85)
    def test_unauthenticated_favorite(self, created_article):
        """TC-FAV-NEG-01: Favoriting article without authentication token returns 401."""
        slug = created_article["slug"]
        response = requests.post(f"{BASE_URL}/articles/{slug}/favorite")
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @qase.id(86)
    def test_non_existent_article_favorite(self, auth_headers, faker):
        """TC-FAV-NEG-02: Favoriting non-existent article slug returns 404 or 422."""
        slug = f"non-existent-slug-{faker.random_int(100000, 999999)}"
        response = requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}: {response.text}"

    @qase.id(87)
    def test_double_favorite_idempotency(self, auth_headers, created_article):
        """TC-FAV-EDG-01: Idempotency of duplicate favorite requests."""
        slug = created_article["slug"]
        
        # First favorite
        res1 = requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
        assert res1.status_code == 200
        count_1 = SingleArticleResponse.model_validate(res1.json()).article.favoritesCount
        assert SingleArticleResponse.model_validate(res1.json()).article.favorited is True

        # Second favorite (duplicate)
        res2 = requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
        assert res2.status_code == 200, f"Expected 200 OK for duplicate favorite, got {res2.status_code}: {res2.text}"
        
        article_resp = SingleArticleResponse.model_validate(res2.json())
        assert article_resp.article.favorited is True
        assert article_resp.article.favoritesCount == count_1

        # Cleanup
        requests.delete(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)

    @qase.id(88)
    def test_guest_favorites_count_view(self, auth_headers, created_article):
        """TC-FAV-EDG-02: Guest viewing article sees correct favoritesCount and favorited=false."""
        slug = created_article["slug"]
        
        # Favorite as auth user
        requests.post(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)

        # View as guest (no auth headers)
        response = requests.get(f"{BASE_URL}/articles/{slug}")
        assert response.status_code == 200
        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.favorited is False
        assert article_resp.article.favoritesCount >= 1

        # Cleanup
        requests.delete(f"{BASE_URL}/articles/{slug}/favorite", headers=auth_headers)
