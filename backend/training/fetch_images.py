"""
Image Fetcher - Download Images from Free Stock Photo APIs

This tool fetches images from free stock photo services and saves them
to your to_annotate folder for quick annotation.

Supported sources:
- Pexels (no rate limits, high quality)
- Unsplash (50/hour, very high quality)
- Pixabay (no rate limits, decent quality)

Usage:
    # Fetch 20 coffee mug images from Pexels
    python backend/training/fetch_images.py --query "coffee mug" --count 20
    
    # Fetch from specific source
    python backend/training/fetch_images.py --query "coffee cup" --count 10 --source unsplash
    
    # Fetch and immediately open annotation tool
    python backend/training/fetch_images.py --query "coffee mug" --count 15 --annotate
"""

import argparse
import logging
import requests
from pathlib import Path
from typing import List, Dict
import time
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ImageFetcher:
    """Fetch images from free stock photo APIs"""
    
    def __init__(self, source: str = 'pexels'):
        """
        Initialize image fetcher
        
        Args:
            source: Image source ('pexels', 'unsplash', or 'pixabay')
        """
        self.source = source.lower()
        self.api_key = self._get_api_key()
        
        if not self.api_key:
            logger.warning(f"⚠️  No API key found for {source}. See setup instructions below.")
    
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        key_mapping = {
            'pexels': 'PEXELS_API_KEY',
            'unsplash': 'UNSPLASH_ACCESS_KEY',
            'pixabay': 'PIXABAY_API_KEY'
        }
        
        env_var = key_mapping.get(self.source, '')
        return os.getenv(env_var, '')
    
    def fetch_pexels(self, query: str, count: int) -> List[Dict]:
        """
        Fetch images from Pexels
        
        Args:
            query: Search query (e.g., "coffee mug")
            count: Number of images to fetch
            
        Returns:
            List of image data dictionaries
        """
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not found in .env file")
        
        headers = {'Authorization': self.api_key}
        images = []
        page = 1
        per_page = min(count, 80)  # Pexels max per page
        
        while len(images) < count:
            url = f'https://api.pexels.com/v1/search'
            params = {
                'query': query,
                'per_page': per_page,
                'page': page,
                'orientation': 'landscape'  # Better for object detection
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"❌ Pexels API error: {response.status_code}")
                break
            
            data = response.json()
            photos = data.get('photos', [])
            
            if not photos:
                logger.warning(f"⚠️  No more images found (got {len(images)} total)")
                break
            
            for photo in photos:
                if len(images) >= count:
                    break
                
                images.append({
                    'url': photo['src']['large'],  # Large size for better quality
                    'photographer': photo['photographer'],
                    'source': 'Pexels',
                    'id': photo['id']
                })
            
            page += 1
        
        return images
    
    def fetch_unsplash(self, query: str, count: int) -> List[Dict]:
        """
        Fetch images from Unsplash
        
        Args:
            query: Search query
            count: Number of images
            
        Returns:
            List of image data dictionaries
        """
        if not self.api_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not found in .env file")
        
        headers = {'Authorization': f'Client-ID {self.api_key}'}
        images = []
        page = 1
        per_page = min(count, 30)  # Unsplash max per page
        
        while len(images) < count:
            url = 'https://api.unsplash.com/search/photos'
            params = {
                'query': query,
                'per_page': per_page,
                'page': page,
                'orientation': 'landscape'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 403:
                logger.error("❌ Unsplash rate limit exceeded (50 requests/hour)")
                break
            elif response.status_code != 200:
                logger.error(f"❌ Unsplash API error: {response.status_code}")
                break
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                logger.warning(f"⚠️  No more images found (got {len(images)} total)")
                break
            
            for photo in results:
                if len(images) >= count:
                    break
                
                images.append({
                    'url': photo['urls']['regular'],  # Regular size ~1080px
                    'photographer': photo['user']['name'],
                    'source': 'Unsplash',
                    'id': photo['id']
                })
            
            page += 1
            time.sleep(0.1)  # Be nice to API
        
        return images
    
    def fetch_pixabay(self, query: str, count: int) -> List[Dict]:
        """
        Fetch images from Pixabay
        
        Args:
            query: Search query
            count: Number of images
            
        Returns:
            List of image data dictionaries
        """
        if not self.api_key:
            raise ValueError("PIXABAY_API_KEY not found in .env file")
        
        images = []
        page = 1
        per_page = min(count, 200)  # Pixabay max per page
        
        while len(images) < count:
            url = 'https://pixabay.com/api/'
            params = {
                'key': self.api_key,
                'q': query,
                'per_page': per_page,
                'page': page,
                'image_type': 'photo',
                'orientation': 'horizontal'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"❌ Pixabay API error: {response.status_code}")
                break
            
            data = response.json()
            hits = data.get('hits', [])
            
            if not hits:
                logger.warning(f"⚠️  No more images found (got {len(images)} total)")
                break
            
            for hit in hits:
                if len(images) >= count:
                    break
                
                images.append({
                    'url': hit['largeImageURL'],
                    'photographer': hit['user'],
                    'source': 'Pixabay',
                    'id': hit['id']
                })
            
            page += 1
        
        return images
    
    def fetch_images(self, query: str, count: int) -> List[Dict]:
        """
        Fetch images from configured source
        
        Args:
            query: Search query
            count: Number of images to fetch
            
        Returns:
            List of image data dictionaries
        """
        logger.info(f"🔍 Searching {self.source.title()} for: {query}")
        
        if self.source == 'pexels':
            return self.fetch_pexels(query, count)
        elif self.source == 'unsplash':
            return self.fetch_unsplash(query, count)
        elif self.source == 'pixabay':
            return self.fetch_pixabay(query, count)
        else:
            raise ValueError(f"Unknown source: {self.source}")
    
    def download_images(self, images: List[Dict], output_dir: Path, query: str) -> int:
        """
        Download images to directory
        
        Args:
            images: List of image data from fetch_images()
            output_dir: Output directory path
            query: Search query (for filename generation)
            
        Returns:
            Number of successfully downloaded images
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        
        for i, image in enumerate(images, 1):
            try:
                logger.info(f"📥 Downloading {i}/{len(images)}: {image['id']} from {image['source']}")
                
                response = requests.get(image['url'], timeout=30)
                
                if response.status_code == 200:
                    # Generate filename
                    filename = f"{self.source}_{query.replace(' ', '_')}_{image['id']}.jpg"
                    filepath = output_dir / filename
                    
                    # Save image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded += 1
                    logger.info(f"✅ Saved: {filename}")
                else:
                    logger.warning(f"⚠️  Failed to download image {image['id']}: HTTP {response.status_code}")
                
                # Be nice to servers
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error downloading {image['id']}: {e}")
        
        return downloaded


def print_setup_instructions():
    """Print setup instructions for API keys"""
    print("\n" + "=" * 70)
    print("📋 API KEY SETUP INSTRUCTIONS")
    print("=" * 70)
    print("\nTo use this tool, you need a FREE API key from one of these services:\n")
    
    print("1️⃣  PEXELS (Recommended - No Rate Limits)")
    print("   • Sign up: https://www.pexels.com/api/")
    print("   • Get your API key")
    print("   • Add to .env file: PEXELS_API_KEY=your_key_here")
    print()
    
    print("2️⃣  UNSPLASH (High Quality - 50 requests/hour)")
    print("   • Sign up: https://unsplash.com/developers")
    print("   • Create an app to get Access Key")
    print("   • Add to .env file: UNSPLASH_ACCESS_KEY=your_key_here")
    print()
    
    print("3️⃣  PIXABAY (No Rate Limits)")
    print("   • Sign up: https://pixabay.com/api/docs/")
    print("   • Get your API key")
    print("   • Add to .env file: PIXABAY_API_KEY=your_key_here")
    print()
    
    print("EXAMPLE .env FILE:")
    print("-" * 70)
    print("# Image Fetching APIs (choose one or all)")
    print("PEXELS_API_KEY=your_pexels_key_here")
    print("UNSPLASH_ACCESS_KEY=your_unsplash_key_here")
    print("PIXABAY_API_KEY=your_pixabay_key_here")
    print()
    print("# OpenAI (for synthetic data generation)")
    print("OPENAI_API_KEY=sk-...")
    print("-" * 70)
    print("\n💡 All services offer FREE tiers with generous limits!\n")
    print("=" * 70)
    print()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fetch images from free stock photo APIs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch 20 coffee mug images from Pexels
  python backend/training/fetch_images.py --query "coffee mug" --count 20
  
  # Fetch from Unsplash
  python backend/training/fetch_images.py --query "coffee cup" --count 10 --source unsplash
  
  # Fetch and immediately open annotation tool
  python backend/training/fetch_images.py --query "white coffee mug" --count 15 --annotate
  
  # Show API setup instructions
  python backend/training/fetch_images.py --setup

Recommended queries for coffee mugs:
  - "coffee mug"
  - "coffee cup"
  - "ceramic mug"
  - "white mug"
  - "coffee mug white background"
  - "mug isolated"
        """
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Search query (e.g., "coffee mug")'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of images to fetch (default: 10)'
    )
    
    parser.add_argument(
        '--source',
        type=str,
        choices=['pexels', 'unsplash', 'pixabay'],
        default='pexels',
        help='Image source (default: pexels)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/to_annotate',
        help='Output directory (default: data/to_annotate)'
    )
    
    parser.add_argument(
        '--annotate',
        action='store_true',
        help='Automatically open annotation tool after fetching'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Show API key setup instructions'
    )
    
    args = parser.parse_args()
    
    # Show setup instructions
    if args.setup:
        print_setup_instructions()
        return
    
    # Require query if not showing setup
    if not args.query:
        parser.error("--query is required (or use --setup for instructions)")
    
    # Create fetcher
    try:
        fetcher = ImageFetcher(source=args.source)
        
        # Fetch images
        logger.info("=" * 60)
        logger.info(f"🚀 Fetching {args.count} images from {args.source.title()}")
        logger.info("=" * 60)
        
        images = fetcher.fetch_images(args.query, args.count)
        
        if not images:
            logger.error("❌ No images found. Try a different query.")
            return
        
        logger.info(f"✅ Found {len(images)} images")
        
        # Download images
        logger.info("")
        logger.info("📥 Downloading images...")
        downloaded = fetcher.download_images(images, args.output, args.query)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✅ Downloaded {downloaded}/{len(images)} images to: {args.output}")
        logger.info("=" * 60)
        
        if downloaded > 0:
            logger.info("")
            logger.info("🎯 Next steps:")
            logger.info(f"   1. Review images in: {args.output}")
            logger.info(f"   2. Run annotation tool: python backend/training/annotation_tool.py")
            logger.info(f"   3. Annotate bounding boxes")
            logger.info(f"   4. Click 'Add to Training Set' to copy to synthetic_training/")
            
            # Optionally open annotation tool
            if args.annotate:
                logger.info("")
                logger.info("🚀 Opening annotation tool...")
                import subprocess
                subprocess.run(['python', 'backend/training/annotation_tool.py'])
        
    except ValueError as e:
        logger.error(f"❌ {e}")
        logger.info("")
        logger.info("💡 Run with --setup flag to see API key setup instructions:")
        logger.info("   python backend/training/fetch_images.py --setup")
    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
