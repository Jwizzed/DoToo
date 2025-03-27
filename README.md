# DoToo
# Todo Application (FastAPI + PostgreSQL + SQLAlchemy)

A simple Todo list application built with FastAPI, using PostgreSQL as the database via SQLAlchemy (async) and Alembic for migrations. It follows a layered architecture enhanced with event-driven patterns (using FastAPI BackgroundTasks).

## Features

- User Authentication (Signup/Login with JWT)
- Create, Read, Update, Delete (CRUD) Todo items per user
- Todo Status Updates (Pending, In Progress, Done)
- [Optional] Upload an image associated with a Todo item.
- Layered Architecture (API, Services, Repositories)
- Asynchronous Database Operations (asyncpg, AsyncSession)
- Database Migrations (Alembic)
- Configuration via Environment Variables (.env)
- Background Tasks for decoupling (e.g., notifications)
- Basic CORS setup

## Project Structure
```
├── alembic/                  # Alembic migration scripts
├── alembic.ini               # Alembic configuration
├── app/                      # Main application source code
│   ├── api/                  # API layer (presentation)
│   │   ├── deps.py           # Dependency injection functions
│   │   └── v1/               # API version 1
│   │       ├── endpoints/    # Route definitions
│   │       │   ├── auth.py
│   │       │   └── todos.py
│   │       └── schemas/      # Pydantic schemas (data contracts)
│   │           ├── auth.py
│   │           ├── base.py
│   │           ├── todo.py
│   │           └── user.py
│   ├── core/                 # Core logic/business rules & security
│   │   ├── config.py         # Application settings/configuration
│   │   └── security.py       # Password hashing, token generation/verification
│   ├── db/                   # Database related setup
│   │   ├── base.py           # SQLAlchemy Base and session setup
│   │   └── models/           # SQLAlchemy ORM models
│   │       ├── __init__.py
│   │       ├── todo.py
│   │       └── user.py
│   ├── events/               # Event handling logic
│   │   ├── event_handlers.py # Functions to run on events (e.g., background tasks)
│   │   └── tasks.py          # Placeholder for more complex async tasks if needed
│   ├── exceptions/           # Custom application exceptions
│   │   └── base.py
│   ├── repositories/         # Data access layer
│   │   ├── base.py           # Base repository (optional)
│   │   ├── todo_repository.py
│   │   └── user_repository.py
│   ├── services/             # Service layer (orchestration)
│   │   ├── auth_service.py
│   │   └── todo_service.py
│   ├── static/               # For storing uploaded files (optional feature)
│   │   └── images/
│   └── main.py               # FastAPI application entry point
├── requirements.txt          # Project dependencies
├── .env                      # Environment variables (sensitive data) - DO NOT COMMIT
├── .gitignore                # Files/directories to ignore in git
└── README.md                 # Project description and setup instructions
```
## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up PostgreSQL:**
    * Ensure PostgreSQL server is running.
    * Create a database (e.g., `todo_db`) and a user/password.
    ```angular2html
    docker run --name todo-postgres-db \
      -e POSTGRES_USER=user \
      -e POSTGRES_PASSWORD=password \
      -e POSTGRES_DB=todo_db \
      -p 5432:5432 \
      -v todo_pgdata:/var/lib/postgresql/data \
      -d postgres:16
    ```

5.  **Configure Environment Variables:**
    * Copy the `sample.env`  or create a `.env` file in the project root.
    * Update the `DATABASE_URL` with your PostgreSQL connection string (using `asyncpg` driver):
        ```dotenv
        DATABASE_URL="postgresql+asyncpg://user:password@host:port/database_name"
        ```
    * Generate a strong `SECRET_KEY` (e.g., `openssl rand -hex 32`) and update it in `.env`.
    * Adjust `IMAGE_BASE_URL` if your server runs on a different address/port.

6.  **Run Database Migrations:**
    * Make sure the `DATABASE_URL` in `.env` is correct.
    * Apply the migrations:
        ```bash
        alembic upgrade head
        ```
    * *(If you modify models later, generate new migrations: `alembic revision --autogenerate -m "Description of changes"`)*

## Running the Application

Use Uvicorn to run the FastAPI application:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
