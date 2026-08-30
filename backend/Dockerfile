# ---- этап сборки: здесь есть компиляторы и dev-заголовки ----
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --user складывает пакеты в /root/.local — оттуда их потом заберёт
# финальный этап, без хвоста в виде gcc и dev-заголовков.
RUN pip install --no-cache-dir --user -r requirements.txt


# ---- финальный этап: то, что реально попадёт в образ ----
FROM python:3.12-slim

# libpq5 — рантайм-библиотека для psycopg2 (без -dev и без компилятора,
# они были нужны только на этапе сборки в builder).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# UID/GID вынесены в ARG, а не захардкожены — если у тебя на хосте твой
# пользователь не 1000 (проверить: id -u), можно собрать образ с
# --build-arg APP_UID=$(id -u) --build-arg APP_GID=$(id -g), и тогда
# при bind-mount'е ./backend:/app из docker-compose не будет Permission denied
# на файлы, которые процесс в контейнере пытается прочитать/создать.
ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid ${APP_GID} app \
    && useradd --uid ${APP_UID} --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app . .

ENV PATH=/home/app/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Без root'а внутри контейнера: если кто-то найдёт RCE-уязвимость в самом
# приложении или в одной из зависимостей, максимум, что он получит —
# права обычного пользователя внутри контейнера, а не root.
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
