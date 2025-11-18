# 🎨 Curated Asset Library

This directory contains high-quality, free (CC0 license) game assets organized for automatic matching to game designs.

## 📁 Directory Structure

```
curated/
├── characters/
│   ├── pixel_art/      # Pixel art characters (player, enemies, NPCs)
│   └── low_poly/       # Low-poly 3D characters
├── environments/
│   ├── platforms/      # Platform tiles and blocks
│   ├── backgrounds/    # Background images
│   └── obstacles/      # Obstacles and traps
├── items/
│   ├── collectibles/   # Coins, gems, powerups
│   └── powerups/       # Power-up items
├── ui/
│   ├── buttons/        # UI buttons
│   └── icons/          # UI icons
├── metadata/
│   └── index.json      # Asset database with metadata
└── download_assets.py   # Script to organize downloaded assets
```

## 📥 How to Download Assets

### Option 1: Kenney.nl (Recommended - CC0 License)

1. Visit: https://kenney.nl/assets
2. Download these packs (all free, CC0 license):
   - **Abstract Platformer** - Great for platformer games
   - **Micro Roguelike** - Characters and items
   - **Tiny Dungeon** - Fantasy/dungeon theme
   - **Tiny Swords** - Characters and weapons
   - **Roguelike** - Complete roguelike pack

3. Extract ZIP files to: `core/assets/curated/temp_downloads/`

4. Run the organization script:
   ```bash
   cd core/assets/curated
   python download_assets.py
   ```

### Option 2: OpenGameArt.org (CC0 Assets)

1. Visit: https://opengameart.org
2. Filter by:
   - License: CC0
   - Type: Sprites, Tilesets, Backgrounds
3. Download and place in `temp_downloads/`
4. Run `download_assets.py`

### Option 3: itch.io Free Assets

1. Visit: https://itch.io/game-assets/free
2. Download free asset packs
3. Extract to `temp_downloads/`
4. Run `download_assets.py`

## 🔧 How It Works

1. **Asset Organization**: The `download_assets.py` script automatically:
   - Categorizes assets by type (player, enemy, collectible, etc.)
   - Extracts metadata (size, colors, style)
   - Creates asset index JSON

2. **Asset Matching**: When generating a game:
   - System matches game design to assets by:
     - Art style (pixel_art, low_poly, etc.)
     - Theme (fantasy, sci-fi, etc.)
     - Genre (platformer, rpg, etc.)
     - Color scheme similarity

3. **Asset Usage**: Selected assets are copied to the game project

## 📊 Asset Index Format

Each asset in `metadata/index.json` contains:

```json
{
  "id": "player_001",
  "path": "characters/pixel_art/player_001.png",
  "category": "player",
  "style": "pixel_art",
  "themes": ["fantasy", "medieval"],
  "genres": ["platformer", "rpg"],
  "colors": {
    "primary": "#4A90E2",
    "secondary": "#50C878"
  },
  "size": [64, 64],
  "tags": ["knight", "warrior"],
  "license": "CC0"
}
```

## ✅ Quick Start

1. Download at least one asset pack (Kenney.nl recommended)
2. Extract to `temp_downloads/`
3. Run: `python download_assets.py`
4. Assets will be organized and indexed automatically

## 📝 License

All assets in this library are CC0 (Public Domain) or compatible licenses.
You can use them in any project without attribution (though attribution is appreciated).

## 🔄 Adding More Assets

Simply:
1. Download new asset packs
2. Place in `temp_downloads/`
3. Run `download_assets.py` again
4. New assets will be added to the index

