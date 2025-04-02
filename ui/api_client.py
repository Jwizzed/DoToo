from typing import Optional, Dict, Any

import httpx

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/v1"


# --- Helper Function ---
async def _request(
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generic function to make async HTTP requests to the backend."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            if form_data or files:
                # Filter out None values from form_data if necessary
                filtered_form_data = {k: v for k, v in form_data.items() if v is not None} if form_data else None
                response = await client.request(
                    method,
                    f"{BASE_URL}{endpoint}",
                    headers=headers,
                    data=filtered_form_data,
                    files=files,
                    timeout=30.0
                )
            else:
                response = await client.request(
                    method,
                    f"{BASE_URL}{endpoint}",
                    headers=headers,
                    json=json_data,
                    timeout=10.0
                )

            # Raise exceptions for 4xx/5xx errors
            response.raise_for_status()

            if response.status_code == 204: # No Content
                return {"success": True, "detail": "Operation successful (No Content)"}

            return response.json()

        except httpx.HTTPStatusError as e:
            # Try to get error detail from response body, otherwise use reason phrase
            detail = "Unknown error"
            try:
                error_data = e.response.json()
                detail = error_data.get("detail", e.response.reason_phrase)
            except Exception:
                detail = e.response.reason_phrase or f"HTTP error {e.response.status_code}"
            return {"success": False, "status_code": e.response.status_code, "detail": detail}
        except httpx.RequestError as e:
            return {"success": False, "status_code": None, "detail": f"Request error: {e}"}
        except Exception as e:
            return {"success": False, "status_code": None, "detail": f"An unexpected error occurred: {e}"}


# --- API Functions ---

async def login(username: str, password: str) -> Dict[str, Any]:
    """Login user and get JWT token."""
    form_data = {"username": username, "password": password}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return {"success": True, **response.json()}
        except httpx.HTTPStatusError as e:
            detail = "Login failed"
            try:
                error_data = e.response.json()
                detail = error_data.get("detail", "Incorrect username or password")
            except Exception:
                pass
            return {"success": False, "status_code": e.response.status_code, "detail": detail}
        except httpx.RequestError as e:
            return {"success": False, "detail": f"Network error: {e}"}


async def signup(username: str, email: str, password: str) -> Dict[str, Any]:
    """Register a new user."""
    json_data = {"username": username, "email": email, "password": password}
    result = await _request("POST", "/auth/signup", json_data=json_data)
    if "id" in result:
        result["success"] = True
    return result


async def get_todos(token: str) -> Dict[str, Any]:
    """Fetch all todos for the logged-in user."""
    result = await _request("GET", "/todos/", token=token)
    if isinstance(result, list):
        return {"success": True, "data": result}
    elif "success" in result and result["success"] is False:
        return result
    else:
        return {"success": False, "detail": "Failed to fetch todos or unexpected response format."}


async def add_todo(token: str, title: str, description: Optional[str], image_file: Optional[Any]) -> Dict[str, Any]:
    """Add a new todo, potentially with an image."""
    form_data = {"title": title, "description": description or ""}
    files = None
    if image_file:
        files = {"image_file": (image_file.name, image_file.file, image_file.type)}

    return await _request("POST", "/todos/", token=token, form_data=form_data, files=files)


async def update_todo_status(token: str, todo_id: int, status: str) -> Dict[str, Any]:
    """Update the status of a specific todo."""
    json_data = {"status": status}
    return await _request("PUT", f"/todos/{todo_id}", token=token, json_data=json_data)


async def update_todo_details(token: str, todo_id: int, title: Optional[str], description: Optional[str]) -> Dict[
    str, Any]:
    """Update the title/description of a specific todo."""
    json_data = {}
    if title is not None:
        json_data["title"] = title
    if description is not None:
        json_data["description"] = description

    if not json_data:
        return {"success": True, "detail": "No details provided for update."}

    return await _request("PUT", f"/todos/{todo_id}", token=token, json_data=json_data)


async def delete_todo(token: str, todo_id: int) -> Dict[str, Any]:
    """Delete a specific todo."""
    return await _request("DELETE", f"/todos/{todo_id}", token=token)
