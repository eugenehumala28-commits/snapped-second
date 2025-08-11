from typing import List, Dict, Any
import re
from difflib import SequenceMatcher

def filter_duplicates(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out duplicate products from search results
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Filtered list of products with duplicates removed
    """
    if not products:
        return []
    
    # Initialize list of unique products
    unique_products = []
    
    # Track seen titles and normalized titles for deduplication
    seen_titles = set()
    seen_normalized_titles = set()
    
    for product in products:
        title = product.get('title', '')
        
        if not title:
            continue
        
        # Skip exact duplicates
        if title in seen_titles:
            continue
        
        # Normalize title for fuzzy matching
        normalized_title = normalize_title(title)
        
        # Check for similar titles
        is_duplicate = False
        for seen_title in seen_normalized_titles:
            if is_similar_title(normalized_title, seen_title, threshold=0.85):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_products.append(product)
            seen_titles.add(title)
            seen_normalized_titles.add(normalized_title)
    
    return unique_products

def normalize_title(title: str) -> str:
    """
    Normalize a product title for comparison
    
    Args:
        title: The product title
        
    Returns:
        Normalized title
    """
    # Convert to lowercase
    normalized = title.lower()
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove common words that don't help with product identification
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
    normalized = ' '.join(word for word in normalized.split() if word not in stop_words)
    
    return normalized

def is_similar_title(title1: str, title2: str, threshold: float = 0.85) -> bool:
    """
    Check if two titles are similar using sequence matching
    
    Args:
        title1: First title
        title2: Second title
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if titles are similar, False otherwise
    """
    # Use SequenceMatcher to calculate similarity ratio
    similarity = SequenceMatcher(None, title1, title2).ratio()
    return similarity >= threshold