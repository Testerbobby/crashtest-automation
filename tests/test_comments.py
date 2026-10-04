import pytest
import requests
from qase.pytest import qase
from src.config import BASE_URL
from src.models.comment import SingleCommentResponse, MultipleCommentsResponse
from src.models.user import GenericErrorModel

@pytest.mark.smoke
class TestCommentSmoke:

    @qase.id(71)
    def test_create_comment(self, auth_headers, created_article, faker):
        """TC-COMM-SMK-01: Create a new comment to an article successfully."""
        comment_text = f"Wonderful article! {faker.sentence()}"
        payload = {
            "comment": {
                "body": comment_text
            }
        }
        response = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        comment_resp = SingleCommentResponse.model_validate(response.json())
        assert comment_resp.comment.body == comment_text
        assert isinstance(comment_resp.comment.id, str)
        assert isinstance(comment_resp.comment.author, object)
        assert isinstance(comment_resp.comment.createdAt, str)

        # Cleanup comment
        requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_resp.comment.id}",
            headers=auth_headers
        )

    @qase.id(72)
    def test_get_comments(self, auth_headers, created_article, faker):
        """TC-COMM-SMK-02: Get comments for an article."""
        # Create a comment first
        payload = {"comment": {"body": "Test comment for listing"}}
        create_res = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert create_res.status_code in [200, 201]
        comment_id = create_res.json()["comment"]["id"]

        # Get comments (can be anonymous or auth)
        response = requests.get(f"{BASE_URL}/articles/{created_article['slug']}/comments")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        multiple_resp = MultipleCommentsResponse.model_validate(response.json())
        assert isinstance(multiple_resp.comments, list)
        assert len(multiple_resp.comments) > 0

        # Cleanup
        requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_id}",
            headers=auth_headers
        )

    @qase.id(73)
    def test_delete_comment(self, auth_headers, created_article, faker):
        """TC-COMM-SMK-03: Delete comment by author successfully."""
        payload = {"comment": {"body": "Comment to be deleted"}}
        create_res = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert create_res.status_code in [200, 201]
        comment_id = create_res.json()["comment"]["id"]

        del_res = requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_id}",
            headers=auth_headers
        )
        assert del_res.status_code in [200, 204], f"Expected 200 or 204, got {del_res.status_code}: {del_res.text}"


@pytest.mark.regression
class TestCommentNegativeAndSecurity:

    @qase.id(74)
    def test_unauthorized_delete_comment(self, auth_headers, other_auth_headers, created_article):
        """TC-COMM-NEG-01: Unauthorized delete of another user's comment returns 403, 401 or 422."""
        # Create comment as registered_user
        payload = {"comment": {"body": "Protected comment"}}
        create_res = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert create_res.status_code in [200, 201]
        comment_id = create_res.json()["comment"]["id"]

        # Try to delete as other_user
        del_res = requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_id}",
            headers=other_auth_headers
        )
        assert del_res.status_code in [403, 401, 422], f"Expected 403/401/422, got {del_res.status_code}: {del_res.text}"

        # Cleanup as owner
        requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_id}",
            headers=auth_headers
        )

    @qase.id(75)
    def test_unauthenticated_creation(self, created_article):
        """TC-COMM-NEG-02: Creating comment without authorization token returns 401."""
        payload = {"comment": {"body": "Guest comment"}}
        response = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload
        )
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @qase.id(76)
    def test_empty_body_creation(self, auth_headers, created_article):
        """TC-COMM-NEG-03: Creating comment with empty body returns 422 or 200/201."""
        payload = {"comment": {"body": ""}}
        response = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 422], f"Expected 200/201/422, got {response.status_code}: {response.text}"
        if response.status_code == 422:
            error_resp = GenericErrorModel.model_validate(response.json())
            assert "body" in error_resp.errors
        else:
            # If API accepts empty body, clean it up
            comment_id = response.json()["comment"]["id"]
            requests.delete(f"{BASE_URL}/articles/{created_article['slug']}/comments/{comment_id}", headers=auth_headers)

    @qase.id(77)
    def test_non_existent_slug_comment(self, auth_headers, faker):
        """TC-COMM-NEG-04: Creating comment for non-existent article slug returns 404 or 422."""
        slug = f"non-existent-article-{faker.random_int(100000, 999999)}"
        payload = {"comment": {"body": "Orphan comment"}}
        response = requests.post(
            f"{BASE_URL}/articles/{slug}/comments",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code}: {response.text}"

    @qase.id(78)
    def test_non_existent_comment_id_delete(self, auth_headers, created_article):
        """TC-COMM-NEG-05: Deleting non-existent comment ID returns 404, 422 or 500."""
        non_existent_id = "999999990000000000000000"
        response = requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{non_existent_id}",
            headers=auth_headers
        )
        assert response.status_code in [404, 422, 500], f"Expected 404, 422 or 500, got {response.status_code}: {response.text}"


@pytest.mark.contract
class TestCommentContract:

    @qase.id(79)
    def test_comment_response_contract(self, auth_headers, created_article):
        """Contract test: Validate single and multiple comment responses against Pydantic models."""
        payload = {"comment": {"body": "Contract test comment"}}
        create_res = requests.post(
            f"{BASE_URL}/articles/{created_article['slug']}/comments",
            json=payload,
            headers=auth_headers
        )
        assert create_res.status_code in [200, 201]
        
        single_resp = SingleCommentResponse.model_validate(create_res.json())
        assert isinstance(single_resp.comment.id, str)
        assert isinstance(single_resp.comment.body, str)
        assert isinstance(single_resp.comment.createdAt, str)
        assert single_resp.comment.updatedAt is None or isinstance(single_resp.comment.updatedAt, str)
        assert isinstance(single_resp.comment.author.username, str)
        assert isinstance(single_resp.comment.author.following, bool)

        # Get multiple comments
        get_res = requests.get(f"{BASE_URL}/articles/{created_article['slug']}/comments")
        assert get_res.status_code == 200
        multi_resp = MultipleCommentsResponse.model_validate(get_res.json())
        assert isinstance(multi_resp.comments, list)
        if len(multi_resp.comments) > 0:
            c = multi_resp.comments[0]
            assert isinstance(c.id, str)
            assert isinstance(c.body, str)

        # Cleanup
        requests.delete(
            f"{BASE_URL}/articles/{created_article['slug']}/comments/{single_resp.comment.id}",
            headers=auth_headers
        )
