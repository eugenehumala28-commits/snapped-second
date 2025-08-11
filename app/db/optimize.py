from sqlalchemy import create_engine, text
from app.core.config import settings

def optimize_database():
    """
    Optimize the SQLite database for better performance
    """
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
    
    with engine.connect() as conn:
        # Enable WAL mode for better concurrency
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        
        # Set synchronous mode to NORMAL for better performance
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        
        # Enable memory-mapped I/O for the database file
        conn.execute(text("PRAGMA mmap_size=30000000000;"))
        
        # Set cache size to 10000 pages (about 40MB)
        conn.execute(text("PRAGMA cache_size=10000;"))
        
        # Enable foreign key constraints
        conn.execute(text("PRAGMA foreign_keys=ON;"))
        
        # Analyze the database to optimize query planning
        conn.execute(text("ANALYZE;"))
        
        # Vacuum the database to reclaim space
        conn.execute(text("VACUUM;"))
    
    print("Database optimized successfully.")

if __name__ == "__main__":
    optimize_database()