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

## Auth

Endpoints:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

No primeiro start (tabela `users` vazia), o sistema cria o admin com:

```env
ADMIN_EMAIL=admin@rotahub.local
ADMIN_PASSWORD=Admin@123
```

Troque a senha em produção.

## Migrations

```bash
alembic upgrade head
```

No Render, use no **Build Command**:

```bash
pip install -r requirements.txt && alembic upgrade head
```

## JWT (Render)

```env
JWT_SECRET_KEY=uma-chave-longa-e-aleatoria
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ADMIN_EMAIL=seu@email.com
ADMIN_PASSWORD=SenhaForteAqui
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
