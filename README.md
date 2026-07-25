# rotahub_back

API do **RotaHub** — Gestão Inteligente de Rotas e Logística.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- Supabase PostgreSQL

## Arquitetura

```
app/
├── api/            # Interface HTTP (rotas, sem regra de negócio)
├── core/           # Config, engine do banco, exceções
├── dependencies/   # Injeção de dependência (sessão, paginação)
├── models/         # Entidades SQLAlchemy
├── repositories/   # Acesso a dados (Repository Pattern)
├── schemas/        # Contratos Pydantic
├── services/       # Regras de negócio (Service Layer)
└── utils/
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Preencha o `DATABASE_URL` no `.env` com a connection string do Supabase
(**Project Settings → Database → Connection string → URI**), trocando o prefixo
`postgresql://` por `postgresql+psycopg://`:

```env
DATABASE_URL=postgresql+psycopg://postgres.xxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

Senhas com caracteres especiais (`@`, `#`, `%`) precisam ser URL-encoded.

## Migrations

```bash
alembic revision --autogenerate -m "descricao"
alembic upgrade head
alembic downgrade -1
```

## Executar

```bash
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

O health check retorna o status do banco (`ok`, `error` ou `not_configured`).

## Segurança

Nunca commite `.env` ou credenciais. Use apenas `.env.example` como modelo.
