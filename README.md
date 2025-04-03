

```angular2html
docker run --name todo-db \
  -e POSTGRES_USER=postgres_user \
  -e POSTGRES_PASSWORD=postgres_password \
  -e POSTGRES_DB=todo_db \
  -p 5432:5432 \
  -v todo-db-data:/var/lib/postgresql/data \
  --restart unless-stopped \
  -d postgres:15
```

```angular2html
alembic revision --autogenerate -m "Initial migration creating user and todo tables"
alembic upgrade head
```