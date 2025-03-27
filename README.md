# DoToo
To do (01219449 Software Architecture)
.
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

```angular2html
alembic init alembic

docker run --name todo-postgres-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=todo_db \
  -p 5432:5432 \
  -v todo_pgdata:/var/lib/postgresql/data \
  -d postgres:16

alembic revision --autogenerate -m "Initial migration with users and todos tables"
```