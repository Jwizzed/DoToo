import re

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def find_form_tag(text):
    match = re.search(r"<form[^>]*>", text, re.IGNORECASE)
    return match.group(0) if match else "!!! FORM TAG NOT FOUND !!!"


def test_read_root_redirects_to_login_unauthenticated():
    """
    Test that accessing the root ('/') redirects to the login page
    when not authenticated (no access token cookie).
    We disable following redirects to check the Location header.
    """
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (
        status.HTTP_307_TEMPORARY_REDIRECT,
        status.HTTP_303_SEE_OTHER,
    )

    login_url_path = app.url_path_for("web_login_form")
    expected_location_suffix = str(login_url_path)

    assert response.headers.get("location") is not None

    assert response.headers["location"].endswith(expected_location_suffix)


def test_get_login_page():
    """
    Test that the login page ('/auth/login') can be accessed via GET
    and returns a successful HTML response containing the correct form action URL.
    """
    login_form_path = app.url_path_for("web_login_form")
    login_action_relative_path = app.url_path_for("web_login")

    expected_login_action_url = f"{client.base_url}{login_action_relative_path}"

    response = client.get(login_form_path)

    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert '<h1 class="mb-4 text-center fw-bold">Login</h1>' in response.text
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text

    form_tag_html = find_form_tag(response.text)
    assert form_tag_html != "!!! FORM TAG NOT FOUND !!!"

    action_pattern = re.compile(
        rf'action\s*=\s*"{re.escape(expected_login_action_url)}"', re.IGNORECASE
    )
    assert action_pattern.search(form_tag_html) is not None


def test_get_signup_page():
    """
    Test that the signup page ('/auth/signup') can be accessed via GET
    and returns a successful HTML response containing the correct form action URL.
    """
    signup_form_path = app.url_path_for("web_signup_form")
    signup_action_relative_path = app.url_path_for("web_signup")

    expected_signup_action_url = f"{client.base_url}{signup_action_relative_path}"

    response = client.get(signup_form_path)

    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert '<h1 class="mb-4 text-center fw-bold">Create Account</h1>' in response.text
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text
    assert 'name="confirm_password"' in response.text

    form_tag_html = find_form_tag(response.text)
    assert form_tag_html != "!!! FORM TAG NOT FOUND !!!"

    action_pattern = re.compile(
        rf'action\s*=\s*"{re.escape(expected_signup_action_url)}"', re.IGNORECASE
    )
    assert action_pattern.search(form_tag_html) is not None


@pytest.mark.skip(
    reason="Requires authentication and DB setup which is not implemented in this simple test"
)
def test_get_todos_page_unauthorized():
    """
    Test accessing the main todos page ('/todos/') without being logged in.
    It should redirect to login (checked by the 401 exception handler in main.py).
    """
    response = client.get(app.url_path_for("web_read_todos"), follow_redirects=False)

    assert response.status_code == status.HTTP_303_SEE_OTHER
    login_url_path = app.url_path_for("web_login_form")
    expected_location_suffix = str(login_url_path)
    assert response.headers.get("location") is not None
    assert response.headers["location"].endswith(expected_location_suffix)
