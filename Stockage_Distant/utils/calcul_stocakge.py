import os
import psutil
from pathlib import Path


def get_image_statistics(image_dir):
    """List all images and calculate statistics"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    images = []
    total_size = 0
    
    image_path = Path(image_dir)
    if not image_path.exists():
        print(f"Directory {image_dir} not found!")
        return None
    
    # Get all image files
    for file in sorted(image_path.iterdir()):
        if file.is_file() and file.suffix.lower() in image_extensions:
            size = file.stat().st_size
            total_size += size
            images.append({
                'name': file.name,
                'size': size,
                'size_mb': size / (1024**2)
            })
    
    if not images:
        print("No images found!")
        return None
    
    # Calculate statistics
    mean_size = total_size / len(images)
    mean_size_mb = mean_size / (1024**2)
    
    return {
        'images': images,
        'count': len(images),
        'total_size': total_size,
        'total_size_gb': total_size / (1024**3),
        'mean_size': mean_size,
        'mean_size_mb': mean_size_mb
    }


def estimate_remaining_capacity(stats):
    """Estimate how many images can fit in remaining storage"""
    if stats is None:
        return None
    
    disk = psutil.disk_usage(".")
    remaining_bytes = disk.free
    mean_size = stats['mean_size']
    
    estimated_images = int(remaining_bytes / mean_size)
    
    return {
        'remaining_bytes': remaining_bytes,
        'remaining_gb': remaining_bytes / (1024**3),
        'estimated_additional_images': estimated_images,
        'disk_usage_percent': disk.percent
    }


def main():
    # Get image directory relative to this script
    script_dir = Path(__file__).parent.parent
    image_dir = script_dir / "static" / "images"
    
    print("=" * 60)
    print("IMAGE STORAGE ANALYSIS")
    print("=" * 60)
    
    # Get image statistics
    stats = get_image_statistics(image_dir)
    
    if stats:
        print(f"\nImages found: {stats['count']}")
        print(f"Total size: {stats['total_size_gb']:.2f} GB")
        print(f"Mean size per image: {stats['mean_size_mb']:.2f} MB")
        print(f"\nImage list:")
        print("-" * 60)
        for img in stats['images']:
            print(f"  {img['name']:<40} {img['size_mb']:>8.2f} MB")
        
        # Estimate remaining capacity
        capacity = estimate_remaining_capacity(stats)
        if capacity:
            print("\n" + "=" * 60)
            print("STORAGE CAPACITY ESTIMATE")
            print("=" * 60)
            print(f"Remaining storage: {capacity['remaining_gb']:.2f} GB")
            print(f"Disk usage: {capacity['disk_usage_percent']:.1f}%")
            print(f"Estimated additional images: {capacity['estimated_additional_images']:,}")
            print("=" * 60)


if __name__ == "__main__":
    main()