# Backend - Phase-II Todo Application

FastAPI backend with SQLModel ORM and Neon PostgreSQL.

## Setup

### Prerequisites
- Python 3.11+
- Neon PostgreSQL account and connection string

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Neon connection string and JWT secret
```

4. Generate JWT secret:
```bash
openssl rand -hex 32
```

### Running

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API Documentation: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── database.py       # Database connection
│   ├── models.py         # SQLModel models
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # Authentication logic
│   ├── dependencies.py   # FastAPI dependencies
│   └── routers/
│       ├── auth.py       # Auth endpoints
│       └── tasks.py      # Task endpoints
├── tests/                # Tests
├── requirements.txt      # Dependencies
└── .env                  # Environment variables (not committed)
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user

### Tasks
- `GET /api/tasks` - Get all tasks for current user
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{id}` - Update task
- `PATCH /api/tasks/{id}/toggle` - Toggle task completion
- `DELETE /api/tasks/{id}` - Delete task

## Testing

See http://localhost:8000/docs for interactive API testing.
