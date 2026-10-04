import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.tag import TagsResponse

@pytest.mark.smoke
class TestTagsSmoke:

    @qase.id(89)
    def test_get_tags_as_guest(self):
        """TC-TAG-SMK-01: Get tags list as guest (anonymously)."""
        response = requests.get(f"{BASE_URL}/tags")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        tags_resp = TagsResponse.model_validate(response.json())
        assert isinstance(tags_resp.tags, list)
        for tag in tags_resp.tags:
            assert isinstance(tag, str)

    @qase.id(90)
    def test_get_tags_as_auth_user(self, auth_headers):
        """TC-TAG-SMK-02: Get tags list as authenticated user."""
        response = requests.get(f"{BASE_URL}/tags", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        tags_resp = TagsResponse.model_validate(response.json())
        assert isinstance(tags_resp.tags, list)


@pytest.mark.regression
class TestTagsEdgeCases:

    @qase.id(93)
    def test_new_tag_appears_after_article_creation(self, auth_headers, faker):
        """TC-TAG-EDG-03: Newly created article tag appears in global tags list."""
        unique_tag = f"tag{faker.random_int(10000, 99999)}"
        payload = {
            "article": {
                "title": f"Article with tag {unique_tag}",
                "description": "Tag test description",
                "body": "Tag test body",
                "tagList": [unique_tag]
            }
        }
        create_res = requests.post(f"{BASE_URL}/articles", json=payload, headers=auth_headers)
        assert create_res.status_code in [200, 201]
        slug = create_res.json()["article"]["slug"]

        # Check global tags
        response = requests.get(f"{BASE_URL}/tags")
        assert response.status_code == 200
        tags_resp = TagsResponse.model_validate(response.json())
        assert unique_tag in tags_resp.tags

        # Cleanup article
        requests.delete(f"{BASE_URL}/articles/{slug}", headers=auth_headers)


@pytest.mark.contract
class TestTagsContract:

    @qase.id(91)
    def test_tags_response_contract(self):
        """Contract test: Validate tags response schema matches TagsResponse (list[str])."""
        response = requests.get(f"{BASE_URL}/tags")
        assert response.status_code == 200

        data = response.json()
        tags_resp = TagsResponse.model_validate(data)
        assert isinstance(tags_resp.tags, list)
        if len(tags_resp.tags) > 0:
            assert all(isinstance(t, str) for t in tags_resp.tags)
