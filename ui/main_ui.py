from typing import Dict, Any

from nicegui import ui, app, Client

import api_client

# --- Constants ---
TODO_STATUSES = ["Pending", "In Progress", "Done"]


# --- Authentication ---

def is_authenticated() -> bool:
    """Check if user token exists in session storage."""
    return app.storage.user.get('auth_token') is not None


def require_authentication(func):
    """Decorator for NiceGUI page functions to enforce authentication."""

    async def wrapper(*args, **kwargs):
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        return await func(*args, **kwargs)

    return wrapper


# --- UI Page Functions ---

@ui.page('/login')
async def login_page():
    """Page for user login."""
    if is_authenticated():
        ui.navigate.to('/')
        return

    async def handle_login():
        """Attempt to login using credentials from inputs."""
        username = username_input.value
        password = password_input.value
        if not username or not password:
            ui.notify('Please enter username and password', type='warning')
            return

        result = await api_client.login(username, password)

        if result.get("success"):
            token = result.get("access_token")
            app.storage.user['auth_token'] = token
            app.storage.user['username'] = username
            ui.notify('Login successful!', type='positive')
            ui.navigate.to('/')
        else:
            error_detail = result.get("detail", "Login failed.")
            ui.notify(f'Login Error: {error_detail}', type='negative')

    # --- UI Layout ---
    with ui.column().classes('absolute-center items-center'):
        ui.label('Todo App Login').classes('text-h4')
        username_input = ui.input('Username', autocomplete='username').props('outlined dense required')
        password_input = ui.input('Password', password=True, password_toggle_button=True).props(
            'outlined dense required')
        ui.button('Login', on_click=handle_login).props('color=primary')
        ui.link('Need an account? Sign Up', '/signup')


@ui.page('/signup')
async def signup_page():
    """Page for user registration."""
    if is_authenticated():
        ui.navigate.to('/')
        return

    async def handle_signup():
        """Attempt to register using credentials from inputs."""
        username = username_input.value
        email = email_input.value
        password = password_input.value
        confirm_password = confirm_password_input.value

        if not all([username, email, password, confirm_password]):
            ui.notify('Please fill in all fields', type='warning')
            return
        if password != confirm_password:
            ui.notify('Passwords do not match', type='warning')
            return

        result = await api_client.signup(username, email, password)

        if result.get("success"):
            ui.notify('Signup successful! Please log in.', type='positive')
            ui.navigate.to('/login')  # Redirect to login page after signup
        else:
            error_detail = result.get("detail", "Signup failed.")
            ui.notify(f'Signup Error: {error_detail}', type='negative')

    # --- UI Layout ---
    with ui.column().classes('absolute-center items-center'):
        ui.label('Sign Up').classes('text-h4')
        username_input = ui.input('Username').props('outlined dense required')
        email_input = ui.input('Email', type='email').props('outlined dense required')
        password_input = ui.input('Password', password=True).props('outlined dense required')
        confirm_password_input = ui.input('Confirm Password', password=True).props('outlined dense required')
        ui.button('Sign Up', on_click=handle_signup).props('color=primary')
        ui.link('Already have an account? Login', '/login')


@ui.page('/')
@require_authentication
async def main_page(client: Client):
    """Main page displaying the Todo list."""

    token = app.storage.user.get('auth_token')
    username = app.storage.user.get('username', 'User')
    todos_list_container = None
    upload_ref = None

    # --- Data Fetching and Refreshing ---
    async def fetch_and_display_todos():
        """Fetches todos from API and updates the UI."""
        nonlocal todos_list_container  # Allow modification of the outer scope variable
        result = await api_client.get_todos(token)

        if todos_list_container is None:  # Should not happen if layout is built first
            print("Error: Todo list container not initialized before fetch.")
            return

        todos_list_container.clear()  # Clear previous items

        if result.get("success"):
            todos = result.get("data", [])
            if not todos:
                with todos_list_container:
                    ui.label("No tasks yet! Add one below.").classes('text-grey')
            else:
                with todos_list_container:
                    for todo in todos:
                        create_todo_item_card(todo)  # Create UI for each todo
        else:
            error_detail = result.get("detail", "Failed to load todos.")
            ui.notify(f'Error: {error_detail}', type='negative')
            with todos_list_container:
                ui.label(f"Error loading tasks: {error_detail}").classes('text-negative')

    # --- Event Handlers ---
    async def handle_add_todo(e):
        """Handles adding a new todo item."""
        nonlocal upload_ref  # Access the upload component reference
        title = add_title_input.value
        description = add_desc_input.value

        if not title:
            ui.notify('Title is required', type='warning')
            return

        # Handle file upload data from the event `e`
        uploaded_file = None
        if e and hasattr(e, 'files') and e.files:
            uploaded_file = e.files[0]  # Assuming single file upload

        ui.notify('Adding task...', type='info', spinner=True)
        result = await api_client.add_todo(token, title, description, uploaded_file)

        if result.get("success"):
            ui.notify('Task added successfully!', type='positive')
            # Clear input fields
            add_title_input.value = ''
            add_desc_input.value = ''
            if upload_ref:
                # Resetting the upload component is tricky, might need specific methods if available
                # Or just notify user upload was processed.
                # await upload_ref.reset() # Check NiceGUI docs for correct method
                upload_ref.clear()  # Clears the list of files in the uploader
                pass  # Let user know upload was part of the request

            await fetch_and_display_todos()  # Refresh the list
        else:
            error_detail = result.get("detail", "Failed to add task.")
            ui.notify(f'Error: {error_detail}', type='negative')

    async def handle_update_status(todo_id: int, new_status: str):
        """Handles updating the status of a todo item."""
        ui.notify('Updating status...', type='info')
        result = await api_client.update_todo_status(token, todo_id, new_status)
        if result.get("success"):
            ui.notify('Status updated!', type='positive')
            await fetch_and_display_todos()  # Refresh the list
        else:
            error_detail = result.get("detail", "Failed to update status.")
            ui.notify(f'Error: {error_detail}', type='negative')

    async def handle_delete_todo(todo_id: int):
        """Handles deleting a todo item."""
        # Optional: Add a confirmation dialog
        # await ui.dialog().confirm('Are you sure you want to delete this task?').on('confirm', lambda: proceed_delete(todo_id)) ...
        ui.notify('Deleting task...', type='info')
        result = await api_client.delete_todo(token, todo_id)
        if result.get("success"):
            ui.notify('Task deleted!', type='positive')
            await fetch_and_display_todos()  # Refresh the list
        else:
            error_detail = result.get("detail", "Failed to delete task.")
            ui.notify(f'Error: {error_detail}', type='negative')

    def handle_logout():
        """Clears authentication token and redirects to login."""
        app.storage.user.clear()  # Clear all user session data
        ui.navigate.to('/login')
        ui.notify('You have been logged out.', type='info')

    # --- UI Component Creation ---
    def create_todo_item_card(todo: Dict[str, Any]):
        """Creates the UI card for a single todo item."""
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center justify-between'):
                # Title and Description
                with ui.column().classes('flex-grow'):
                    ui.label(todo['title']).classes('text-lg font-semibold')
                    if todo.get('description'):
                        ui.label(todo['description']).classes('text-sm text-grey')

                # Optional: Image Display
                if todo.get('image_url'):
                    with ui.column().classes('items-center'):  # Limit image size if needed
                        ui.image(todo['image_url']).classes('w-20 h-auto rounded')  # Adjust size as needed

                # Status Dropdown
                with ui.column().classes('items-end'):  # Align controls to the right
                    ui.select(
                        options=TODO_STATUSES,
                        value=todo['status'],
                        label='Status',
                        on_change=lambda e, tid=todo['id']: handle_update_status(tid, e.value)
                    ).props('dense outlined').classes('w-40')  # Adjust width

                    # Delete Button
                    ui.button(icon='delete', on_click=lambda tid=todo['id']: handle_delete_todo(tid)).props(
                        'flat color=negative round dense')

    # --- Page Layout ---
    with ui.header().classes('bg-primary text-white'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label(f'{username}\'s Todos').classes('text-h5')
            ui.button('Logout', on_click=handle_logout, icon='logout').props('flat round dense')

    ui.label('Add New Task').classes('text-h6 mt-4')
    with ui.card().classes('w-full'):
        add_title_input = ui.input('Title').props('outlined dense required').classes('w-full')
        add_desc_input = ui.textarea('Description').props('outlined dense').classes('w-full')
        # File Upload (Optional) - use on_upload for immediate processing, or include in form submission logic
        # Here we tie it to the 'Add Task' button click via the event 'e'
        upload_ref = ui.upload(
            label="Optional Image",
            auto_upload=False,  # Don't upload automatically, handle with button click
            max_files=1,
            max_file_size=5_000_000,  # 5MB limit example
            # on_upload=lambda e: handle_file_upload(e.files), # Alternative: Handle upload separately
        ).props('dense flat bordered').classes('w-full')

        # Pass the upload event 'e' to the handler
        ui.button('Add Task', on_click=lambda e: handle_add_todo(e), icon='add').props('color=positive')

    ui.separator().classes('my-4')
    ui.label('Your Tasks').classes('text-h6')

    # Container where todo items will be dynamically added/removed
    todos_list_container = ui.column().classes('w-full gap-2')

    # Initial data fetch when the page loads and client is connected
    await client.connected()  # Ensure client is connected before fetching
    await fetch_and_display_todos()


# --- Run the UI ---
# The host and port should not conflict with your backend API
ui.run(storage_secret='a_secure_secret_key_for_storage', host='localhost',
       port=8080)  # Use a different port than the backend!
