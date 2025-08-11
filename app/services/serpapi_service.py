import httpx
import json
import asyncio
import os
import re
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.utils.deduplication import filter_duplicates
from app.utils.performance import timed_async, run_in_threadpool

# Set up logging
logger = logging.getLogger(__name__)

# Use Redis cache in production, fallback to in-memory cache in development
if os.getenv("REDIS_ENABLED", "false").lower() == "true":
    from app.utils.redis_cache import redis_cache
    cache_decorator = redis_cache(ttl=3600)
else:
    from app.utils.performance import async_cache
    cache_decorator = async_cache(ttl=3600)

# Regular expressions for extracting price and brand from titles
PRICE_PATTERN = re.compile(r'(?:[\$£€¥]|USD|EUR|GBP|JPY)\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*(?:USD|EUR|GBP|JPY)')
BRAND_PATTERNS = [
    re.compile(r'^([\w\s]+?)\s+[-–|]'),  # Brand at the beginning followed by separator
    re.compile(r'by\s+([\w\s]+)', re.IGNORECASE),  # "by Brand"
    re.compile(r'from\s+([\w\s]+)', re.IGNORECASE),  # "from Brand"
]

def extract_price_from_title(title: str) -> Optional[str]:
    """Extract price from product title if present"""
    if not title:
        return None
    
    match = PRICE_PATTERN.search(title)
    if match:
        return match.group(0).strip()
    return None

def extract_brand_from_title(title: str) -> Optional[str]:
    """Extract brand from product title if present"""
    if not title:
        return None
    
    for pattern in BRAND_PATTERNS:
        match = pattern.search(title)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, try to get the first word if it's capitalized
    words = title.split()
    if words and words[0][0].isupper():
        return words[0]
    
    return None

@timed_async
@cache_decorator  # Cache results for 1 hour
async def search_similar_products(image_url: str) -> List[Dict[str, Any]]:
    """
    Search for similar products using SerpAPI's Google Reverse Image Search
    
    Args:
        image_url: URL of the image to search
        
    Returns:
        List of similar products with title, link, image, price, and brand
    """
    # Construct the SerpAPI URL
    api_url = "https://serpapi.com/search.json"
    
    # Set up the query parameters
    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": settings.SERPAPI_API_KEY
    }
    
    # Make the API request with timeout and retries
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                logger.info(f"Making SerpAPI request for image: {image_url}")
                response = await client.get(api_url, params=params)
                
                # Check if the request was successful
                if response.status_code != 200:
                    raise Exception(f"SerpAPI request failed with status code {response.status_code}: {response.text}")
                
                # Parse the response
                data = response.json()
                
                # Process the response to extract products
                products = await process_serpapi_response(data)
                
                # Log the number of products found
                logger.info(f"Found {len(products)} products from SerpAPI")
                
                return products
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # If this is the last attempt, raise the exception
                if attempt == 2:
                    logger.error(f"Failed to connect to SerpAPI after 3 attempts: {str(e)}")
                    raise
                
                # Otherwise, wait and retry
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(f"SerpAPI request failed, retrying in {wait_time} seconds: {str(e)}")
                await asyncio.sleep(wait_time)
                continue

async def process_serpapi_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process the SerpAPI response to extract product information
    
    Args:
        data: The JSON response from SerpAPI
        
    Returns:
        List of products with extracted information
    """
    products = []
    
    # Check if the response contains an error
    if "error" in data:
        logger.error(f"SerpAPI error: {data['error']}")
        return []
    
    # Process inline_images (main source of product data)
    if "inline_images" in data:
        for item in data.get("inline_images", []):
            product = {
                "title": item.get("title", ""),
                "link": item.get("source", item.get("link", "")),
                "image_url": item.get("original", item.get("thumbnail", "")),
                "price": extract_price_from_title(item.get("title", "")),
                "brand": extract_brand_from_title(item.get("title", "")),
                "source": "inline_images"
            }
            products.append(product)
    
    # Process image_results (secondary source)
    if "image_results" in data:
        for item in data.get("image_results", []):
            product = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "image_url": item.get("thumbnail", ""),
                "price": extract_price_from_title(item.get("title", "")),
                "brand": extract_brand_from_title(item.get("title", "")),
                "source": "image_results"
            }
            products.append(product)
    
    # Process shopping_results if available (most reliable for product data)
    if "shopping_results" in data:
        for item in data.get("shopping_results", []):
            product = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "image_url": item.get("thumbnail", ""),
                "price": item.get("price", extract_price_from_title(item.get("title", ""))),
                "brand": item.get("source", extract_brand_from_title(item.get("title", ""))),
                "source": "shopping_results"
            }
            products.append(product)
    
    # Filter out duplicates using a thread pool to avoid blocking the event loop
    unique_products = await run_in_threadpool(filter_duplicates, products)
    
    # Limit to the maximum number of similar products
    return unique_products[:settings.MAX_SIMILAR_PRODUCTS]

def extract_product_info(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant product information from SerpAPI response
    
    Args:
        product: Product data from SerpAPI
        
    Returns:
        Dictionary with extracted product information
    """
    return {
        "title": product.get("title", ""),
        "link": product.get("link", ""),
        "image_url": product.get("image_url", ""),
        "price": product.get("price", ""),
        "brand": product.get("brand", ""),
        "source": product.get("source", ""),
        "description": product.get("description", ""),
        "rating": product.get("rating", None),
        "reviews_count": product.get("reviews_count", None),
        "raw_data": json.dumps(product) if settings.STORE_RAW_DATA else None
    }