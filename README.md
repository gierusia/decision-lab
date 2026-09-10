# Decision Lab

Локально: `docker compose up --build`, затем в контейнере бэка `python -m app.seed`.

Демо-вход после seed: админ из `backend/config_admin.yaml`; `member@example.com` и `viewer@example.com` с паролем `demo-pass-12`. Другой домен — `SEED_EMAIL_DOMAIN` в `.env` (на сервере то же самое).
