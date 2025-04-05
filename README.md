# DoToo - Full-Stack Todo Application

[![Run Python Tests](https://github.com/Jwizzed/DoToo/actions/workflows/ci.yml/badge.svg)](https://github.com/Jwizzed/DoToo/actions/workflows/ci.yml)

DoToo is a full-stack web application built with FastAPI and Jinja2 for managing your tasks efficiently. It features user authentication, task creation, updates, deletion, filtering, sorting, and optional image uploads.

**Live Application:** [https://dotoo.onrender.com/](https://dotoo.onrender.com/)

## Features

* **User Authentication:** Secure user registration and login using JWT tokens stored in HTTP-only cookies.
* **CRUD Operations:** Create, Read, Update, and Delete Todo items.
* **Task Management:** Assign titles, descriptions, due dates, and priorities (High, Medium, Low).
* **Filtering & Sorting:** Filter todos by status or priority, and sort by creation date, due date, or priority.
* **Search:** Search todos by title or description.
* **Photo Uploads:** Optionally attach photos to your todos (uses Cloudinary).
* **Responsive UI:** User interface built with Bootstrap 5 and Jinja2 templates.
* **Database Migrations:** Uses Alembic for managing database schema changes.
* **Asynchronous:** Built with FastAPI and `asyncpg` for asynchronous database operations.
* **Testing:** Includes unit/integration tests using `pytest`.
* **CI/CD:** Automated testing pipeline using GitHub Actions.

## UI Previews

Here's a glimpse of the DoToo application interface:

**Login Page:**
![Login Page](ui_previews/login.png)

**Signup Page:**
![Signup Page](ui_previews/signup.png)

**Todo List Page:**
![Todo List Page](ui_previews/todo_overview.png)

**Add Todo Form:**
![Add Todo Form](ui_previews/todo_form.pngg)

**Edit Todo Page:**
![Edit Todo Page](ui_previews/edit_todo.png)


## Tech Stack

* **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Database:** [PostgreSQL](https://www.postgresql.org/)
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (Async with `asyncpg`)
* **Database Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
* **Templating Engine:** [Jinja2](https://jinja.palletsprojects.com/)
* **Frontend Styling:** [Bootstrap 5](https://getbootstrap.com/)
* **Authentication:** JWT (JSON Web Tokens) via `python-jose`, password hashing via `passlib[bcrypt]`
* **Data Validation:** [Pydantic](https://docs.pydantic.dev/)
* **Image Storage:** [Cloudinary](https://cloudinary.com/) (Optional)
* **Testing:** [Pytest](https://docs.pytest.org/)
* **Web Server (Development):** [Uvicorn](https://www.uvicorn.org/)
* **Containerization (Local DB):** [Docker](https://www.docker.com/)
* **CI/CD:** [GitHub Actions](https://github.com/features/actions)

## Project Structure

The project follows a layered architecture promoting separation of concerns:

```angular2html
DoToo/
├── .github/workflows/ci.yml  # GitHub Actions CI configuration
├── alembic/                  # Alembic migration scripts
├── app/                      # Main application source code
│   ├── core/                 # Core settings, security helpers
│   ├── crud/                 # Create, Read, Update, Delete database operations
│   ├── db/                   # Database models (SQLAlchemy), session management
│   ├── schemas/              # Pydantic schemas for data validation & serialization
│   ├── services/             # Business logic services (Auth, Todo, Orchestrator)
│   ├── static/               # Static files (CSS)
│   └── web/                  # Web layer (FastAPI routers, dependencies, templates)
│       ├── deps.py           # Request dependencies (e.g., get current user)
│       ├── routes/           # API/Web route definitions
│       └── templates/        # Jinja2 HTML templates
├── tests/                    # Pytest tests
├── ui_previews/              # UI Screenshot images (Added this line for clarity)
├── .env.example              # Example environment variables file
├── alembic.ini               # Alembic configuration
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Database

* **Type:** PostgreSQL
* **Tables:**
    * `users`: Stores user information (id, email, hashed\_password, is\_active).
    * `todos`: Stores todo items (id, title, description, status, created\_at, updated\_at, owner\_id, photo\_filename, due\_date, priority). Relationships are defined via SQLAlchemy models in `app/db/models.py`.
* **Local Setup:** A PostgreSQL database running in a Docker container is recommended for local development.
* **Production Setup:** The production database is hosted on Render: `postgresql+asyncpg://todo_db_r08f_user:*****@dpg-cvoil8buibrs73brtqjg-a.singapore-postgres.render.com/todo_db_r08f`
* **Migrations:** Alembic is used to manage database schema changes.
    * Generate a new migration: `alembic revision --autogenerate -m "Your migration message"`
    * Apply migrations: `alembic upgrade head`

## Getting Started / Local Setup

### Prerequisites

* Python 3.11+
* Docker (for local database)
* Git

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Jwizzed/DoToo.git](https://github.com/Jwizzed/DoToo.git)
    cd DoToo
    ```

2.  **Set Up Environment Variables:**
    * Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    * **Edit the `.env` file** and provide necessary values:
        * `SECRET_KEY`: A strong, random secret key (important for security). You can generate one using `openssl rand -hex 32`.
        * `DATABASE_URL`: Set to the local Docker database URL: `postgresql+asyncpg://postgres_user:postgres_password@localhost:5432/todo_db`
        * `CLOUDINARY_URL` (Optional): If you want to use photo uploads, provide your Cloudinary environment variable URL. Otherwise, leave it blank or comment it out (photo features will be disabled).

3.  **Install Dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

4.  **Start the Local Database (Docker):**
    Use the command provided (ensure Docker Desktop is running):
    ```bash
    docker run --name todo-db \
      -e POSTGRES_USER=postgres_user \
      -e POSTGRES_PASSWORD=postgres_password \
      -e POSTGRES_DB=todo_db \
      -p 5432:5432 \
      -v todo-db-data:/var/lib/postgresql/data \
      --restart unless-stopped \
      -d postgres:15
    ```
    *Note: This uses the credentials defined in the `.env` file's `DATABASE_URL`.*

5.  **Apply Database Migrations:**
    Make sure your virtual environment is active and the database container is running.
    ```bash
    alembic upgrade head
    ```

6.  **Run the Application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will be available at `http://127.0.0.1:8000`.

## Deployment

* **Production:** The application is deployed on [Render](https://render.com/) and accessible at [https://dotoo.onrender.com/](https://dotoo.onrender.com/).
* **CI/CD:** The `.github/workflows/ci.yml` file defines a GitHub Actions workflow that automatically runs tests (`pytest`) on every push or pull request to the `main` branch. This helps ensure code quality and catch regressions early.

## Testing

* Tests are written using `pytest` and located in the `tests/` directory.
* The current tests focus on basic web route accessibility (`tests/test_web_routes.py`).
* To run tests locally (ensure dependencies are installed and `.env` is configured for testing if needed):
    ```bash
    # Make sure PYTHONPATH includes the project root if running from a subdirectory
    export PYTHONPATH=$(pwd) # Or set appropriately for your environment
    python -m pytest -v
    ```
    *(See `.github/workflows/ci.yml` for how tests are run in the CI environment, including setting up a dummy `.env`)*.

## Code Explanation / Architecture

This project utilizes several architectural patterns to ensure maintainability, testability, and separation of concerns:

1.  **Layered Architecture:**
    * **Presentation Layer (`app/web`):** Handles HTTP requests, interacts with services, renders templates (Jinja2), and manages user sessions/authentication via cookies. Uses FastAPI routers and dependencies (`Depends`).
    * **Service Layer (`app/services`):** Contains the core business logic. It orchestrates operations by coordinating between different CRUD functions and external services (like Cloudinary).
    * **Data Access Layer (`app/crud`):** Responsible for direct database interactions (Create, Read, Update, Delete) using SQLAlchemy ORM. Keeps database query logic separate.
    * **Domain Layer (`app/db/models.py`, `app/schemas`):** Defines the data structures (SQLAlchemy models for the database, Pydantic schemas for API validation and serialization).
    * **Core Layer (`app/core`):** Holds application-wide configurations (`config.py`) and utilities like security functions (`security.py` for password hashing and JWT).

2.  **Service Oriented Architecture (SOA) / Orchestration:**
    * The `OrchestratorService` (`app/services/orchestrator_service.py`) acts as a central coordinator for complex actions involving multiple domains (e.g., handling login requires both authentication logic from `AuthService` and potentially user data). This prevents web routes from becoming overly complex and keeps business workflows encapsulated within the service layer.
    * Individual services like `AuthService` and `TodoService` handle specific business domains.

3.  **Dependency Injection:** FastAPI's `Depends` system is used extensively (e.g., in `app/web/deps.py`, route signatures) to inject dependencies like database sessions (`get_db`) and the current user (`get_current_active_user_from_cookie`), making components easier to test and reuse.

4.  **Configuration Management:** Settings are managed via environment variables loaded into a Pydantic `Settings` model (`app/core/config.py`), allowing for different configurations between development, testing, and production without code changes.

5.  **Asynchronous Operations:** Leveraging FastAPI's async capabilities and `asyncpg` with SQLAlchemy ensures non-blocking I/O operations, particularly for database interactions, leading to better performance under concurrent load.

6.  **Photo Handling:** The `TodoService` interacts with the Cloudinary API (if configured) to upload and delete photos associated with todo items, abstracting this external interaction away from the CRUD and web layers.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.
