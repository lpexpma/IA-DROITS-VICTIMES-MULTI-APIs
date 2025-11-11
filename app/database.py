"""Database utilities for OLIVIA.

This module exposes a light abstraction on top of SQLAlchemy so both the
Streamlit application and the service layer can share a persistent cache of
search results.  The implementation deliberately stays simple: a local SQLite
database is used by default and a context-managed helper (`db.session()`) is
provided to manage transactions.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///olivia.db")


engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class RechercheCache(Base):
    """Cache des recherches effectuées par les utilisateurs."""

    __tablename__ = "recherches_cachees"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)
    situation = Column(Text, nullable=False)
    strategie = Column(String(64), nullable=True)
    resultats = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "query_hash", name="uq_user_query_hash"),)


def init_database() -> None:
    """Initialise la base de données en créant les tables si nécessaire."""

    Base.metadata.create_all(bind=engine)


@dataclass
class DatabaseManager:
    """Fin utilitaire pour gérer les sessions SQLAlchemy."""

    session_factory: sessionmaker

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Optional[Session] = None
        try:
            session = self.session_factory()
            yield session
            transaction = session.get_transaction()
            if transaction is not None and transaction.is_active:
                session.commit()
        except Exception:
            if session is not None:
                session.rollback()
            raise
        finally:
            if session is not None:
                session.close()


db = DatabaseManager(SessionLocal)


__all__ = ["Base", "RechercheCache", "db", "engine", "init_database"]

