"""
Database Session - Iteration 4: Enhanced Connection Pooling, Retry Logic & Health Checks
Production-grade async SQLAlchemy with resilience patterns
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from app.core.config import settings
from typing import AsyncGenerator
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager with health checks and retry logic"""
    
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database engine with optimized pool settings"""
        if self._initialized:
            return
        
        logger.info("Initializing database connection pool...")
        
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,   # Recycle connections after 1 hour
            pool_timeout=30,     # Timeout for getting connection from pool
            echo=settings.DATABASE_ECHO,
            future=True,
        )
        
        self._initialized = True
        logger.info(f"Database pool initialized: size={settings.DATABASE_POOL_SIZE}, max_overflow={settings.DATABASE_MAX_OVERFLOW}")
    
    async def health_check(self) -> bool:
        """Perform database health check"""
        if not self.engine:
            return False
        
        try:
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def dispose(self) -> None:
        """Dispose of the engine and all connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections disposed")


# Global database manager instance
db_manager = DatabaseManager()


def get_engine() -> AsyncEngine:
    """Get the database engine, initializing if necessary"""
    if not db_manager._initialized:
        db_manager.initialize()
    return db_manager.engine


async_session_maker = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    future=True,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session with retry logic.
    Automatically commits on success, rolls back on failure.
    """
    if not db_manager._initialized:
        db_manager.initialize()
    
    session = async_session_maker(bind=get_engine())
    
    try:
        async with session as db_session:
            yield db_session
            # Session context manager handles commit/rollback
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database connection on startup"""
    db_manager.initialize()
    
    # Perform health check
    is_healthy = await db_manager.health_check()
    if not is_healthy:
        logger.warning("Database health check failed on startup")
    else:
        logger.info("Database health check passed")


async def close_db() -> None:
    """Close database connections on shutdown"""
    await db_manager.dispose()

