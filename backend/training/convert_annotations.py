"""
Convert YOLO annotations from one class ID to another

This script batch-converts all .txt annotation files in specified directories,
replacing a source class ID with a target class ID while preserving bounding box coordinates.

Usage:
    python backend/training/convert_annotations.py --from-class 80 --to-class 0
    python backend/training/convert_annotations.py --from-class 80 --to-class 0 --dry-run
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnnotationConverter:
    """Converts YOLO annotation files from one class ID to another"""

    def __init__(self, from_class: int, to_class: int, dry_run: bool = False):
        """
        Initialize converter

        Args:
            from_class: Source class ID to convert from
            to_class: Target class ID to convert to
            dry_run: If True, only report what would be changed without modifying files
        """
        self.from_class = from_class
        self.to_class = to_class
        self.dry_run = dry_run
        self.files_processed = 0
        self.lines_converted = 0

    def convert_line(self, line: str) -> Tuple[str, bool]:
        """
        Convert a single annotation line

        Args:
            line: YOLO annotation line (e.g., "80 0.5 0.5 0.3 0.4")

        Returns:
            Tuple of (converted_line, was_converted)
        """
        parts = line.strip().split()
        if not parts:
            return line, False

        try:
            class_id = int(parts[0])
            if class_id == self.from_class:
                # Replace class ID while preserving coordinates
                parts[0] = str(self.to_class)
                return ' '.join(parts) + '\n', True
            return line, False
        except (ValueError, IndexError):
            logger.warning(f"⚠️  Skipping malformed line: {line.strip()}")
            return line, False

    def convert_file(self, annotation_path: Path) -> int:
        """
        Convert all annotations in a single file

        Args:
            annotation_path: Path to .txt annotation file

        Returns:
            Number of lines converted in this file
        """
        if not annotation_path.exists():
            logger.warning(f"⚠️  File not found: {annotation_path}")
            return 0

        try:
            with open(annotation_path, 'r') as f:
                lines = f.readlines()

            converted_lines = []
            file_conversions = 0

            for line in lines:
                converted_line, was_converted = self.convert_line(line)
                converted_lines.append(converted_line)
                if was_converted:
                    file_conversions += 1

            if file_conversions > 0:
                if self.dry_run:
                    logger.info(f"🔍 [DRY RUN] Would convert {file_conversions} lines in: {annotation_path.name}")
                else:
                    with open(annotation_path, 'w') as f:
                        f.writelines(converted_lines)
                    logger.info(f"✅ Converted {file_conversions} lines in: {annotation_path.name}")

            return file_conversions

        except Exception as e:
            logger.error(f"❌ Failed to convert {annotation_path}: {e}")
            return 0

    def convert_directory(self, directory: Path) -> int:
        """
        Convert all .txt files in a directory

        Args:
            directory: Directory containing annotation files

        Returns:
            Total number of lines converted
        """
        if not directory.exists():
            logger.warning(f"⚠️  Directory not found: {directory}")
            return 0

        annotation_files = list(directory.glob('*.txt'))
        if not annotation_files:
            logger.info(f"📂 No .txt files found in: {directory}")
            return 0

        logger.info(f"📂 Processing {len(annotation_files)} files in: {directory}")
        total_conversions = 0

        for annotation_path in annotation_files:
            conversions = self.convert_file(annotation_path)
            total_conversions += conversions

        return total_conversions

    def convert_all(self, base_dirs: List[Path]) -> None:
        """
        Convert annotations in all specified directories

        Args:
            base_dirs: List of base directories to search for annotations
        """
        logger.info(f"🔄 Converting class {self.from_class} → {self.to_class}")
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No files will be modified")

        for base_dir in base_dirs:
            if not base_dir.exists():
                logger.warning(f"⚠️  Base directory not found: {base_dir}")
                continue

            logger.info(f"\n{'='*60}")
            logger.info(f"Processing base directory: {base_dir}")
            logger.info(f"{'='*60}")

            # Process base directory itself
            conversions = self.convert_directory(base_dir)
            if conversions > 0:
                self.lines_converted += conversions
                self.files_processed += len(list(base_dir.glob('*.txt')))

            # Process subdirectories recursively
            for subdir in base_dir.rglob('*'):
                if subdir.is_dir():
                    conversions = self.convert_directory(subdir)
                    if conversions > 0:
                        self.lines_converted += conversions
                        self.files_processed += len(list(subdir.glob('*.txt')))

        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        if self.dry_run:
            logger.info(f"🔍 [DRY RUN] Would convert {self.lines_converted} total lines")
        else:
            logger.info(f"✅ Converted {self.lines_converted} total lines")
        logger.info(f"{'='*60}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Convert YOLO annotation class IDs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert class 80 to class 0 (actual conversion)
  python backend/training/convert_annotations.py --from-class 80 --to-class 0

  # Preview what would be changed (dry run)
  python backend/training/convert_annotations.py --from-class 80 --to-class 0 --dry-run

  # Custom directories
  python backend/training/convert_annotations.py --from-class 80 --to-class 0 --dirs data/my_annotations
        """
    )

    parser.add_argument(
        '--from-class',
        type=int,
        required=True,
        help='Source class ID to convert from (e.g., 80)'
    )

    parser.add_argument(
        '--to-class',
        type=int,
        required=True,
        help='Target class ID to convert to (e.g., 0)'
    )

    parser.add_argument(
        '--dirs',
        type=str,
        nargs='+',
        default=['data/synthetic_training', 'data/training_data/labels'],
        help='Directories to search for annotation files (default: synthetic_training and training_data/labels)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    args = parser.parse_args()

    # Convert directory paths to Path objects
    base_dirs = [Path(d) for d in args.dirs]

    # Create converter and run
    converter = AnnotationConverter(
        from_class=args.from_class,
        to_class=args.to_class,
        dry_run=args.dry_run
    )

    converter.convert_all(base_dirs)

    logger.info("\n✅ Conversion complete!")
    if converter.dry_run:
        logger.info("💡 Remove --dry-run flag to actually modify files")


if __name__ == "__main__":
    main()
