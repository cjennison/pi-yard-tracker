"""
Speed Annotation Tool - Fast GUI for Manual Bounding Box Annotation

Features:
- Load images one by one
- View existing annotations (if any)
- Click anywhere to create initial bounding box
- Drag to move box
- Drag corners/edges to resize box
- Dropdown to select class
- Auto-save on navigation
- Keyboard shortcuts for speed

Keyboard Shortcuts:
- Left/Right Arrow: Previous/Next image
- Delete/Backspace: Delete current box
- Space: Toggle box visibility
- N: New box at center
- S: Save current annotation
"""

import argparse
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageTk, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BoundingBox:
    """Represents a YOLO bounding box"""
    
    def __init__(self, class_id: int, x_center: float, y_center: float, width: float, height: float):
        """
        Initialize bounding box (YOLO normalized format)
        
        Args:
            class_id: Class ID
            x_center: Normalized x center (0.0-1.0)
            y_center: Normalized y center (0.0-1.0)
            width: Normalized width (0.0-1.0)
            height: Normalized height (0.0-1.0)
        """
        self.class_id = class_id
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
    
    def to_pixel_coords(self, img_width: int, img_height: int) -> Tuple[int, int, int, int]:
        """
        Convert to pixel coordinates (x1, y1, x2, y2)
        
        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
            
        Returns:
            Tuple of (x1, y1, x2, y2)
        """
        x1 = int((self.x_center - self.width / 2) * img_width)
        y1 = int((self.y_center - self.height / 2) * img_height)
        x2 = int((self.x_center + self.width / 2) * img_width)
        y2 = int((self.y_center + self.height / 2) * img_height)
        return (x1, y1, x2, y2)
    
    @classmethod
    def from_pixel_coords(cls, class_id: int, x1: int, y1: int, x2: int, y2: int, 
                          img_width: int, img_height: int) -> 'BoundingBox':
        """
        Create from pixel coordinates
        
        Args:
            class_id: Class ID
            x1, y1, x2, y2: Pixel coordinates
            img_width: Image width
            img_height: Image height
            
        Returns:
            BoundingBox instance
        """
        x_center = ((x1 + x2) / 2) / img_width
        y_center = ((y1 + y2) / 2) / img_height
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height
        return cls(class_id, x_center, y_center, width, height)
    
    def to_yolo_string(self) -> str:
        """Convert to YOLO format string"""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"


class AnnotationTool:
    """Speed annotation GUI"""
    
    def __init__(self, input_dir: Path, class_names: List[str], class_ids: Optional[List[int]] = None):
        """
        Initialize annotation tool
        
        Args:
            input_dir: Directory containing images to annotate
            class_names: List of class names (for display)
            class_ids: List of class IDs (for YOLO). If None, uses indices 0, 1, 2...
        """
        self.input_dir = Path(input_dir)
        self.class_names = class_names
        
        # Map class names to IDs
        if class_ids is None:
            self.class_ids = list(range(len(class_names)))
        else:
            if len(class_ids) != len(class_names):
                raise ValueError("class_ids and class_names must have same length")
            self.class_ids = class_ids
        
        self.class_name_to_id = {name: id for name, id in zip(class_names, self.class_ids)}
        self.class_id_to_name = {id: name for name, id in zip(class_names, self.class_ids)}
        
        self.images = self._find_images()
        self.current_index = 0
        self.current_box: Optional[BoundingBox] = None
        self.selected_class_id = self.class_ids[0] if self.class_ids else 0
        
        # Canvas state
        self.canvas_rect = None
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.resize_handle = None
        self.creating_box = False  # Track if we're creating a new box
        
        # Image state
        self.original_image = None
        self.display_image = None
        self.photo_image = None
        self.img_width = 0
        self.img_height = 0
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Speed Annotation Tool")
        self.root.geometry("1200x800")
        self._create_widgets()
        self._bind_shortcuts()
        
        # Load first image
        if self.images:
            self.load_image(0)
        else:
            messagebox.showwarning("No Images", f"No images found in {input_dir}")
            self.root.quit()
    
    def _find_images(self) -> List[Path]:
        """Find all images in directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        images = set()  # Use set to avoid duplicates
        
        for ext in image_extensions:
            images.update(self.input_dir.glob(f'*{ext}'))
            images.update(self.input_dir.glob(f'*{ext.upper()}'))
        
        return sorted(list(images))
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Top control panel
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Class dropdown
        ttk.Label(control_frame, text="Class:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        self.class_var = tk.StringVar(value=self.class_names[0] if self.class_names else "")
        class_dropdown = ttk.Combobox(
            control_frame, 
            textvariable=self.class_var, 
            values=self.class_names,
            state='readonly',
            width=20,
            font=('Arial', 12)
        )
        class_dropdown.pack(side=tk.LEFT, padx=5)
        class_dropdown.bind('<<ComboboxSelected>>', self._on_class_changed)
        
        # Image counter
        self.counter_label = ttk.Label(control_frame, text="", font=('Arial', 12))
        self.counter_label.pack(side=tk.LEFT, padx=20)
        
        # Navigation buttons
        ttk.Button(control_frame, text="⬅️ Previous (←)", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Next ➡️ (→)", command=self.next_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Box (Del)", command=self.delete_box).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Save (S)", command=self.save_annotation).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Workflow buttons
        ttk.Button(control_frame, text="📦 Add to Training Set", command=self.add_to_training_set, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🧹 Clear Folder", command=self.clear_folder).pack(side=tk.LEFT, padx=5)
        
        # Canvas for image display
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray25', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Canvas bindings
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        
        # Status bar
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Delete>', lambda e: self.delete_box())
        self.root.bind('<BackSpace>', lambda e: self.delete_box())
        self.root.bind('s', lambda e: self.save_annotation())
        self.root.bind('S', lambda e: self.save_annotation())
        self.root.bind('n', lambda e: self._create_box_at_center())
        self.root.bind('N', lambda e: self._create_box_at_center())
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_label.config(text=message)
        logger.info(message)
    
    def _update_counter(self):
        """Update image counter"""
        if self.images:
            self.counter_label.config(
                text=f"Image {self.current_index + 1} / {len(self.images)}"
            )
    
    def _on_class_changed(self, event):
        """Handle class dropdown change"""
        selected_name = self.class_var.get()
        self.selected_class_id = self.class_name_to_id[selected_name]
        if self.current_box:
            self.current_box.class_id = self.selected_class_id
            self._update_status(f"Changed class to: {selected_name} (ID {self.selected_class_id})")
    
    def load_image(self, index: int):
        """Load image and its annotation"""
        if not (0 <= index < len(self.images)):
            return
        
        self.current_index = index
        image_path = self.images[index]
        
        # Load image
        self.original_image = Image.open(image_path)
        self.img_width, self.img_height = self.original_image.size
        
        # Force canvas to update its size
        self.canvas.update_idletasks()
        
        # Resize to fit canvas (with padding)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        padding = 20  # Padding around image
        max_width = canvas_width - padding * 2
        max_height = canvas_height - padding * 2
        
        if max_width > 100 and max_height > 100:  # Canvas is initialized
            scale = min(max_width / self.img_width, max_height / self.img_height, 1.0)
            new_width = int(self.img_width * scale)
            new_height = int(self.img_height * scale)
            self.display_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Fallback: resize to reasonable default
            self.display_image = self.original_image.copy()
            scale = min(800 / self.img_width, 600 / self.img_height, 1.0)
            new_width = int(self.img_width * scale)
            new_height = int(self.img_height * scale)
            self.display_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.photo_image = ImageTk.PhotoImage(self.display_image)
        
        # Display image
        self.canvas.delete('all')
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor=tk.CENTER,
            tags='image'
        )
        
        # Load annotation
        self._load_annotation(image_path)
        
        # Update UI
        self._update_counter()
        self._update_status(f"Loaded: {image_path.name}")
    
    def _load_annotation(self, image_path: Path):
        """Load existing annotation for image"""
        annotation_path = image_path.with_suffix('.txt')
        
        if not annotation_path.exists():
            self.current_box = None
            self.canvas_rect = None
            return
        
        # Read first annotation (we only support one box for now)
        try:
            with open(annotation_path, 'r') as f:
                lines = f.readlines()
            
            if lines:
                parts = lines[0].strip().split()
                if len(parts) == 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    self.current_box = BoundingBox(class_id, x_center, y_center, width, height)
                    
                    # Update class dropdown
                    if class_id in self.class_id_to_name:
                        self.class_var.set(self.class_id_to_name[class_id])
                        self.selected_class_id = class_id
                    else:
                        # Class ID not in our list - map to first defined class
                        logger.warning(f"Loaded annotation with class {class_id}, not in defined classes. Mapping to {self.class_names[0]} (ID {self.class_ids[0]})")
                        self.class_var.set(self.class_names[0])
                        self.selected_class_id = self.class_ids[0]
                        # Update the box to use the new class ID
                        self.current_box.class_id = self.selected_class_id
                    
                    # Draw box on canvas
                    self._draw_box()
        except Exception as e:
            logger.warning(f"Failed to load annotation: {e}")
            self.current_box = None
    
    def _draw_box(self):
        """Draw bounding box on canvas"""
        if not self.current_box:
            return
        
        # Convert to pixel coordinates
        x1, y1, x2, y2 = self.current_box.to_pixel_coords(self.img_width, self.img_height)
        
        # Scale to display size
        scale = self.display_image.width / self.img_width
        x1 = int(x1 * scale) + (self.canvas.winfo_width() - self.display_image.width) // 2
        y1 = int(y1 * scale) + (self.canvas.winfo_height() - self.display_image.height) // 2
        x2 = int(x2 * scale) + (self.canvas.winfo_width() - self.display_image.width) // 2
        y2 = int(y2 * scale) + (self.canvas.winfo_height() - self.display_image.height) // 2
        
        # Delete old rectangle
        if self.canvas_rect:
            self.canvas.delete(self.canvas_rect)
        
        # Draw new rectangle
        self.canvas_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline='lime',
            width=3,
            tags='bbox'
        )
    
    def _on_canvas_click(self, event):
        """Handle canvas click"""
        # Check if clicking on existing box
        if self.canvas_rect:
            bbox = self.canvas.bbox(self.canvas_rect)
            if bbox:
                x1, y1, x2, y2 = bbox
                # Check if click is on box edges (resize) or inside (move)
                margin = 15  # Larger margin for easier grabbing
                on_left = abs(event.x - x1) < margin and y1 - margin <= event.y <= y2 + margin
                on_right = abs(event.x - x2) < margin and y1 - margin <= event.y <= y2 + margin
                on_top = abs(event.y - y1) < margin and x1 - margin <= event.x <= x2 + margin
                on_bottom = abs(event.y - y2) < margin and x1 - margin <= event.x <= x2 + margin
                
                if on_left or on_right or on_top or on_bottom:
                    # Resize mode
                    self.resize_handle = {'left': on_left, 'right': on_right, 'top': on_top, 'bottom': on_bottom}
                    self.drag_data = {"item": self.canvas_rect, "x": event.x, "y": event.y, "resize": True}
                    # Change cursor to indicate resize
                    if on_left and on_top:
                        self.canvas.config(cursor="top_left_corner")
                    elif on_right and on_top:
                        self.canvas.config(cursor="top_right_corner")
                    elif on_left and on_bottom:
                        self.canvas.config(cursor="bottom_left_corner")
                    elif on_right and on_bottom:
                        self.canvas.config(cursor="bottom_right_corner")
                    elif on_left or on_right:
                        self.canvas.config(cursor="sb_h_double_arrow")
                    elif on_top or on_bottom:
                        self.canvas.config(cursor="sb_v_double_arrow")
                elif x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    # Inside box - move
                    self.drag_data = {"item": self.canvas_rect, "x": event.x, "y": event.y, "resize": False}
                    self.canvas.config(cursor="fleur")
                else:
                    # Outside box - start creating new box
                    self._start_box_creation(event.x, event.y)
        else:
            # No box exists - start creating new box
            self._start_box_creation(event.x, event.y)
    
    def _start_box_creation(self, x: int, y: int):
        """Start creating a new box at click position"""
        # Delete existing box if any
        if self.canvas_rect:
            self.canvas.delete(self.canvas_rect)
            self.canvas_rect = None
        
        # Mark that we're creating a new box
        self.creating_box = True
        
        # Store start position
        self.drag_data = {"x": x, "y": y, "creating": True}
        
        # Create initial rectangle (single point)
        self.canvas_rect = self.canvas.create_rectangle(
            x, y, x, y,
            outline='lime',
            width=3,
            tags='bbox'
        )
        self.canvas.config(cursor="crosshair")
    
    def _create_box_at_click(self, x: int, y: int):
        """Create new bounding box at click position (old behavior - creates fixed size box)"""
        # Default box size (100x100 pixels)
        box_size = 100
        x1 = x - box_size // 2
        y1 = y - box_size // 2
        x2 = x + box_size // 2
        y2 = y + box_size // 2
        
        # Convert to image coordinates
        self._create_box_from_canvas_coords(x1, y1, x2, y2)
    
    def _create_box_at_center(self):
        """Create box at image center"""
        center_x = self.canvas.winfo_width() // 2
        center_y = self.canvas.winfo_height() // 2
        self._create_box_at_click(center_x, center_y)
    
    def _create_box_from_canvas_coords(self, x1: int, y1: int, x2: int, y2: int):
        """Create bounding box from canvas coordinates"""
        # Convert canvas coords to image coords
        scale = self.display_image.width / self.img_width
        offset_x = (self.canvas.winfo_width() - self.display_image.width) // 2
        offset_y = (self.canvas.winfo_height() - self.display_image.height) // 2
        
        img_x1 = int((x1 - offset_x) / scale)
        img_y1 = int((y1 - offset_y) / scale)
        img_x2 = int((x2 - offset_x) / scale)
        img_y2 = int((y2 - offset_y) / scale)
        
        # Clamp to image bounds
        img_x1 = max(0, min(img_x1, self.img_width))
        img_y1 = max(0, min(img_y1, self.img_height))
        img_x2 = max(0, min(img_x2, self.img_width))
        img_y2 = max(0, min(img_y2, self.img_height))
        
        # Create bounding box
        self.current_box = BoundingBox.from_pixel_coords(
            self.selected_class_id,
            img_x1, img_y1, img_x2, img_y2,
            self.img_width, self.img_height
        )
        
        self._draw_box()
        self._update_status("Created new bounding box")
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        # Check if we're creating a new box
        if self.drag_data.get("creating"):
            # Update rectangle to current mouse position
            start_x = self.drag_data["x"]
            start_y = self.drag_data["y"]
            
            # Draw from top-left (start) to bottom-right (current)
            self.canvas.coords(self.canvas_rect, start_x, start_y, event.x, event.y)
            return
        
        if not self.drag_data["item"]:
            return
        
        if self.drag_data.get("resize"):
            # Resize box - get current bbox
            bbox = self.canvas.bbox(self.canvas_rect)
            if bbox:
                x1, y1, x2, y2 = bbox
                
                # Store original opposite edges (only on first drag movement)
                if "orig_bbox" not in self.drag_data:
                    self.drag_data["orig_bbox"] = (x1, y1, x2, y2)
                
                orig_x1, orig_y1, orig_x2, orig_y2 = self.drag_data["orig_bbox"]
                
                # Start with original coordinates
                new_x1, new_y1, new_x2, new_y2 = orig_x1, orig_y1, orig_x2, orig_y2
                
                # Modify only the edges/corners being dragged
                if self.resize_handle.get('left'):
                    new_x1 = event.x
                else:
                    new_x1 = orig_x1
                    
                if self.resize_handle.get('right'):
                    new_x2 = event.x
                else:
                    new_x2 = orig_x2
                    
                if self.resize_handle.get('top'):
                    new_y1 = event.y
                else:
                    new_y1 = orig_y1
                    
                if self.resize_handle.get('bottom'):
                    new_y2 = event.y
                else:
                    new_y2 = orig_y2
                
                # Ensure x1 < x2 and y1 < y2
                if new_x1 > new_x2:
                    new_x1, new_x2 = new_x2, new_x1
                if new_y1 > new_y2:
                    new_y1, new_y2 = new_y2, new_y1
                
                # Ensure minimum size
                if new_x2 - new_x1 >= 20 and new_y2 - new_y1 >= 20:
                    self.canvas.coords(self.canvas_rect, new_x1, new_y1, new_x2, new_y2)
        else:
            # Move box - use delta
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.move(self.canvas_rect, dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
    
    def _on_canvas_release(self, event):
        """Handle mouse release - update bounding box"""
        # If we were creating a new box, finalize it
        if self.drag_data.get("creating"):
            self.creating_box = False
            bbox = self.canvas.bbox(self.canvas_rect)
            if bbox:
                x1, y1, x2, y2 = bbox
                
                # Ensure x1 < x2 and y1 < y2
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                
                # Check minimum size (at least 10x10 pixels)
                if x2 - x1 >= 10 and y2 - y1 >= 10:
                    # Create the bounding box from the drawn rectangle
                    self._update_box_from_canvas_coords(x1, y1, x2, y2)
                    self._update_status("Created new bounding box")
                else:
                    # Too small - delete it
                    self.canvas.delete(self.canvas_rect)
                    self.canvas_rect = None
                    self.current_box = None
                    self._update_status("Box too small - cancelled")
            
            self.canvas.config(cursor="")
            self.drag_data = {"item": None, "x": 0, "y": 0}
            return
        
        # Only update the underlying box coordinates if we were dragging
        if self.canvas_rect and self.drag_data.get("item"):
            bbox = self.canvas.bbox(self.canvas_rect)
            if bbox:
                # Update the underlying BoundingBox without redrawing
                self._update_box_from_canvas_coords(*bbox)
        
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.resize_handle = None
        self.canvas.config(cursor="")  # Reset cursor
    
    def _update_box_from_canvas_coords(self, x1: int, y1: int, x2: int, y2: int):
        """Update current bounding box from canvas coordinates WITHOUT redrawing"""
        # Convert canvas coords to image coords
        scale = self.display_image.width / self.img_width
        offset_x = (self.canvas.winfo_width() - self.display_image.width) // 2
        offset_y = (self.canvas.winfo_height() - self.display_image.height) // 2
        
        img_x1 = int((x1 - offset_x) / scale)
        img_y1 = int((y1 - offset_y) / scale)
        img_x2 = int((x2 - offset_x) / scale)
        img_y2 = int((y2 - offset_y) / scale)
        
        # Clamp to image bounds
        img_x1 = max(0, min(img_x1, self.img_width))
        img_y1 = max(0, min(img_y1, self.img_height))
        img_x2 = max(0, min(img_x2, self.img_width))
        img_y2 = max(0, min(img_y2, self.img_height))
        
        # Update bounding box (don't create new, just update existing)
        self.current_box = BoundingBox.from_pixel_coords(
            self.selected_class_id,
            img_x1, img_y1, img_x2, img_y2,
            self.img_width, self.img_height
        )
        # Don't call _draw_box() here - the canvas rect is already in the right position!
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize - redraw image"""
        if self.original_image and event.width > 100 and event.height > 100:
            # Reload current image to fit new canvas size
            self.load_image(self.current_index)
    
    def save_annotation(self):
        """Save current annotation to file"""
        if not self.images:
            return
        
        image_path = self.images[self.current_index]
        annotation_path = image_path.with_suffix('.txt')
        
        try:
            if self.current_box:
                with open(annotation_path, 'w') as f:
                    f.write(self.current_box.to_yolo_string())
                self._update_status(f"✅ Saved annotation: {annotation_path.name}")
                
                # Create visualization
                self._save_visualization(image_path, annotation_path)
            else:
                # No box - create empty file or delete existing
                if annotation_path.exists():
                    annotation_path.unlink()
                self._update_status(f"⚠️  No box to save (deleted annotation if existed)")
        except Exception as e:
            logger.error(f"Failed to save annotation: {e}")
            messagebox.showerror("Save Error", f"Failed to save annotation: {e}")
    
    def _save_visualization(self, image_path: Path, annotation_path: Path):
        """Save a visualization of the annotation"""
        try:
            # Create annotation_check directory next to to_annotate
            viz_dir = self.input_dir.parent / 'annotation_check'
            viz_dir.mkdir(parents=True, exist_ok=True)
            
            # Load original image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            img_width, img_height = image.size
            
            # Parse annotation
            with open(annotation_path, 'r') as f:
                line = f.readline().strip()
            
            if line:
                parts = line.split()
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Convert to pixel coordinates
                x_center_px = x_center * img_width
                y_center_px = y_center * img_height
                width_px = width * img_width
                height_px = height * img_height
                
                x1 = int(x_center_px - width_px / 2)
                y1 = int(y_center_px - height_px / 2)
                x2 = int(x_center_px + width_px / 2)
                y2 = int(y_center_px + height_px / 2)
                
                # Get class name
                class_name = self.class_id_to_name.get(class_id, f"class_{class_id}")
                
                # Draw green box
                color = (0, 255, 0)  # Green
                for i in range(3):
                    draw.rectangle([x1 + i, y1 + i, x2 - i, y2 - i], outline=color)
                
                # Draw label
                label = f"{class_name} (ID:{class_id})"
                
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                label_y = y1 - text_height - 4 if y1 - text_height - 4 > 0 else y1
                draw.rectangle(
                    [x1, label_y, x1 + text_width + 4, label_y + text_height + 4],
                    fill=color
                )
                draw.text((x1 + 2, label_y + 2), label, fill=(255, 255, 255), font=font)
                
                # Save visualization
                viz_path = viz_dir / f"annotated_{image_path.name}"
                image.save(viz_path, "JPEG", quality=95)
                logger.info(f"📸 Saved visualization: {viz_path}")
        
        except Exception as e:
            logger.warning(f"Failed to save visualization: {e}")
    
    def delete_box(self):
        """Delete current bounding box"""
        if self.canvas_rect:
            self.canvas.delete(self.canvas_rect)
        self.canvas_rect = None
        self.current_box = None
        self._update_status("Deleted bounding box")
    
    def prev_image(self):
        """Load previous image"""
        self.save_annotation()  # Auto-save current
        if self.current_index > 0:
            self.load_image(self.current_index - 1)
    
    def next_image(self):
        """Load next image"""
        self.save_annotation()  # Auto-save current
        if self.current_index < len(self.images) - 1:
            self.load_image(self.current_index + 1)
    
    def add_to_training_set(self):
        """Copy all annotated images to synthetic_training folder"""
        # Get destination folder
        dest_dir = self.input_dir.parent / 'synthetic_training'
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Count annotated images
        annotated_images = []
        for image_path in self.images:
            annotation_path = image_path.with_suffix('.txt')
            if annotation_path.exists() and annotation_path.stat().st_size > 0:
                annotated_images.append(image_path)
        
        if not annotated_images:
            messagebox.showwarning("No Annotations", "No annotated images found to add to training set.")
            return
        
        # Confirm action
        result = messagebox.askyesno(
            "Add to Training Set",
            f"Copy {len(annotated_images)} annotated image(s) and their annotations to:\n{dest_dir}\n\nExisting files will be overwritten.\n\nContinue?"
        )
        
        if not result:
            return
        
        # Copy files
        copied_count = 0
        import shutil
        
        try:
            for image_path in annotated_images:
                annotation_path = image_path.with_suffix('.txt')
                
                # Copy image (overwrite if exists)
                dest_image = dest_dir / image_path.name
                shutil.copy2(str(image_path), str(dest_image))
                
                # Copy annotation (overwrite if exists)
                dest_annotation = dest_dir / annotation_path.name
                shutil.copy2(str(annotation_path), str(dest_annotation))
                
                copied_count += 1
                logger.info(f"✅ Copied {image_path.name} and annotation to training set")
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"Successfully copied {copied_count} image(s) to training set:\n{dest_dir}\n\nYou can now run prepare_dataset.py to organize them for training."
            )
            
            self._update_status(f"Added {copied_count} image(s) to training set")
        
        except Exception as e:
            logger.error(f"Failed to copy files: {e}")
            messagebox.showerror("Error", f"Failed to copy files to training set:\n{e}")
    
    def clear_folder(self):
        """Clear all images and annotations from the to_annotate folder"""
        if not self.images:
            messagebox.showinfo("Empty", "Folder is already empty.")
            return
        
        # Count total files (images + annotations)
        total_files = len(self.images)
        annotation_count = sum(1 for img in self.images if img.with_suffix('.txt').exists())
        
        # Confirm action
        result = messagebox.askyesno(
            "Clear Folder - Confirm",
            f"⚠️ WARNING ⚠️\n\nThis will DELETE:\n- {total_files} image(s)\n- {annotation_count} annotation(s)\n\nfrom: {self.input_dir}\n\nThis action CANNOT be undone!\n\nAre you sure?",
            icon='warning'
        )
        
        if not result:
            return
        
        # Double confirmation
        result2 = messagebox.askyesno(
            "Final Confirmation",
            "This is your last chance!\n\nReally delete all files?",
            icon='warning'
        )
        
        if not result2:
            return
        
        # Delete files
        deleted_images = 0
        deleted_annotations = 0
        
        try:
            for image_path in self.images:
                # Delete image
                if image_path.exists():
                    image_path.unlink()
                    deleted_images += 1
                
                # Delete annotation
                annotation_path = image_path.with_suffix('.txt')
                if annotation_path.exists():
                    annotation_path.unlink()
                    deleted_annotations += 1
            
            logger.info(f"🗑️ Deleted {deleted_images} images and {deleted_annotations} annotations")
            
            # Show success message
            messagebox.showinfo(
                "Folder Cleared",
                f"Successfully deleted:\n- {deleted_images} image(s)\n- {deleted_annotations} annotation(s)\n\nFolder is now empty."
            )
            
            # Reload image list (should be empty now)
            self.images = self._find_images()
            self.current_index = 0
            self.current_box = None
            self.canvas_rect = None
            self.canvas.delete('all')
            self._update_status("Folder cleared")
        
        except Exception as e:
            logger.error(f"Failed to clear folder: {e}")
            messagebox.showerror("Error", f"Failed to clear folder:\n{e}")
    
    def run(self):
        """Start GUI main loop"""
        self.root.mainloop()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Speed annotation tool for YOLO bounding boxes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Keyboard Shortcuts:
  Left/Right Arrow  : Navigate between images
  Delete/Backspace  : Delete current box
  N                 : Create new box at center
  S                 : Save current annotation

Mouse Controls:
  Click             : Create new box at click position
  Drag inside box   : Move box
  Drag edge/corner  : Resize box

Examples:
  # Annotate images in default folder (coffee_mug = class 0)
  python backend/training/annotation_tool.py
  
  # Annotate coffee_mug as class 0 explicitly (single-class model)
  python backend/training/annotation_tool.py --class-ids 0
  
  # Annotate with multiple classes (for multi-class models)
  python backend/training/annotation_tool.py --classes coffee_mug cup bowl --class-ids 0 1 2
  
  # Specify input directory
  python backend/training/annotation_tool.py --input data/my_images
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='data/to_annotate',
        help='Input directory containing images (default: data/to_annotate)'
    )
    
    parser.add_argument(
        '--classes',
        type=str,
        nargs='+',
        default=['coffee_mug'],
        help='Class names (default: coffee_mug)'
    )
    
    parser.add_argument(
        '--class-ids',
        type=int,
        nargs='+',
        default=None,
        help='Class IDs corresponding to class names (default: 0, 1, 2...). Example: --class-ids 0 for single-class coffee_mug model'
    )
    
    args = parser.parse_args()
    
    # Create and run annotation tool
    tool = AnnotationTool(
        input_dir=args.input,
        class_names=args.classes,
        class_ids=args.class_ids
    )
    tool.run()


if __name__ == "__main__":
    main()
