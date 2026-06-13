"""
Database session wrapper. Exposes elements from core/database for compatibility.
"""
from app.core.database import engine, async_session_maker, get_db
