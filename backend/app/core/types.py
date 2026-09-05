"""Кастомные типы колонок, общие для всех моделей проекта.

Пока здесь только один тип, но он завязан на важный момент архитектуры:
модели используют этот GUID вместо прямого postgresql.UUID, чтобы то же
самое приложение (и те же модели) можно было гонять в тестах на SQLite,
без поднятия реального Postgres под каждый pytest-run.
"""

import uuid

from sqlalchemy import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls, *, name: str):
    """Persist enum *values* (`owner`), not member names (`OWNER`).

    Alembic already created Postgres types with lowercase labels.
    Without values_callable SQLAlchemy sends OWNER/DRAFT and the insert
    dies with a 500 on a live database.
    """
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda members: [member.value for member in members],
    )


class GUID(TypeDecorator):
    """UUID-колонка, которая сама выбирает физическое представление.

    В Postgres хранится как нативный UUID (компактно, с нормальной
    индексацией). На любом другом диалекте (в проекте это SQLite для
    тестов) значение приходится хранить как CHAR(32) — hex-строка без
    дефисов, — потому что своего типа UUID там нет.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
