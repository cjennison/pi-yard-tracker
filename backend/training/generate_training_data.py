#!/usr/bin/env python3
"""
Synthetic Training Data Generator

Uses OpenAI DALL-E 3 to generate training images with specific objects (like deer)
and automatically creates YOLO-format annotations.

This solves the "I don't have 1000 deer photos" problem by generating synthetic data!

Usage:
    python backend/generate_training_data.py \
        --object "white-tailed deer" \
        --background "backyard with grass and trees" \
        --count 50

Educational Notes:
- DALL-E 3 generates realistic images based on text prompts
- We generate images with known object positions
- Since we control generation, we can create perfect annotations
- Mix synthetic data with real photos for best results
"""

import argparse
import os
import time
from pathlib import Path
from datetime import datetime
import logging
import json
from dotenv import load_dotenv

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available. Install: pip install openai")

# Image processing
try:
    from PIL import Image
    import requests
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL not available. Install: pip install pillow")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SyntheticDataGenerator:
    """Generates synthetic training images using OpenAI DALL-E 3"""
    
    def __init__(self, api_key=None):
        """
        Initialize generator
        
        Args:
            api_key: OpenAI API key (or reads from OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        if not PIL_AVAILABLE:
            raise ImportError("PIL library not installed. Run: pip install pillow")
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found! Set OPENAI_API_KEY in .env file or pass as parameter.\n"
                "Get your API key from: https://platform.openai.com/api-keys"
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info("✅ OpenAI client initialized")
    
    def generate_image(self, prompt, size="1024x1024", quality="standard", 
                      base_image_path=None):
        """
        Generate image using OpenAI image generation
        
        Two modes:
        1. Generate from scratch (base_image_path=None) - uses DALL-E 3
        2. Edit existing image (base_image_path provided) - uses Responses API with GPT Image
        
        Args:
            prompt: Text description of image to generate
            size: Image size (1024x1024, 1536x1024, 1024x1536)
            quality: 'standard' or 'hd' (DALL-E) / 'low', 'medium', 'high' (GPT Image)
            base_image_path: Optional path to base image to edit
        
        Returns:
            PIL Image object
        """
        if base_image_path:
            return self._edit_image_with_object(base_image_path, prompt, quality)
        else:
            return self._generate_from_scratch(prompt, size, quality)
    
    def _generate_from_scratch(self, prompt, size, quality):
        """Generate image from scratch using DALL-E 3"""
        logger.info(f"🎨 Generating image from scratch: {prompt[:50]}...")
        
        try:
            # Call DALL-E 3 API
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1  # DALL-E 3 only supports n=1
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download image
            image_response = requests.get(image_url)
            image = Image.open(BytesIO(image_response.content))
            
            logger.info(f"✅ Image generated successfully ({image.size})")
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Failed to generate image: {e}")
            return None
    
    def _edit_image_with_object(self, base_image_path, object_prompt, quality):
        """
        Edit existing image by adding an object
        
        IMPORTANT: OpenAI's image editing works differently than you might expect:
        - DALL-E 2 edit: Requires a MASK showing where to edit (we don't have one)
        - DALL-E 3: Doesn't support editing at all
        - GPT Image: Not yet available in stable API
        
        WORKAROUND: We'll use vision + generation approach:
        1. Send base image to GPT-4o with vision
        2. Ask it to describe the scene
        3. Generate new image with DALL-E 3 using that description + object
        
        Args:
            base_image_path: Path to your backyard photo
            object_prompt: What to add (e.g., "a white-tailed deer")
            quality: Image quality setting
        
        Returns:
            PIL Image with object in similar scene
        """
        logger.info(f"🖼️  Analyzing base image: {Path(base_image_path).name}")
        logger.info(f"➕ Will add: {object_prompt}")
        
        try:
            import base64
            
            # Read and encode base image
            with open(base_image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image format
            img_format = Path(base_image_path).suffix.lower()
            mime_type = f"image/{img_format[1:]}" if img_format in ['.jpg', '.jpeg', '.png', '.webp'] else "image/jpeg"
            
            # Step 1: Use GPT-4o Vision to describe the scene
            logger.info("🔍 Analyzing scene with GPT-4o Vision...")
            
            vision_prompt = (
                "Describe this scene in detail for image generation purposes. "
                "Focus on: lighting (time of day, shadows), environment (grass, trees, buildings, etc.), "
                "weather conditions, camera angle and perspective. "
                "Be specific and concise (2-3 sentences max)."
            )
            
            vision_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            
            scene_description = vision_response.choices[0].message.content.strip()
            logger.info(f"📝 Scene: {scene_description[:100]}...")
            
            # Step 2: Generate new image with DALL-E 3 using scene description + object
            generation_prompt = (
                f"A photorealistic image matching this scene: {scene_description}. "
                f"In this scene, add {object_prompt} that is clearly visible and centered, "
                f"taking up about 40-60% of the image. "
                f"The {object_prompt} should look natural and realistic in this environment. "
                f"Match the lighting, perspective, and style of the original scene exactly."
            )
            
            logger.info("🎨 Generating new image with DALL-E 3...")
            
            # Map quality parameter
            dalle_quality = 'hd' if quality == 'high' else 'standard'
            
            generated_image = self._generate_from_scratch(
                prompt=generation_prompt,
                size="1024x1024",
                quality=dalle_quality
            )
            
            if generated_image:
                logger.info("✅ Image generated with object in similar scene")
            
            return generated_image
            
        except Exception as e:
            logger.error(f"❌ Failed to edit image: {e}")
            logger.info("ℹ️  Falling back to simple generation...")
            
            # Fallback: Just generate from scratch
            fallback_prompt = f"A photorealistic image of {object_prompt} in a backyard, centered and clearly visible"
            return self._generate_from_scratch(fallback_prompt, "1024x1024", "standard")
    
    def auto_detect_bbox(self, image_path):
        """
        Use pre-trained YOLOv8n to automatically detect object position
        
        This solves the "assumed centered" problem by using AI to find where
        the deer actually is in the generated image!
        
        Args:
            image_path: Path to generated image
        
        Returns:
            (x_center, y_center, width, height) normalized 0-1, or None if not found
        """
        try:
            from ultralytics import YOLO
            
            # Load pre-trained model (reuse if already loaded)
            if not hasattr(self, '_detector_model'):
                logger.info("📦 Loading YOLOv8n for auto-annotation...")
                self._detector_model = YOLO('yolov8n.pt')
            
            # Run detection
            results = self._detector_model(image_path, verbose=False)
            
            # COCO classes that could be animals (we want the largest one)
            # 15=bird, 16=cat, 17=dog, 18=horse, 19=sheep, 20=cow
            # 21=elephant, 22=bear, 23=zebra, 24=giraffe
            animal_classes = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
            
            best_box = None
            best_area = 0
            
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Look for any animal-like detection
                    if cls in animal_classes and conf > 0.3:
                        # Get normalized coordinates
                        x1, y1, x2, y2 = box.xyxyn[0].tolist()
                        
                        # Calculate area
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        
                        # Keep the largest detection
                        if area > best_area:
                            best_area = area
                            x_center = (x1 + x2) / 2
                            y_center = (y1 + y2) / 2
                            best_box = (x_center, y_center, width, height)
                            logger.info(f"   🎯 Detected animal (class {cls}, conf {conf:.2f}, area {area:.2%})")
            
            if best_box:
                logger.info(f"   ✅ Auto-annotation: center=({best_box[0]:.2f}, {best_box[1]:.2f}), size=({best_box[2]:.2f}x{best_box[3]:.2f})")
                return best_box
            else:
                logger.warning("   ⚠️  No animal detected, using centered guess")
                return None
                
        except Exception as e:
            logger.error(f"   ❌ Auto-detection failed: {e}")
            return None
    
    def create_yolo_annotation(self, image_size, object_class, bbox_normalized=None):
        """
        Create YOLO-format annotation
        
        Args:
            image_size: (width, height) of image
            object_class: Class ID (0 for first class)
            bbox_normalized: (x_center, y_center, width, height) all 0-1
                           If None, assumes object is centered and takes up 60% of image
        
        Returns:
            YOLO annotation string
        """
        if bbox_normalized is None:
            # Default: centered object taking up 60% of image
            bbox_normalized = (0.5, 0.5, 0.6, 0.6)
        
        x_center, y_center, width, height = bbox_normalized
        
        # YOLO format: class_id x_center y_center width height (all normalized 0-1)
        annotation = f"{object_class} {x_center} {y_center} {width} {height}\n"
        
        return annotation
    
    def generate_training_sample(self, object_name, background_description=None, 
                                 class_id=0, output_dir="data/synthetic_training",
                                 base_image_path=None):
        """
        Generate one complete training sample (image + annotation)
        
        Two modes:
        1. Generate from scratch: Provide object_name + background_description
        2. Edit existing photo: Provide object_name + base_image_path
        
        Args:
            object_name: What to generate (e.g., "white-tailed deer")
            background_description: Scene description (only for generate mode)
            class_id: YOLO class ID
            output_dir: Where to save files
            base_image_path: Optional path to your actual backyard photo
        
        Returns:
            Tuple of (image_path, label_path) or (None, None) if failed
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if base_image_path:
            # Mode 2: Edit existing image
            logger.info(f"📸 Using base image: {Path(base_image_path).name}")
            prompt = object_name  # Simple object name for editing
            image = self.generate_image(
                prompt=prompt,
                base_image_path=base_image_path
            )
        else:
            # Mode 1: Generate from scratch
            if not background_description:
                background_description = "backyard with grass and trees"
            
            # Create detailed prompt for DALL-E
            prompt = (
                f"A high-quality photograph of a {object_name} in {background_description}. "
                f"The {object_name} is clearly visible, centered in the frame, "
                f"taking up about 60% of the image. Realistic photography style, "
                f"natural lighting, sharp focus on the {object_name}."
            )
            
            image = self.generate_image(prompt, size="1024x1024", quality="standard")
        
        if image is None:
            return None, None
        
        # Create unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        image_filename = f"synthetic_{object_name.replace(' ', '_')}_{timestamp}.jpg"
        label_filename = f"synthetic_{object_name.replace(' ', '_')}_{timestamp}.txt"
        
        image_path = output_dir / image_filename
        label_path = output_dir / label_filename
        
        # Save image
        image.save(image_path, "JPEG", quality=95)
        logger.info(f"💾 Saved image: {image_path.name}")
        
        # Create annotation using AUTO-DETECTION
        logger.info("🔍 Auto-detecting object position...")
        detected_bbox = self.auto_detect_bbox(image_path)
        
        if detected_bbox:
            # Use detected bounding box
            annotation = self.create_yolo_annotation(
                image_size=image.size,
                object_class=class_id,
                bbox_normalized=detected_bbox
            )
        else:
            # Fallback to centered guess
            logger.warning("   Using fallback centered annotation")
            annotation = self.create_yolo_annotation(
                image_size=image.size,
                object_class=class_id,
                bbox_normalized=(0.5, 0.5, 0.6, 0.6)  # Centered, 60% of image
            )
        
        # Save annotation
        with open(label_path, 'w') as f:
            f.write(annotation)
        logger.info(f"💾 Saved annotation: {label_path.name}")
        
        return image_path, label_path
    
    def generate_batch(self, object_name, background_description=None, count=10, 
                      class_id=0, delay=2.0, output_dir="data/synthetic_training",
                      base_image_path=None):
        """
        Generate multiple training samples
        
        Args:
            object_name: What to generate
            background_description: Scene description (None if using base_image)
            count: Number of images to generate
            class_id: YOLO class ID
            delay: Seconds to wait between API calls (rate limiting)
            output_dir: Where to save files
            base_image_path: Optional path to base image to edit
        
        Returns:
            List of (image_path, label_path) tuples
        """
        logger.info("=" * 60)
        logger.info(f"🚀 Generating {count} synthetic training samples")
        logger.info("=" * 60)
        logger.info(f"📝 Object: {object_name}")
        
        if base_image_path:
            logger.info(f"📸 Mode: EDIT existing image")
            logger.info(f"🖼️  Base image: {Path(base_image_path).name}")
        else:
            logger.info(f"� Mode: GENERATE from scratch")
            logger.info(f"�🏞️  Background: {background_description or 'default'}")
        
        logger.info(f"💾 Output: {output_dir}")
        logger.info("")
        
        results = []
        
        for i in range(count):
            logger.info(f"[{i+1}/{count}] Generating sample...")
            
            # For generation mode, add variation to background for diversity
            bg = None
            if not base_image_path and background_description:
                variations = [
                    background_description,
                    f"{background_description}, morning light",
                    f"{background_description}, afternoon sun",
                    f"{background_description}, overcast sky",
                    f"{background_description}, golden hour lighting",
                ]
                bg = variations[i % len(variations)]
            
            # Generate sample
            image_path, label_path = self.generate_training_sample(
                object_name=object_name,
                background_description=bg,
                class_id=class_id,
                output_dir=output_dir,
                base_image_path=base_image_path
            )
            
            if image_path and label_path:
                results.append((image_path, label_path))
                logger.info(f"✅ Sample {i+1} complete\n")
            else:
                logger.error(f"❌ Sample {i+1} failed\n")
            
            # Rate limiting delay (except for last iteration)
            if i < count - 1:
                logger.info(f"⏳ Waiting {delay}s before next generation...")
                time.sleep(delay)
        
        logger.info("=" * 60)
        logger.info(f"✅ Batch complete: {len(results)}/{count} successful")
        logger.info("=" * 60)
        
        return results

def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic training data using OpenAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MODE 1: Generate from scratch (DALL-E 3)
  python backend/generate_training_data.py \\
      --object "white-tailed deer" \\
      --background "New Hampshire backyard with grass and trees" \\
      --count 10

  # MODE 2: Edit your actual backyard photo (Recommended!)
  python backend/generate_training_data.py \\
      --object "white-tailed deer" \\
      --base-image data/photos/my_backyard.jpg \\
      --count 5

  # Generate turkey images
  python backend/generate_training_data.py \\
      --object "wild turkey" \\
      --background "forest clearing" \\
      --count 5

  # Test with single image
  python backend/generate_training_data.py \\
      --object "deer" \\
      --base-image data/photos/test.jpg \\
      --count 1

Note: Requires OPENAI_API_KEY in .env file
      Get API key from: https://platform.openai.com/api-keys
      
Costs (as of Oct 2025):
      - DALL-E 3 (from scratch): ~$0.04 per image
      - DALL-E 2 (edit mode): ~$0.02 per image
      - Using YOUR backyard photos is cheaper AND more realistic!
        """
    )
    
    parser.add_argument('--object', type=str, required=True,
                       help='Object to generate/add (e.g., "white-tailed deer")')
    parser.add_argument('--background', type=str, default=None,
                       help='Background scene (only for generate mode, optional)')
    parser.add_argument('--base-image', type=str, default=None,
                       help='Path to your backyard photo to edit (enables EDIT mode)')
    parser.add_argument('--count', type=int, default=1,
                       help='Number of images to generate (default: 1)')
    parser.add_argument('--class-id', type=int, default=0,
                       help='YOLO class ID (default: 0)')
    parser.add_argument('--output', type=str, default='data/synthetic_training',
                       help='Output directory (default: data/synthetic_training)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between API calls in seconds (default: 2.0)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.base_image and not Path(args.base_image).exists():
        logger.error(f"❌ Base image not found: {args.base_image}")
        exit(1)
    
    if args.base_image and args.background:
        logger.warning("⚠️  --background ignored when using --base-image")
    
    try:
        # Initialize generator
        generator = SyntheticDataGenerator()
        
        # Generate batch
        results = generator.generate_batch(
            object_name=args.object,
            background_description=args.background,
            count=args.count,
            class_id=args.class_id,
            delay=args.delay,
            output_dir=args.output,
            base_image_path=args.base_image
        )
        
        if results:
            logger.info("")
            logger.info("📁 Generated files:")
            for img_path, lbl_path in results:
                logger.info(f"   {img_path.name}")
                logger.info(f"   {lbl_path.name}")
            logger.info("")
            logger.info("🎯 Next steps:")
            logger.info("   1. Review generated images")
            logger.info("   2. Adjust bounding boxes if needed (using LabelImg)")
            logger.info("   3. Mix with real photos for best results")
            logger.info("   4. Use for training: python backend/train_custom_model.py")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
