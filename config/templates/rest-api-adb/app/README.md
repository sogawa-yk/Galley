# {{app_name}}

REST API application built with FastAPI and Oracle Autonomous Database.

## Setup

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_DSN` | Yes | ADB connection string |
| `DATABASE_USER` | Yes | Database username |
| `DATABASE_PASSWORD` | Yes | Database password |
| `DATABASE_WALLET_DIR` | No | Path to wallet directory (default: `/app/wallet`) |
| `JWT_SECRET` | No | JWT secret for HS256 verification |
| `JWT_JWKS_URL` | No | JWKS URL for RS256 verification |

### Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port {{app_port}}
```

### Docker

```bash
docker build -t {{app_name}} .
docker run -p {{app_port}}:{{app_port}} \
  -e DATABASE_DSN="..." \
  -e DATABASE_USER="..." \
  -e DATABASE_PASSWORD="..." \
  {{app_name}}
```

## API Endpoints

- `GET /health` - Health check (includes DB connectivity)
- `GET /api/v1/items` - List items
- `GET /api/v1/items/{id}` - Get item by ID
- `POST /api/v1/items` - Create item (JSON body: `{"name": "...", "description": "..."}`)

## Project Structure

```
├── main.py           # FastAPI app entry point
├── src/
│   ├── auth.py       # JWT authentication (protected)
│   ├── db.py         # Database connection pool (protected)
│   └── routes.py     # API route definitions
├── Dockerfile        # Container build (protected)
└── requirements.txt  # Python dependencies
```

Files marked as "protected" are managed by Galley and should not be modified directly.
