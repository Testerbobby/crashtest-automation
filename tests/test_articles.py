import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.article import SingleArticleResponse, MultipleArticlesResponse
from src.models.user import GenericErrorModel

@pytest.mark.smoke
class TestArticleSmoke:

    @qase.id(52)
    def test_create_article(self, auth_headers, faker):
        """TC-ART-SMK-01: Create a new article successfully."""
        title = f"Dragon Training {faker.random_int(10000, 99999)}"
        payload = {
            "article": {
                "title": title,
                "description": "Ever wonder how to train your dragon?",
                "body": "It takes a lot of time and patience.",
                "tagList": ["reactjs", "angularjs"]
            }
        }
        response = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
        assert response.status_code in [200, 201], f"Expected 200/201 Created, got {response.status_code}: {response.text}"

        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.title == title
        assert article_resp.article.description == payload["article"]["description"]
        assert article_resp.article.body == payload["article"]["body"]
        assert set(article_resp.article.tagList) == set(payload["article"]["tagList"])
        assert isinstance(article_resp.article.slug, str)
        assert isinstance(article_resp.article.author, object)

        # Cleanup created article
        requests.delete(f"{BASE_URL}/articles/{article_resp.article.slug}", headers=auth_headers)

    @qase.id(53)
    def test_get_article_by_slug(self, created_article):
        """TC-ART-SMK-02: Get an article by its slug."""
        response = requests.get(f"{BASE_URL}/articles/{created_article['slug']}")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.slug == created_article["slug"]
        assert article_resp.article.title == created_article["title"]

    @qase.id(54)
    def test_get_global_articles(self):
        """TC-ART-SMK-03: Get global articles feed with query parameters."""
        response = requests.get(f"{BASE_URL}/articles?limit=5&offset=0")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleArticlesResponse.model_validate(response.json())
        assert isinstance(multiple_resp.articles, list)
        assert isinstance(multiple_resp.articlesCount, int)
        assert len(multiple_resp.articles) <= 5

    @qase.id(55)
    def test_get_articles_feed(self, auth_headers):
        """TC-ART-SMK-04: Get personal feed for authenticated user."""
        response = requests.get(f"{BASE_URL}/articles/feed", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleArticlesResponse.model_validate(response.json())
        assert isinstance(multiple_resp.articles, list)
        assert isinstance(multiple_resp.articlesCount, int)

    @qase.id(56)
    def test_update_article(self, auth_headers, created_article, faker):
        """TC-ART-SMK-05: Update an existing article."""
        new_title = f"Updated Title {faker.random_int(1000, 9999)}"
        payload = {
            "article": {
                "title": new_title,
                "description": "Updated description"
            }
        }
        response = requests.put(f"{BASE_URL}/articles/{created_article['slug']}", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        article_resp = SingleArticleResponse.model_validate(response.json())
        assert article_resp.article.title == new_title
        assert article_resp.article.description == "Updated description"

    @qase.id(57)
    def test_delete_article(self, auth_headers, faker):
        """TC-ART-SMK-06: Delete an article successfully."""
        # Create an article specifically for deletion
        title = f"Article To Delete {faker.random_int(1000, 9999)}"
        payload = {
            "article": {
                "title": title,
                "description": "Delete me",
                "body": "Body text"
            }
        }
        create_res = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
        assert create_res.status_code in [200, 201]
        slug = create_res.json()["article"]["slug"]

        # Delete article
        del_res = requests.delete(f"{BASE_URL}/articles/{slug}", headers=auth_headers)
        assert del_res.status_code in [200, 204], f"Expected 200 or 204, got {del_res.status_code}: {del_res.text}"

        # Verify article is no longer found
        get_res = requests.get(f"{BASE_URL}/articles/{slug}")
        assert get_res.status_code in [404, 422], f"Expected 404 or 422 after deletion, got {get_res.status_code}"


@pytest.mark.regression
class TestArticleNegativeAndSecurity:

    @qase.id(62)
    def test_create_article_without_token(self):
        """TC-ART-NEG-05: Creating article without authentication token returns 401."""
        payload = {
            "article": {
                "title": "Unauthorized Article",
                "description": "No token",
                "body": "Should fail"
            }
        }
        response = requests.post(f"{BASE_URL}/articles", json=payload)
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @qase.id(58)
    @pytest.mark.parametrize("invalid_article", [
        {"description": "Missing title", "body": "Body"},
        {}
    ])
    def test_create_article_missing_required_fields(self, auth_headers, invalid_article):
        """TC-ART-NEG-01: Creating article without required fields returns 422 or 400/500."""
        payload = {"article": invalid_article}
        response = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422, 500], f"Expected error status code, got {response.status_code}: {response.text}"

    @qase.id(59)
    def test_edit_or_delete_other_users_article(self, auth_headers, other_auth_headers, created_article):
        """TC-ART-NEG-02: Unauthorized edit or delete of another user's article returns 403 or 401."""
        # Try to update other user's article
        update_payload = {"article": {"title": "Hacked Title"}}
        update_res = requests.put(f"{BASE_URL}/articles/{created_article['slug']}", json=update_payload, headers=other_auth_headers)
        assert update_res.status_code in [403, 401, 422], f"Expected 403/401/422, got {update_res.status_code}: {update_res.text}"

        # Try to delete other user's article
        del_res = requests.delete(f"{BASE_URL}/articles/{created_article['slug']}", headers=other_auth_headers)
        assert del_res.status_code in [403, 401, 422], f"Expected 403/401/422, got {del_res.status_code}: {del_res.text}"

    @qase.id(60)
    def test_get_non_existent_article(self, faker):
        """TC-ART-NEG-03: Requesting non-existent article slug returns 404 or 422."""
        slug = f"non-existent-slug-{faker.random_int(100000, 999999)}"
        response = requests.get(f"{BASE_URL}/articles/{slug}")
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}: {response.text}"

    @qase.id(61)
    def test_get_feed_without_token(self):
        """TC-ART-NEG-04: Getting personal feed without authentication token returns 401."""
        response = requests.get(f"{BASE_URL}/articles/feed")
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"


@pytest.mark.regression
class TestArticleFilteringPagination:

    @qase.id(63)
    def test_filter_articles_by_tag(self, auth_headers, faker):
        """TC-ART-FIL-01: Filter articles by tag query parameter."""
        tag = f"tag{faker.random_int(1000, 9999)}"
        payload = {
            "article": {
                "title": f"Tagged Article {faker.random_int(1000, 9999)}",
                "description": "Tag filter test",
                "body": "Body content",
                "tagList": [tag]
            }
        }
        create_res = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
        assert create_res.status_code in [200, 201]
        slug = create_res.json()["article"]["slug"]

        # Filter by tag
        response = requests.get(f"{BASE_URL}/articles?tag={tag}")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleArticlesResponse.model_validate(response.json())
        assert multiple_resp.articlesCount > 0
        for article in multiple_resp.articles:
            assert tag in article.tagList

        # Cleanup
        requests.delete(f"{BASE_URL}/articles/{slug}", headers=auth_headers)

    @qase.id(64)
    def test_filter_articles_by_author(self, registered_user, created_article):
        """TC-ART-FIL-02: Filter articles by author query parameter."""
        username = registered_user["username"]
        response = requests.get(f"{BASE_URL}/articles?author={username}")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleArticlesResponse.model_validate(response.json())
        assert multiple_resp.articlesCount > 0
        for article in multiple_resp.articles:
            assert article.author.username == username

    @qase.id(66)
    def test_pagination_limit_offset(self):
        """TC-ART-FIL-04: Pagination with limit and offset query parameters."""
        response = requests.get(f"{BASE_URL}/articles?limit=2&offset=0")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleArticlesResponse.model_validate(response.json())
        assert len(multiple_resp.articles) <= 2


@pytest.mark.contract
class TestArticleContract:

    @qase.id(67)
    def test_single_article_response_contract(self, created_article):
        """Contract test: Validate single article response matches SingleArticleResponse schema."""
        response = requests.get(f"{BASE_URL}/articles/{created_article['slug']}")
        assert response.status_code == 200
        
        data = response.json()
        article_resp = SingleArticleResponse.model_validate(data)
        
        assert isinstance(article_resp.article.slug, str)
        assert isinstance(article_resp.article.title, str)
        assert article_resp.article.description is None or isinstance(article_resp.article.description, str)
        assert article_resp.article.body is None or isinstance(article_resp.article.body, str)
        assert isinstance(article_resp.article.tagList, list)
        assert isinstance(article_resp.article.createdAt, str)
        assert isinstance(article_resp.article.updatedAt, str)
        assert isinstance(article_resp.article.favorited, bool)
        assert isinstance(article_resp.article.favoritesCount, int)
        assert isinstance(article_resp.article.author.username, str)
        assert isinstance(article_resp.article.author.following, bool)

    @qase.id(68)
    def test_multiple_articles_response_contract(self):
        """Contract test: Validate multiple articles response matches MultipleArticlesResponse schema."""
        response = requests.get(f"{BASE_URL}/articles?limit=3")
        assert response.status_code == 200
        
        data = response.json()
        multiple_resp = MultipleArticlesResponse.model_validate(data)
        
        assert isinstance(multiple_resp.articles, list)
        assert isinstance(multiple_resp.articlesCount, int)
        
        if len(multiple_resp.articles) > 0:
            article = multiple_resp.articles[0]
            assert isinstance(article.slug, str)
            assert isinstance(article.title, str)
            assert isinstance(article.favorited, bool)
            assert isinstance(article.favoritesCount, int)
            assert isinstance(article.author.username, str)
