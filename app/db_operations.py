"""Database operations."""
from typing import List, Optional, Dict
from app.models import get_db_session, Item, init_db
from sqlalchemy.exc import SQLAlchemyError


def check_db_connection() -> dict:
    """Check database connection status."""
    session = get_db_session()
    if not session:
        return {
            "status": "disconnected",
            "message": "Database not configured"
        }
    
    try:
        # Try to execute a simple query
        session.execute("SELECT 1")
        session.close()
        return {
            "status": "connected",
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }


def create_item(name: str, description: Optional[str] = None) -> dict:
    """Create a new item in the database."""
    session = get_db_session()
    if not session:
        raise Exception("Database not configured")
    
    try:
        # Initialize database if needed
        init_db()
        
        item = Item(name=name, description=description)
        session.add(item)
        session.commit()
        session.refresh(item)
        
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "created_at": item.created_at.isoformat()
        }
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Error creating item: {str(e)}")
    finally:
        session.close()


def get_items(limit: int = 100, offset: int = 0) -> List[dict]:
    """Get items from database."""
    session = get_db_session()
    if not session:
        return []
    
    try:
        items = session.query(Item).offset(offset).limit(limit).all()
        return [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]
    except SQLAlchemyError as e:
        raise Exception(f"Error fetching items: {str(e)}")
    finally:
        session.close()


def get_item(item_id: int) -> Optional[dict]:
    """Get a single item by ID."""
    session = get_db_session()
    if not session:
        return None
    
    try:
        item = session.query(Item).filter(Item.id == item_id).first()
        if item:
            return {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "created_at": item.created_at.isoformat()
            }
        return None
    except SQLAlchemyError as e:
        raise Exception(f"Error fetching item: {str(e)}")
    finally:
        session.close()

