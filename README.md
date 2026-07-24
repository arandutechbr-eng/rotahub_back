# rotahub_back

API do **RotaHub** — Gestão Inteligente de Rotas e Logística.

## Stack

- Python 3.13
- FastAPI
- Pydantic v2

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Segurança

Nunca commite `.env` ou credenciais. Use apenas `.env.example` como modelo.
