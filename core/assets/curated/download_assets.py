"""
Script to download and organize curated game assets
Downloads free CC0 assets from Kenney.nl and organizes them
"""

import os
import zipfile
import httpx
import json
from pathlib import Path
from PIL import Image
import io

# Base directory for curated assets
BASE_DIR = Path(__file__).parent

# Kenney.nl asset packs (CC0 license, free to use)
KENNEY_PACKS = {
    "abstract_platformer": {
        "url": "https://kenney.nl/assets/abstract-platformer",
        "description": "Abstract platformer pack with characters, platforms, and items",
        "style": "pixel_art",
        "themes": ["abstract", "minimal"],
        "genres": ["platformer"]
    },
    "micro_roguelike": {
        "url": "https://kenney.nl/assets/micro-roguelike",
        "description": "Micro roguelike pack with characters and items",
        "style": "pixel_art",
        "themes": ["fantasy", "medieval"],
        "genres": ["roguelike", "rpg"]
    },
    "tiny_dungeon": {
        "url": "https://kenney.nl/assets/tiny-dungeon",
        "description": "Tiny dungeon pack with characters and environments",
        "style": "pixel_art",
        "themes": ["fantasy", "dungeon"],
        "genres": ["rpg", "adventure"]
    }
}

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL"""
    try:
        print(f"Downloading: {url}")
        with httpx.stream("GET", url, timeout=30.0) as response:
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                print(f"[OK] Downloaded: {output_path.name}")
                return True
            else:
                print(f"[ERROR] Failed to download: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] Error downloading {url}: {e}")
        return False

def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract ZIP file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[OK] Extracted: {zip_path.name}")
        return True
    except Exception as e:
        print(f"[ERROR] Error extracting {zip_path}: {e}")
        return False

def organize_assets(source_dir: Path, target_dir: Path):
    """Organize assets into proper categories"""
    asset_index = []
    
    # Walk through extracted files
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                source_path = Path(root) / file
                
                # Determine category based on filename/path
                file_lower = file.lower()
                path_lower = str(source_path).lower()
                
                # Categorize
                if any(word in file_lower for word in ['player', 'character', 'hero', 'knight', 'warrior']):
                    category = "player"
                    dest_dir = target_dir / "characters" / "pixel_art"
                elif any(word in file_lower for word in ['enemy', 'monster', 'goblin', 'skeleton', 'zombie']):
                    category = "enemy"
                    dest_dir = target_dir / "characters" / "pixel_art"
                elif any(word in file_lower for word in ['coin', 'gem', 'collectible', 'item', 'pickup']):
                    category = "collectible"
                    dest_dir = target_dir / "items" / "collectibles"
                elif any(word in file_lower for word in ['platform', 'ground', 'tile', 'block']):
                    category = "platform"
                    dest_dir = target_dir / "environments" / "platforms"
                elif any(word in file_lower for word in ['background', 'bg', 'sky', 'cloud']):
                    category = "background"
                    dest_dir = target_dir / "environments" / "backgrounds"
                elif any(word in file_lower for word in ['obstacle', 'spike', 'trap']):
                    category = "obstacle"
                    dest_dir = target_dir / "environments" / "obstacles"
                else:
                    # Default to items
                    category = "item"
                    dest_dir = target_dir / "items" / "collectibles"
                
                # Create destination directory
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file with unique name
                dest_path = dest_dir / file
                if dest_path.exists():
                    # Add number suffix if file exists
                    base_name = dest_path.stem
                    counter = 1
                    while dest_path.exists():
                        dest_path = dest_dir / f"{base_name}_{counter}{dest_path.suffix}"
                        counter += 1
                
                # Read and analyze image
                try:
                    with Image.open(source_path) as img:
                        img.save(dest_path, "PNG")
                        width, height = img.size
                        
                        # Extract dominant colors (simplified)
                        colors = extract_dominant_colors(img)
                        
                        # Add to index
                        asset_index.append({
                            "id": f"{category}_{len(asset_index)}",
                            "path": str(dest_path.relative_to(target_dir)).replace("\\", "/"),
                            "category": category,
                            "style": "pixel_art",
                            "themes": ["generic"],
                            "genres": ["platformer", "rpg"],
                            "colors": {
                                "primary": colors[0] if colors else "#4A90E2",
                                "secondary": colors[1] if len(colors) > 1 else "#50C878"
                            },
                            "size": [width, height],
                            "tags": [category, "pixel_art"],
                            "license": "CC0"
                        })
                except Exception as e:
                    print(f"[WARNING] Skipped {file}: {e}")
    
    return asset_index

def extract_dominant_colors(img: Image.Image, num_colors: int = 2) -> list:
    """Extract dominant colors from image (simplified)"""
    try:
        # Resize for faster processing
        img_small = img.resize((64, 64))
        colors = img_small.getcolors(maxcolors=256*256*256)
        
        if colors:
            # Sort by frequency and get top colors
            colors_sorted = sorted(colors, key=lambda x: x[0], reverse=True)
            dominant = []
            for count, color in colors_sorted[:num_colors]:
                if isinstance(color, tuple) and len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    dominant.append(hex_color)
            return dominant
    except:
        pass
    return []

def create_asset_index(asset_index: list, output_path: Path):
    """Create asset index JSON file"""
    index_data = {
        "version": "1.0",
        "total_assets": len(asset_index),
        "generated_at": str(Path(__file__).stat().st_mtime),
        "assets": asset_index
    }
    
    with open(output_path, "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"[OK] Created asset index: {output_path} ({len(asset_index)} assets)")

def main():
    """Main function to download and organize assets"""
    import sys
    import io
    # Fix Windows console encoding for emojis
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("Curated Asset Library Setup")
    print("=" * 50)
    
    # Create temp directory for downloads
    temp_dir = BASE_DIR / "temp_downloads"
    temp_dir.mkdir(exist_ok=True)
    
    # For now, we'll create a manual download guide since Kenney.nl requires manual download
    # But we'll create the index structure and organize any assets you place in temp_downloads
    
    print("\nAsset Download Instructions:")
    print("=" * 50)
    print("1. Visit https://kenney.nl/assets")
    print("2. Download these packs (all free, CC0 license):")
    print("   - Abstract Platformer")
    print("   - Micro Roguelike")
    print("   - Tiny Dungeon")
    print("3. Extract ZIP files to: core/assets/curated/temp_downloads/")
    print("4. Run this script again to organize them")
    print("\nAlternatively, place any PNG/JPG assets in temp_downloads/ and run this script.")
    
    # Check if temp_downloads has files
    if (temp_dir).exists() and any(temp_dir.iterdir()):
        print("\nOrganizing assets...")
        all_assets = []
        
        # Organize from temp_downloads
        for item in temp_dir.iterdir():
            if item.is_dir():
                assets = organize_assets(item, BASE_DIR)
                all_assets.extend(assets)
            elif item.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                # Single file - organize it
                assets = organize_assets(temp_dir, BASE_DIR)
                all_assets.extend(assets)
                break
        
        if all_assets:
            # Create index
            index_path = BASE_DIR / "metadata" / "index.json"
            create_asset_index(all_assets, index_path)
            print(f"\n[OK] Organized {len(all_assets)} assets!")
        else:
            print("\n[WARNING] No assets found in temp_downloads/")
    else:
        print("\n[INFO] Tip: After downloading assets, place them in temp_downloads/ and run this script again.")
        # Create empty index
        index_path = BASE_DIR / "metadata" / "index.json"
        create_asset_index([], index_path)

if __name__ == "__main__":
    main()

