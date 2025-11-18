"""
Example Test Script - Enhanced Godot Integration
Demonstrates how to use the new Godot integration system
"""

import asyncio
import json
from pathlib import Path
from services.godot_service import GodotService
from services.storage import StorageService
from config.settings import Settings


async def test_godot_integration():
    """
    Complete example of generating a game from AI content
    """
    
    print("🎮 Testing Enhanced Godot Integration\n")
    
    # Initialize services
    settings = Settings()
    
    # Initialize storage (Supabase)
    storage = StorageService(
        supabase_url=settings.supabase_url if hasattr(settings, 'supabase_url') else None,
        supabase_key=settings.supabase_key if hasattr(settings, 'supabase_key') else None,
        bucket="gamoraai-projects"
    )
    await storage.connect()
    
    # Initialize Godot service
    godot = GodotService(
        godot_path=settings.godot_path,
        projects_dir=settings.projects_dir
    )
    await godot.start()
    
    # Example AI-generated content
    # In production, this comes from ChatGPT-4 + DeepSeek
    ai_content = {
        "game_design": {
            "title": "Pixel Runner",
            "description": "A fast-paced platformer where you run, jump, and collect coins!",
            "genre": "platformer",
            "art_style": "pixel art",
            "color_scheme": {
                "primary": "#4A90E2",
                "secondary": "#50C878"
            },
            "player_description": "A blue ninja character",
            "enemy_description": "Red robots that patrol platforms",
            "environment_description": "Colorful forest with floating platforms",
            "win_condition": "Collect all coins and reach the flag",
            "lose_condition": "Health reaches zero or fall off screen"
        },
        
        "game_mechanics": {
            "player_movement": {
                "speed": 350.0,
                "jump_force": -450.0,
                "acceleration": 1800.0,
                "friction": 1400.0
            },
            "player_abilities": ["jump", "double_jump", "dash"],
            "enemy_behaviors": ["patrol", "chase_on_sight"],
            "collectibles": ["coin", "gem", "health_potion"],
            "power_ups": ["speed_boost", "invincibility"],
            "obstacles": ["spikes", "moving_platforms", "falling_platforms"],
            "game_rules": [
                "Collect all coins to unlock the exit",
                "Avoid enemies or lose health",
                "Collect power-ups for special abilities",
                "Health depletes when hit by enemies"
            ],
            "scoring_system": {
                "coin": 10,
                "gem": 50,
                "enemy_defeated": 100,
                "time_bonus": "1 point per second remaining"
            },
            "progression": {
                "difficulty_scaling": "More enemies and faster movement per level",
                "level_count": 3
            }
        },
        
        "level_design": {
            "levels": [
                {
                    "name": "Level 1 - Forest Start",
                    "difficulty": "easy",
                    "platforms": [
                        {"position": [100, 550], "size": [300, 50]},
                        {"position": [450, 500], "size": [200, 50]},
                        {"position": [700, 450], "size": [250, 50]},
                        {"position": [1000, 400], "size": [200, 50]},
                        {"position": [200, 350], "size": [150, 50]}
                    ],
                    "enemies": [
                        {"position": [500, 450], "type": "patrol", "patrol_range": 200},
                        {"position": [850, 400], "type": "patrol", "patrol_range": 150}
                    ],
                    "collectibles": [
                        {"position": [250, 500], "type": "coin"},
                        {"position": [550, 450], "type": "coin"},
                        {"position": [800, 400], "type": "coin"},
                        {"position": [1100, 350], "type": "gem"},
                        {"position": [300, 300], "type": "health_potion"}
                    ],
                    "obstacles": [
                        {"position": [600, 480], "type": "spikes", "size": [50, 20]}
                    ]
                }
            ]
        },
        
        "ui_design": {
            "menu_style": "modern",
            "font_size": 24,
            "button_style": "rounded",
            "color_theme": {
                "background": "#1a1a2e",
                "primary": "#4A90E2",
                "secondary": "#50C878",
                "text": "#ffffff"
            },
            "hud_elements": [
                {"type": "score", "position": "top-left"},
                {"type": "health", "position": "top-left"},
                {"type": "timer", "position": "top-right"}
            ]
        },
        
        "assets": [
            # In production, these would be DALL-E generated images
            # For this example, procedural sprites will be generated
        ],
        
        "scripts": {
            # Custom AI-generated scripts can go here
            # The GDScriptGenerator will create all standard scripts
        }
    }
    
    print("📝 AI Content Generated:")
    print(f"   Title: {ai_content['game_design']['title']}")
    print(f"   Genre: {ai_content['game_design']['genre']}")
    print(f"   Mechanics: {len(ai_content['game_mechanics'])} systems")
    print(f"   Levels: {len(ai_content['level_design']['levels'])}")
    print()
    
    # Build the game
    print("🔨 Building game with Godot Engine...")
    project_id = "test_pixel_runner_001"
    
    result = await godot.build_game_from_ai_content(
        project_id=project_id,
        ai_content=ai_content,
        storage_service=storage
    )
    
    if result['success']:
        print("\n✅ Game built successfully!")
        print(f"\n📦 Build Results:")
        print(f"   Project ID: {result['project_id']}")
        print(f"   Project Path: {result['project_path']}")
        print(f"   Build Time: {result['build_time']}")
        
        if result.get('builds'):
            print(f"\n🎮 Available Builds:")
            for platform, url in result['builds'].items():
                print(f"   {platform.upper()}: {url}")
        
        if result.get('web_preview_url'):
            print(f"\n🌐 Web Preview:")
            print(f"   {result['web_preview_url']}")
            print(f"\n   Copy this URL to your browser to play the game!")
        
        # Show generated files
        print(f"\n📁 Generated Files:")
        project_path = Path(result['project_path'])
        
        def show_tree(path, prefix="", max_depth=2, current_depth=0):
            if current_depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    print(f"{prefix}{'└── ' if is_last else '├── '}{item.name}")
                    if item.is_dir() and item.name not in ['.godot', '.import', '__pycache__']:
                        new_prefix = prefix + ('    ' if is_last else '│   ')
                        show_tree(item, new_prefix, max_depth, current_depth + 1)
            except PermissionError:
                pass
        
        show_tree(project_path)
        
        # Show some sample content
        print(f"\n📜 Sample Generated Script (player.gd):")
        player_script = project_path / "scripts/player/player.gd"
        if player_script.exists():
            with open(player_script, 'r') as f:
                lines = f.readlines()[:20]
                for line in lines:
                    print(f"   {line.rstrip()}")
                if len(lines) == 20:
                    print("   ...")
        
        print(f"\n🎬 Sample Generated Scene (main.tscn):")
        main_scene = project_path / "scenes/main.tscn"
        if main_scene.exists():
            with open(main_scene, 'r') as f:
                lines = f.readlines()[:15]
                for line in lines:
                    print(f"   {line.rstrip()}")
                if len(lines) == 15:
                    print("   ...")
        
        print(f"\n⚙️  Project Configuration:")
        project_godot = project_path / "project.godot"
        if project_godot.exists():
            with open(project_godot, 'r') as f:
                lines = f.readlines()[:10]
                for line in lines:
                    print(f"   {line.rstrip()}")
        
    else:
        print(f"\n❌ Game build failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Cleanup
    await godot.stop()
    await storage.disconnect()
    
    print(f"\n✨ Test complete!")


async def test_individual_generators():
    """
    Test individual generator components
    """
    
    print("\n🧪 Testing Individual Generators\n")
    
    from services.gdscript_generator import GDScriptGenerator
    from services.scene_generator import SceneGenerator
    from services.asset_processor import AssetProcessor
    
    # Test GDScript Generator
    print("1️⃣ Testing GDScript Generator...")
    script_gen = GDScriptGenerator()
    
    test_mechanics = {
        "player_movement": {
            "speed": 300.0,
            "jump_force": -400.0
        },
        "player_abilities": ["jump", "double_jump"]
    }
    
    test_design = {
        "title": "Test Game",
        "win_condition": "Collect all items"
    }
    
    scripts = script_gen.generate_all_scripts(test_design, test_mechanics)
    print(f"   ✅ Generated {len(scripts)} scripts")
    for script_path in scripts.keys():
        print(f"      - {script_path}")
    
    # Test Scene Generator
    print("\n2️⃣ Testing Scene Generator...")
    scene_gen = SceneGenerator()
    
    test_level_design = {
        "levels": [
            {
                "name": "Test Level",
                "platforms": [],
                "enemies": [],
                "collectibles": []
            }
        ]
    }
    
    scenes = scene_gen.generate_all_scenes(test_design, test_level_design)
    print(f"   ✅ Generated {len(scenes)} scenes")
    for scene_path in scenes.keys():
        print(f"      - {scene_path}")
    
    # Test Asset Processor
    print("\n3️⃣ Testing Asset Processor...")
    asset_proc = AssetProcessor()
    
    procedural_sprites = asset_proc.generate_procedural_sprites(test_design)
    print(f"   ✅ Generated {len(procedural_sprites)} procedural sprites")
    for sprite_name in procedural_sprites.keys():
        print(f"      - {sprite_name}")
    
    print("\n✅ All generators working!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("   GAMORA AI - Enhanced Godot Integration Test")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_individual_generators())
    asyncio.run(test_godot_integration())
    
    print("\n" + "=" * 60)
    print("   Test Suite Complete!")
    print("=" * 60)
