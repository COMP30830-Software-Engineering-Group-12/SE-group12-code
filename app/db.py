# app/db.py

import os
from flask import g, current_app
from sqlalchemy import create_engine

def _make_engine():
    """
    Create a SQLAlchemy engine using DATABASE_URL.
    Example:
      mysql+pymysql://root:password@127.0.0.1:3306/bike_database
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var not set")

    # echo=True to print SQL queries in console
    echo = current_app.config.get("SQL_ECHO", False)
    return create_engine(db_url, echo=echo, pool_pre_ping=True)

def get_db():
    """
    Store the engine on flask.g
    """
    engine = getattr(g, "_db_engine", None)
    if engine is None:
        engine = g._db_engine = _make_engine()
    return engine
