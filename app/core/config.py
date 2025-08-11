from pydantic_settings import BaseSettings
from typing import Optional, List, Set
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Snapped AI"
    
    # SerpAPI settings
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    MAX_SIMILAR_PRODUCTS: int = int(os.getenv("MAX_SIMILAR_PRODUCTS", "30"))
    STORE_RAW_DATA: bool = os.getenv("STORE_RAW_DATA", "false").lower() == "true"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Redis settings
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Upload settings
    UPLOAD_FOLDER: str = "app/static/uploads"
    STATIC_FOLDER: str = "app/static"
    ALLOWED_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
    
    # Cloudinary settings
    USE_CLOUDINARY: bool = os.getenv("USE_CLOUDINARY", "false").lower() == "true"
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    SAVE_LOCAL_COPY: bool = os.getenv("SAVE_LOCAL_COPY", "true").lower() == "true"
    REQUIRE_CLOUDINARY: bool = os.getenv("REQUIRE_CLOUDINARY", "false").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "12000"))
    
    # Performance settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    THREAD_POOL_SIZE: int = int(os.getenv("THREAD_POOL_SIZE", "4"))

settings = Settings()