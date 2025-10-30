"""
Frame encoding utilities for live streaming

Handles conversion of numpy arrays to compressed image formats for streaming.
"""

import logging
from io import BytesIO
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class FrameEncoder:
    """
    Encodes video frames to compressed formats
    
    Optimized for real-time streaming with quality/size tradeoffs
    """
    
    def __init__(self, format: str = 'JPEG', quality: int = 85):
        """
        Initialize frame encoder
        
        Args:
            format: Image format ('JPEG' or 'PNG')
            quality: Compression quality (1-100, JPEG only)
        """
        self.format = format.upper()
        self.quality = quality
        
        if self.format not in ['JPEG', 'PNG']:
            logger.warning(f"⚠️  Unsupported format {format}, using JPEG")
            self.format = 'JPEG'
    
    def encode(self, frame: np.ndarray) -> Optional[bytes]:
        """
        Encode frame to compressed image bytes
        
        Args:
            frame: RGB numpy array (H, W, 3)
        
        Returns:
            Compressed image bytes or None on error
        """
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(frame)
            
            # Encode to bytes
            buffer = BytesIO()
            
            if self.format == 'JPEG':
                pil_image.save(buffer, format='JPEG', quality=self.quality, optimize=True)
            else:  # PNG
                pil_image.save(buffer, format='PNG', optimize=True)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.debug(f"⚠️  Frame encoding error: {e}")
            return None
    
    def update_quality(self, quality: int):
        """
        Update JPEG compression quality
        
        Args:
            quality: New quality (1-100)
        """
        self.quality = max(1, min(100, quality))
        logger.debug(f"🎨 Updated encoding quality: {self.quality}")
