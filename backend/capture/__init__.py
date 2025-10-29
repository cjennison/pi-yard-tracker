"""
Camera capture module for Pi Yard Tracker

Handles image capture from Raspberry Pi camera module.
"""

from .camera_capture import capture_images, cleanup_old_captures

__all__ = ['capture_images', 'cleanup_old_captures']
