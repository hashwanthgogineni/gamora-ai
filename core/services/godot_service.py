"""
Godot Engine Service - Build Games from AI Content
Converts AI-generated game mechanics, assets, and logic into playable Godot builds
"""

import os
import json
import asyncio
import subprocess
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import base64
from io import BytesIO

# Import our new generators
from services.gdscript_generator import GDScriptGenerator
from services.scene_generator import SceneGenerator
from services.asset_processor import AssetProcessor
from services.game_architecture import GameArchitectureGenerator
from services.ai_code_generator import AICodeGenerator

logger = logging.getLogger(__name__)


class GodotService:
    """
    Godot Engine integration service
    Takes AI-generated content and produces playable game builds
    """
    
    def __init__(
        self,
        godot_path: str = "/usr/local/bin/godot",
        projects_dir: str = "./projects",
        templates_dir: str = "./godot_templates"
    ):
        self.godot_executable = godot_path
        self.projects_dir = Path(projects_dir)
        self.templates_dir = Path(templates_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Build export templates location (Windows uses AppData, Linux/Mac uses .local/share)
        if os.name == 'nt':  # Windows
            self.export_templates_dir = Path(os.getenv('APPDATA', '')) / "Godot" / "export_templates"
        else:  # Linux/Mac
            self.export_templates_dir = Path.home() / ".local/share/godot/export_templates"
        
        # Initialize generators
        self.script_generator = GDScriptGenerator()
        self.scene_generator = SceneGenerator()
        self.asset_processor = AssetProcessor()
        self.architecture_generator = GameArchitectureGenerator()
        
        logger.info(f"🎮 Godot Service initialized")
        logger.info(f"   Godot: {godot_path}")
        logger.info(f"   Projects: {projects_dir}")
    
    async def start(self):
        """Initialize Godot service"""
        # Verify Godot installation
        if not await self._verify_godot():
            raise RuntimeError("Godot executable not found or not working")
        
        # Setup export templates
        await self._setup_export_templates()
        
        logger.info("✅ Godot service started successfully")
    
    async def stop(self):
        """Cleanup on shutdown"""
        logger.info("🛑 Godot service stopped")
    
    async def is_healthy(self) -> bool:
        """Health check"""
        return await self._verify_godot()
    
    async def build_game_from_ai_content(
        self,
        project_id: str,
        ai_content: Dict[str, Any],
        storage_service: Any,
        deepseek_client = None
    ) -> Dict[str, Any]:
        """
        Main method: Build complete Godot game from AI-generated content
        
        Args:
            project_id: Unique project identifier
            ai_content: Dictionary containing all AI-generated content:
                - game_design: Game design specifications
                - game_mechanics: Gameplay mechanics and rules
                - assets: Generated sprites, textures, audio
                - scripts: GDScript code
                - ui_design: UI layout and styling
                - level_design: Level layouts and objects
            storage_service: Storage service for uploading builds
        
        Returns:
            Dictionary with build results and URLs
        """
        logger.info(f"🎮 Building game for project: {project_id}")
        
        try:
            # Create project directory
            project_path = self.projects_dir / project_id
            if project_path.exists():
                shutil.rmtree(project_path)
            project_path.mkdir(parents=True)
            
            # Step 1: Create Godot project structure
            await self._create_project_structure(project_path)
            
            # Step 2: Generate project.godot configuration
            await self._generate_project_config(
                project_path,
                ai_content.get('game_design', {})
            )
            
            # Step 3: Write game assets (sprites, audio, textures)
            await self._write_game_assets(
                project_path,
                ai_content.get('assets', []),
                ai_content.get('game_design', {})
            )
            
            # Step 4: Generate GDScript files (hybrid AI approach)
            await self._generate_scripts(
                project_path,
                ai_content.get('scripts', {}),
                ai_content.get('game_mechanics', {}),
                ai_content.get('game_design', {}),
                deepseek_client  # Pass AI client for code generation
            )
            
            # Step 5: Create game scenes
            await self._generate_scenes(
                project_path,
                ai_content.get('level_design', {}),
                ai_content.get('ui_design', {}),
                ai_content.get('game_design', {})
            )
            
            # Step 6: Generate UI
            await self._generate_ui(
                project_path,
                ai_content.get('ui_design', {})
            )
            
            # Step 7: Export game builds
            builds = await self._export_game_builds(project_path, project_id)
            
            # Step 8: Upload to storage
            urls = await self._upload_builds_to_storage(
                builds,
                project_id,
                storage_service
            )
            
            # Step 9: Create web preview
            web_preview_url = await self._create_web_preview(
                project_path,
                project_id,
                storage_service
            )
            
            result = {
                "success": True,
                "project_id": project_id,
                "builds": urls,
                "web_preview_url": web_preview_url,
                "build_time": datetime.utcnow().isoformat(),
                "project_path": str(project_path)
            }
            
            logger.info(f"✅ Game built successfully: {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Game build failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }
    
    async def _verify_godot(self) -> bool:
        """Verify Godot installation"""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"✅ Godot {version} detected")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Godot verification failed: {e}")
            return False
    
    async def _setup_export_templates(self):
        """Setup Godot export templates for building"""
        # This would download/setup export templates
        # For now, we'll assume they're installed
        logger.info("📦 Export templates ready")
    
    async def _create_project_structure(self, project_path: Path):
        """Create standard Godot project directory structure"""
        directories = [
            "scenes",
            "scenes/levels",
            "scenes/ui",
            "scripts",
            "scripts/player",
            "scripts/enemies",
            "scripts/managers",
            "assets",
            "assets/sprites",
            "assets/textures",
            "assets/audio",
            "assets/music",
            "assets/fonts",
            "assets/shaders"
        ]
        
        for directory in directories:
            (project_path / directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Project structure created: {project_path}")
    
    async def _write_game_assets(
        self,
        project_path: Path,
        assets: List[Dict]
    ):
        """Write AI-generated assets to project"""
        import base64
        
        for asset in assets:
            asset_path = project_path / asset['path']
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle different asset types
            if asset['type'] in ['texture', 'sprite', 'image']:
                # Decode base64 if present
                if asset.get('content'):
                    try:
                        image_data = base64.b64decode(asset['content'])
                        with open(asset_path, 'wb') as f:
                            f.write(image_data)
                    except Exception as e:
                        logger.warning(f"Failed to decode asset {asset['name']}: {e}")
                        # Create placeholder
                        self._create_placeholder_texture(asset_path)
                else:
                    # Create placeholder if no content
                    self._create_placeholder_texture(asset_path)
            
            elif asset['type'] == 'audio':
                # Handle audio assets
                if asset.get('content'):
                    try:
                        audio_data = base64.b64decode(asset['content'])
                        with open(asset_path, 'wb') as f:
                            f.write(audio_data)
                    except Exception as e:
                        logger.warning(f"Failed to decode audio {asset['name']}: {e}")
            
            elif asset['type'] == 'script':
                # Write script content
                with open(asset_path, 'w') as f:
                    f.write(asset.get('content', ''))
        
        logger.info(f"✅ {len(assets)} assets written")
    
    def _create_placeholder_texture(self, path: Path):
        """Create a simple placeholder image using PIL"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple colored square
            img = Image.new('RGB', (64, 64), color=(100, 150, 200))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, 54, 54], outline=(255, 255, 255), width=2)
            img.save(path)
        except Exception as e:
            logger.warning(f"Failed to create placeholder: {e}")
    
    async def _generate_project_config(
        self,
        project_path: Path,
        game_design: Dict
    ):
        """Generate project.godot configuration file"""
        
        title = game_design.get('title', 'Gamora AI Game')
        description = game_design.get('description', 'Generated by Gamora AI')
        
        # Check if 3D game
        dimension = game_design.get('dimension', '2D')
        is_3d = dimension == '3D' or '3d' in game_design.get('genre', '').lower()
        
        # Physics settings based on dimension
        if is_3d:
            physics_settings = '''
[physics/3d]

default_gravity=20.0
default_gravity_vector=Vector3(0, -1, 0)
default_linear_damp=0.1
default_angular_damp=0.1
'''
        else:
            physics_settings = '''
[physics/2d]

default_gravity=980.0
default_gravity_vector=Vector2(0, 1)
default_linear_damp=0.1
default_angular_damp=0.1
'''
        
        # Use regular string formatting to avoid f-string issues with curly braces
        config_content = '''[application]

config/name="''' + title + '''"
config/description="''' + description + '''"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.2", "GL Compatibility")
config/icon="res://icon.png"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[input]

ui_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194319,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)
]}
ui_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194321,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"location":0,"echo":false,"script":null)
]}
ui_accept={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194320,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)
, Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)
]}

[display]

window/size/viewport_width=1280
window/size/viewport_height=720
window/size/resizable=true
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/vram_compression/import_etc2_astc=true
'''
        
        # Add physics settings
        config_content += physics_settings
        
        # Add 3D-specific rendering settings if needed
        if is_3d:
            config_content += '''
[rendering]

3d/use_occlusion_culling=true
3d/use_occlusion_culling_bake=true
'''
        
        with open(project_path / "project.godot", "w") as f:
            f.write(config_content)
        
        logger.info("⚙️ Project configuration generated")
    
    async def _write_game_assets(
        self,
        project_path: Path,
        assets: List[Dict],
        game_design: Dict = None
    ):
        """Write all game assets to project using our asset processor"""
        
        logger.info("📦 Processing and writing game assets...")
        
        # Generate procedural sprites if needed
        if game_design is None:
            game_design = {}
        
        procedural_sprites = self.asset_processor.generate_procedural_sprites(game_design)
        
        # Organize all assets
        organized_assets = self.asset_processor.organize_assets(assets, procedural_sprites)
        
        # Validate assets before writing
        if not organized_assets:
            logger.warning("⚠️  No assets to write, generating fallback procedural sprites")
            # Ensure we have at least basic sprites
            if not procedural_sprites:
                procedural_sprites = self.asset_processor.generate_procedural_sprites(game_design)
            for name, data in procedural_sprites.items():
                path = f"assets/sprites/{name}"
                organized_assets[path] = data
        
        # Write all assets to disk with error handling
        written_count = 0
        for asset_path, asset_data in organized_assets.items():
            if not asset_path:
                logger.warning("Skipping asset with empty path")
                continue
                
            full_path = project_path / asset_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                if isinstance(asset_data, bytes):
                    if len(asset_data) == 0:
                        logger.warning(f"Skipping empty asset: {asset_path}")
                        continue
                    with open(full_path, 'wb') as f:
                        f.write(asset_data)
                    written_count += 1
                elif isinstance(asset_data, str):
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(asset_data)
                    written_count += 1
                else:
                    logger.warning(f"Unknown asset data type for {asset_path}: {type(asset_data)}")
                
                logger.debug(f"   ✅ Asset written: {asset_path}")
                
            except Exception as e:
                logger.error(f"   ❌ Failed to write asset {asset_path}: {e}", exc_info=True)
        
        if written_count == 0:
            logger.error("⚠️  No assets were successfully written!")
        else:
            logger.info(f"✅ {written_count} assets written to project")
        
        # Create placeholder icon if not provided
        icon_path = project_path / "icon.png"
        if not icon_path.exists():
            await self._create_placeholder_icon(icon_path)
        
        logger.info(f"✅ {len(organized_assets)} assets written to project")
    
    
    async def _create_placeholder_icon(self, icon_path: Path):
        """Create a simple placeholder icon"""
        from PIL import Image, ImageDraw
        
        img = Image.new('RGB', (128, 128), color=(73, 109, 137))
        draw = ImageDraw.Draw(img)
        draw.ellipse([20, 20, 108, 108], fill=(255, 255, 255))
        img.save(icon_path)
    
    async def _generate_scripts(
        self,
        project_path: Path,
        scripts: Dict,
        mechanics: Dict,
        game_design: Dict = None,
        deepseek_client = None
    ):
        """Generate all GDScript files using hybrid AI approach (AI + fallback templates)"""
        
        logger.info("📝 Generating GDScript files with hybrid AI approach...")
        
        try:
            # Use provided game_design or extract from scripts
            if game_design is None:
                game_design = scripts.get('game_design', {})
            
            # Ensure we have valid game_design and mechanics
            if not game_design:
                game_design = {"dimension": "3D", "genre": "endless_runner"}
                logger.warning("No game_design provided, using defaults")
            if not mechanics:
                mechanics = {"player_movement": {"speed": 500.0, "jump_force": 8.0}}
                logger.warning("No mechanics provided, using defaults")
            
            # Check if we should use AI generation
            use_ai = scripts.get('use_ai', True) and deepseek_client is not None
            
            if use_ai:
                # Use AI-powered code generator (with template fallback)
                logger.info("🤖 Using AI to generate unique game code...")
                ai_generator = AICodeGenerator(deepseek_client)
                generated_scripts = await ai_generator.generate_all_scripts(
                    game_design,
                    mechanics,
                    use_ai=True
                )
            else:
                # Use template-based generator (fallback)
                logger.info("📝 Using template-based code generation...")
                generated_scripts = self.script_generator.generate_all_scripts(
                    game_design,
                    mechanics
                )
            
            if not generated_scripts or len(generated_scripts) == 0:
                logger.error("❌ Script generator returned empty scripts!")
                raise ValueError("No scripts generated")
            
            # Write all scripts to project
            written_count = 0
            for script_path, script_content in generated_scripts.items():
                try:
                    full_path = project_path / script_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Ensure script content is not empty
                    if not script_content or len(script_content.strip()) == 0:
                        logger.warning(f"⚠️  Empty script content for {script_path}, skipping")
                        continue
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    written_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to write script {script_path}: {e}", exc_info=True)
                    # Continue with other scripts
            
            # Generate professional architecture scripts
            try:
                logger.info("🏗️  Generating professional game architecture...")
                
                # Game state manager
                state_manager_script = self.architecture_generator.generate_game_state_manager(game_design)
                state_manager_path = project_path / "scripts/managers/game_state_manager.gd"
                state_manager_path.parent.mkdir(parents=True, exist_ok=True)
                with open(state_manager_path, 'w', encoding='utf-8') as f:
                    f.write(state_manager_script)
                written_count += 1
                
                # Event system
                event_system_script = self.architecture_generator.generate_event_system()
                event_system_path = project_path / "scripts/managers/event_system.gd"
                with open(event_system_path, 'w', encoding='utf-8') as f:
                    f.write(event_system_script)
                written_count += 1
                
                # Physics manager
                physics_manager_script = self.architecture_generator.generate_physics_manager(game_design)
                physics_manager_path = project_path / "scripts/managers/physics_manager.gd"
                with open(physics_manager_path, 'w', encoding='utf-8') as f:
                    f.write(physics_manager_script)
                written_count += 1
                
                # Audio manager
                audio_manager_script = self.architecture_generator.generate_audio_manager()
                audio_manager_path = project_path / "scripts/managers/audio_manager.gd"
                with open(audio_manager_path, 'w', encoding='utf-8') as f:
                    f.write(audio_manager_script)
                written_count += 1
                
                logger.info("✅ Professional architecture scripts generated")
            except Exception as e:
                logger.warning(f"⚠️  Architecture generation failed (non-critical): {e}")
            
            # Write any custom AI-generated scripts (if any)
            for script_name, script_content in scripts.items():
                if script_name not in ['game_design', 'scripts_generated_by', 'custom_scripts', 'status', 'error']:
                    try:
                        script_path = project_path / f"scripts/{script_name}.gd"
                        script_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(script_path, "w", encoding='utf-8') as f:
                            f.write(str(script_content))
                        written_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to write custom script {script_name}: {e}")
            
            logger.info(f"✅ Generated and wrote {written_count} GDScript files")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: Script generation failed: {e}", exc_info=True)
            # This should never happen, but if it does, we need to ensure scripts are still generated
            # Use fallback generator
            try:
                logger.info("🔄 Attempting fallback script generation...")
                fallback_scripts = self.script_generator.generate_all_scripts(
                    game_design or {"dimension": "3D", "genre": "endless_runner"},
                    mechanics or {"player_movement": {"speed": 500.0, "jump_force": 8.0}}
                )
                for script_path, script_content in fallback_scripts.items():
                    full_path = project_path / script_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                logger.info(f"✅ Fallback: Generated {len(fallback_scripts)} scripts")
            except Exception as fallback_error:
                logger.critical(f"💀 Fatal: Even fallback script generation failed: {fallback_error}", exc_info=True)
                raise RuntimeError(f"Script generation completely failed: {e}, fallback also failed: {fallback_error}")
    
    
    def _generate_player_script(self, mechanics: Dict) -> str:
        """Generate player controller GDScript"""
        
        movement = mechanics.get('player_movement', {})
        speed = movement.get('speed', 300.0)
        jump_force = movement.get('jump_force', -400.0)
        
        return f'''extends CharacterBody2D

# Player movement constants
const SPEED = {speed}
const JUMP_VELOCITY = {jump_force}
const ACCELERATION = 1500.0
const FRICTION = 1200.0

# Get gravity from project settings
var gravity = ProjectSettings.get_setting("physics/2d/default_gravity")

@onready var sprite = $Sprite2D
@onready var animation_player = $AnimationPlayer if has_node("AnimationPlayer") else null

func _physics_process(delta):
\t# Apply gravity
\tif not is_on_floor():
\t\tvelocity.y += gravity * delta
\t
\t# Handle jump
\tif Input.is_action_just_pressed("jump") and is_on_floor():
\t\tvelocity.y = JUMP_VELOCITY
\t\tif animation_player:
\t\t\tanimation_player.play("jump")
\t
\t# Get input direction
\tvar direction = Input.get_axis("move_left", "move_right")
\t
\t# Apply movement with acceleration/friction
\tif direction != 0:
\t\tvelocity.x = move_toward(velocity.x, direction * SPEED, ACCELERATION * delta)
\t\tsprite.flip_h = direction < 0
\t\tif is_on_floor() and animation_player:
\t\t\tanimation_player.play("run")
\telse:
\t\tvelocity.x = move_toward(velocity.x, 0, FRICTION * delta)
\t\tif is_on_floor() and animation_player:
\t\t\tanimation_player.play("idle")
\t
\tmove_and_slide()

func take_damage(amount: int):
\t# Override this in child classes
\tpass

func collect_item(item_type: String):
\t# Signal to game manager
\tGameManager.on_item_collected(item_type)
'''
    
    def _generate_game_manager_script(self, mechanics: Dict) -> str:
        """Generate game manager singleton script"""
        
        return '''extends Node

# Game state signals
signal game_started
signal game_paused
signal game_resumed
signal game_over(won: bool)
signal score_changed(new_score: int)
signal health_changed(new_health: int)

# Game state
var score: int = 0
var health: int = 100
var is_paused: bool = false
var game_active: bool = false

func _ready():
\tprocess_mode = Node.PROCESS_MODE_ALWAYS

func start_game():
\tgame_active = true
\tscore = 0
\thealth = 100
\temit_signal("game_started")

func pause_game():
\tis_paused = true
\tget_tree().paused = true
\temit_signal("game_paused")

func resume_game():
\tis_paused = false
\tget_tree().paused = false
\temit_signal("game_resumed")

func end_game(won: bool):
\tgame_active = false
\temit_signal("game_over", won)

func add_score(points: int):
\tif game_active:
\t\tscore += points
\t\temit_signal("score_changed", score)

func modify_health(amount: int):
\tif game_active:
\t\thealth = clamp(health + amount, 0, 100)
\t\temit_signal("health_changed", health)
\t\tif health <= 0:
\t\t\tend_game(false)

func on_item_collected(item_type: String):
\tmatch item_type:
\t\t"coin":
\t\t\tadd_score(10)
\t\t"health":
\t\t\tmodify_health(20)
\t\t"powerup":
\t\t\tadd_score(50)

func restart_game():
\tget_tree().reload_current_scene()
'''
    
    async def _generate_scenes(
        self,
        project_path: Path,
        level_design: Dict,
        ui_design: Dict,
        game_design: Dict = None
    ):
        """Generate Godot scene files (.tscn) using our scene generator"""
        
        logger.info("🎬 Generating scene files from AI level design...")
        
        # Use provided game_design or extract from other dicts
        if game_design is None:
            game_design = level_design.get('game_design', ui_design.get('game_design', {}))
        
        # Generate all scenes using our generator
        generated_scenes = self.scene_generator.generate_all_scenes(
            game_design,
            level_design
        )
        
        # Write all scenes to project
        for scene_path, scene_content in generated_scenes.items():
            full_path = project_path / scene_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(scene_content)
        
        logger.info(f"✅ Generated {len(generated_scenes)} scene files")
    
    
    def _generate_main_scene(self, level_design: Dict) -> str:
        """Generate main game scene"""
        
        return '''[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/managers/game_manager.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="2"]

[node name="Main" type="Node2D"]

[node name="GameManager" type="Node" parent="."]
script = ExtResource("1")

[node name="Player" parent="." instance=ExtResource("2")]
position = Vector2(640, 500)

[node name="Ground" type="StaticBody2D" parent="."]
position = Vector2(640, 650)

[node name="ColorRect" type="ColorRect" parent="Ground"]
offset_left = -640.0
offset_top = -50.0
offset_right = 640.0
offset_bottom = 50.0
color = Color(0.4, 0.3, 0.2, 1)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Ground"]
shape = RectangleShape2D

[node name="Camera2D" type="Camera2D" parent="."]
position = Vector2(640, 360)
zoom = Vector2(1, 1)
'''
    
    def _generate_player_scene(self) -> str:
        """Generate player scene"""
        
        return '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="1"]
size = Vector2(32, 64)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color(0.4, 0.6, 1, 1)
texture = PlaceholderTexture2D.new()
offset = Vector2(0, 0)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("1")

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(1.5, 1.5)
position_smoothing_enabled = true
'''
    
    async def _generate_ui(self, project_path: Path, ui_design: Dict):
        """Generate UI scenes and scripts"""
        
        ui_scene = '''[gd_scene format=3]

[node name="UI" type="CanvasLayer"]

[node name="ScoreLabel" type="Label" parent="."]
offset_left = 20.0
offset_top = 20.0
offset_right = 200.0
offset_bottom = 60.0
text = "Score: 0"
theme_override_font_sizes/font_size = 24

[node name="HealthLabel" type="Label" parent="."]
offset_left = 20.0
offset_top = 60.0
offset_right = 200.0
offset_bottom = 100.0
text = "Health: 100"
theme_override_font_sizes/font_size = 24
'''
        
        with open(project_path / "scenes/ui/game_ui.tscn", "w") as f:
            f.write(ui_scene)
        
        logger.info("🎨 UI generated")
    
    async def _export_game_builds(
        self,
        project_path: Path,
        project_id: str
    ) -> Dict[str, Path]:
        """Export game to multiple platforms"""
        
        builds = {}
        export_dir = project_path / "exports"
        # Ensure directory exists with absolute path
        export_dir = export_dir.resolve()
        export_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Export directory: {export_dir}")
        
        # Export for Web (HTML5) - Universal browser preview
        web_path = export_dir / f"{project_id}_web.html"
        web_path = web_path.resolve()
        await self._export_for_web(project_path, web_path)
        if web_path.exists():
            builds['web'] = web_path
        
        # Export for Windows (EXE) - Native Windows executable
        windows_path = export_dir / f"{project_id}_windows.exe"
        windows_path = windows_path.resolve()
        await self._export_for_windows(project_path, windows_path)
        if windows_path.exists():
            builds['windows'] = windows_path
        
        # Export for macOS (.app) - Native macOS application
        macos_path = export_dir / f"{project_id}_macos.zip"
        macos_path = macos_path.resolve()
        await self._export_for_macos(project_path, macos_path)
        if macos_path.exists():
            builds['macos'] = macos_path
        
        # Export for Linux - Native Linux executable
        linux_path = export_dir / f"{project_id}_linux.x86_64"
        linux_path = linux_path.resolve()
        await self._export_for_linux(project_path, linux_path)
        if linux_path.exists():
            builds['linux'] = linux_path
        
        # Export for Android (APK) - Android application
        android_path = export_dir / f"{project_id}_android.apk"
        android_path = android_path.resolve()
        await self._export_for_android(project_path, android_path)
        if android_path.exists():
            builds['android'] = android_path
        
        # Export for iOS (.ipa) - iOS application (requires certificates)
        ios_path = export_dir / f"{project_id}_ios.ipa"
        ios_path = ios_path.resolve()
        await self._export_for_ios(project_path, ios_path)
        if ios_path.exists():
            builds['ios'] = ios_path
        
        logger.info(f"📦 Exported {len(builds)} build(s): {list(builds.keys())}")
        return builds
    
    async def _export_for_web(self, project_path: Path, output_path: Path):
        """Export game for web/HTML5"""
        try:
            # Ensure output path is absolute
            output_path = output_path.resolve()
            # Use forward slashes for Godot config (works on Windows)
            output_path_str = str(output_path).replace('\\', '/')
            
            export_preset = '''[preset.0]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
progressive_web_app/offline_page=""
progressive_web_app/display=1
progressive_web_app/orientation=0
progressive_web_app/icon_144x144=""
progressive_web_app/icon_180x180=""
progressive_web_app/icon_512x512=""
progressive_web_app/background_color=Color(0, 0, 0, 1)
'''.format(output=output_path_str)
            
            export_presets_path = project_path / "export_presets.cfg"
            with open(export_presets_path, "w") as f:
                f.write(export_preset)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to absolute path and use forward slashes for Godot (works on Windows too)
            abs_output_path = output_path.resolve()
            # Use forward slashes for Godot export path (Godot handles this on Windows)
            godot_output_path = str(abs_output_path).replace('\\', '/')
            
            logger.info(f"🎮 Exporting to: {godot_output_path}")
            
            # Run Godot export
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "Web",
                godot_output_path,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Web export failed: {stderr.decode()}")
            else:
                logger.info("✅ Web build exported")
                
        except Exception as e:
            logger.error(f"Web export error: {e}")
    
    async def _export_for_windows(self, project_path: Path, output_path: Path):
        """Export game for Windows (EXE)"""
        try:
            # Ensure output path is absolute
            output_path = output_path.resolve()
            # Use forward slashes for Godot config (works on Windows)
            output_path_str = str(output_path).replace('\\', '/')
            
            export_preset = '''[preset.1]

name="Windows Desktop"
platform="Windows Desktop"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.1.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
binary_format/embed_pck=true
binary_format/architecture="x86_64"
'''.format(output=output_path_str)
            
            # Read existing export presets or create new
            export_presets_path = project_path / "export_presets.cfg"
            existing_presets = ""
            if export_presets_path.exists():
                with open(export_presets_path, "r") as f:
                    existing_presets = f.read()
            
            # Append Windows preset (or replace if already exists)
            if "[preset.1]" not in existing_presets:
                with open(export_presets_path, "a") as f:
                    f.write("\n" + export_preset)
            else:
                # Replace existing Windows preset
                lines = existing_presets.split('\n')
                new_lines = []
                skip_until_next_preset = False
                for i, line in enumerate(lines):
                    if line.strip() == "[preset.1]":
                        skip_until_next_preset = True
                        # Write new preset
                        new_lines.append(export_preset)
                        # Skip until next preset or end
                        continue
                    if skip_until_next_preset:
                        if line.strip().startswith("[preset.") and line.strip() != "[preset.1]":
                            skip_until_next_preset = False
                            new_lines.append(line)
                        continue
                    new_lines.append(line)
                with open(export_presets_path, "w") as f:
                    f.write('\n'.join(new_lines))
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to absolute path and use forward slashes for Godot
            abs_output_path = output_path.resolve()
            godot_output_path = str(abs_output_path).replace('\\', '/')
            
            logger.info(f"🎮 Exporting Windows EXE to: {godot_output_path}")
            
            # Run Godot export for Windows
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "Windows Desktop",
                godot_output_path,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.error(f"Windows export failed: {error_msg}")
                # Don't fail completely - web export might still work
            else:
                logger.info("✅ Windows EXE build exported")
                if output_path.exists():
                    logger.info(f"✅ EXE file created: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
                else:
                    logger.warning(f"⚠️  EXE file not found at expected path: {output_path}")
                
        except Exception as e:
            logger.error(f"Windows export error: {e}", exc_info=True)
            # Don't raise - allow other exports to continue
    
    async def _export_for_macos(self, project_path: Path, output_path: Path):
        """Export game for macOS (.app bundle, packaged as ZIP)"""
        try:
            # macOS exports as .app bundle, we'll zip it
            app_output = output_path.parent / f"{output_path.stem.replace('_macos', '')}.app"
            app_output = app_output.resolve()
            output_path_str = str(app_output).replace('\\', '/')
            
            export_preset = '''[preset.2]

name="macOS"
platform="macOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.2.options]

custom_template/debug=""
custom_template/release=""
binary_format/architecture="universal"
binary_format/embed_pck=true
codesign/enable=false
'''.format(output=output_path_str)
            
            # Update export presets
            export_presets_path = project_path / "export_presets.cfg"
            await self._update_export_preset(export_presets_path, export_preset, "[preset.2]")
            
            # Ensure output directory exists
            app_output.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🍎 Exporting macOS app to: {output_path_str}")
            
            # Run Godot export for macOS
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "macOS",
                output_path_str,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.warning(f"macOS export failed: {error_msg}")
            else:
                logger.info("✅ macOS app exported")
                # Zip the .app bundle
                if app_output.exists():
                    import shutil
                    shutil.make_archive(str(output_path.with_suffix('')), 'zip', app_output.parent, app_output.name)
                    logger.info(f"✅ macOS ZIP created: {output_path}")
                
        except Exception as e:
            logger.warning(f"macOS export error: {e}")
    
    async def _export_for_linux(self, project_path: Path, output_path: Path):
        """Export game for Linux (x86_64 executable)"""
        try:
            output_path_str = str(output_path.resolve()).replace('\\', '/')
            
            export_preset = '''[preset.3]

name="Linux/X11"
platform="Linux/X11"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.3.options]

custom_template/debug=""
custom_template/release=""
binary_format/architecture="x86_64"
binary_format/embed_pck=true
'''.format(output=output_path_str)
            
            # Update export presets
            export_presets_path = project_path / "export_presets.cfg"
            await self._update_export_preset(export_presets_path, export_preset, "[preset.3]")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🐧 Exporting Linux executable to: {output_path_str}")
            
            # Run Godot export for Linux
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "Linux/X11",
                output_path_str,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.warning(f"Linux export failed: {error_msg}")
            else:
                logger.info("✅ Linux executable exported")
                # Make executable
                if output_path.exists():
                    os.chmod(output_path, 0o755)
                    logger.info(f"✅ Linux executable created: {output_path}")
                
        except Exception as e:
            logger.warning(f"Linux export error: {e}")
    
    async def _export_for_android(self, project_path: Path, output_path: Path):
        """Export game for Android (APK)"""
        try:
            output_path_str = str(output_path.resolve()).replace('\\', '/')
            
            export_preset = '''[preset.4]

name="Android"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.4.options]

gradle_build/use_gradle_build=false
binary_format/architecture="arm64v8"
binary_format/embed_pck=true
version/code="1"
version/name="1.0"
package/unique_name="com.gamoraai.game"
package/name="Gamora Game"
package/signed=false
screen/orientation=0
screen/immersive_mode=true
'''.format(output=output_path_str)
            
            # Update export presets
            export_presets_path = project_path / "export_presets.cfg"
            await self._update_export_preset(export_presets_path, export_preset, "[preset.4]")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📱 Exporting Android APK to: {output_path_str}")
            
            # Run Godot export for Android
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "Android",
                output_path_str,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.warning(f"Android export failed: {error_msg}")
            else:
                logger.info("✅ Android APK exported")
                if output_path.exists():
                    logger.info(f"✅ APK created: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
                
        except Exception as e:
            logger.warning(f"Android export error: {e}")
    
    async def _export_for_ios(self, project_path: Path, output_path: Path):
        """Export game for iOS (.ipa) - Note: Requires Xcode and certificates"""
        try:
            output_path_str = str(output_path.resolve()).replace('\\', '/')
            
            export_preset = '''[preset.5]

name="iOS"
platform="iOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{output}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.5.options]

custom_template/debug=""
custom_template/release=""
binary_format/architecture="universal"
binary_format/embed_pck=true
application/app_store_team_id=""
application/provisioning_profile_uuid=""
application/certificate_path=""
application/certificate_password=""
application/certificate_identity=""
application/export_method=0
application/target_device=2
'''.format(output=output_path_str)
            
            # Update export presets
            export_presets_path = project_path / "export_presets.cfg"
            await self._update_export_preset(export_presets_path, export_preset, "[preset.5]")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🍎 Exporting iOS IPA to: {output_path_str}")
            
            # Run Godot export for iOS
            proc = await asyncio.create_subprocess_exec(
                self.godot_executable,
                "--headless",
                "--export-release",
                "iOS",
                output_path_str,
                cwd=str(project_path.resolve()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.warning(f"iOS export failed (may require Xcode/certificates): {error_msg}")
            else:
                logger.info("✅ iOS IPA exported")
                if output_path.exists():
                    logger.info(f"✅ IPA created: {output_path}")
                
        except Exception as e:
            logger.warning(f"iOS export error (may require Xcode/certificates): {e}")
    
    async def _upload_builds_to_storage(
        self,
        builds: Dict[str, Path],
        project_id: str,
        storage_service: Any
    ) -> Dict[str, str]:
        """Upload all builds to Supabase storage"""
        
        urls = {}
        
        for platform, build_path in builds.items():
            try:
                if not build_path.exists():
                    logger.warning(f"Build file not found: {build_path}")
                    continue
                
                # Read build file
                with open(build_path, 'rb') as f:
                    build_data = f.read()
                
                # Upload to storage
                storage_path = f"games/{project_id}/{platform}/{build_path.name}"
                url = await storage_service.upload_file(
                    storage_path,
                    build_data,
                    content_type=self._get_content_type(build_path)
                )
                
                urls[platform] = url
                logger.info(f"✅ Uploaded {platform} build: {url}")
                
            except Exception as e:
                logger.error(f"Failed to upload {platform} build: {e}")
        
        return urls
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for file"""
        ext = file_path.suffix.lower()
        content_types = {
            '.html': 'text/html',
            '.js': 'application/javascript',
            '.wasm': 'application/wasm',
            '.pck': 'application/octet-stream',
            '.exe': 'application/x-msdownload',
            '.zip': 'application/zip'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    async def _create_web_preview(
        self,
        project_path: Path,
        project_id: str,
        storage_service: Any
    ) -> str:
        """Create web preview by uploading HTML5 build files"""
        try:
            exports_dir = project_path / "exports"
            
            # Find all web export files
            web_files = list(exports_dir.glob(f"{project_id}_web.*"))
            
            preview_url = None
            for file in web_files:
                if file.suffix == '.html':
                    # Read HTML file
                    with open(file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Get the Supabase public URL for assets (for relative paths)
                    # We'll modify the HTML to use absolute URLs for assets
                    supabase_public_url = preview_url if 'preview_url' in locals() else None
                    
                    # Note: We'll upload the original HTML to Supabase first,
                    # then return a proxy URL that will serve it with proper headers
                    # The assets (.wasm, .pck) will still load from Supabase using relative paths
                    
                    # Convert to bytes for upload
                    html_data = html_content.encode('utf-8')
                    
                    storage_path = f"games/{project_id}/preview/index.html"
                    preview_url = await storage_service.upload_file(
                        storage_path,
                        html_data,
                        content_type='text/html',
                        public=True
                    )
            
            # Upload associated files (.wasm, .pck, .js)
            for file in web_files:
                if file.suffix != '.html':
                    with open(file, 'rb') as f:
                        file_data = f.read()
                    
                    storage_path = f"games/{project_id}/preview/{file.name}"
                    await storage_service.upload_file(
                        storage_path,
                        file_data,
                        content_type=self._get_content_type(file),
                        public=True
                    )
            
            # Create a simple launcher script for easy local execution
            launcher_script = self._create_web_launcher(project_id)
            if launcher_script:
                launcher_path = f"games/{project_id}/preview/PLAY_GAME.bat"
                await storage_service.upload_file(
                    launcher_path,
                    launcher_script.encode('utf-8'),
                    content_type='application/x-msdownload',
                    public=True
                )
                logger.info(f"✅ Created launcher: PLAY_GAME.bat")
            
            logger.info(f"🌐 Web preview created: {preview_url}")
            
            # Return proxy URL instead of direct Supabase URL to bypass CSP
            # The proxy endpoint serves the HTML with proper headers
            from config.settings import Settings
            settings = Settings()
            api_base = getattr(settings, 'api_base_url', None) or "http://localhost:8000"
            proxy_url = f"{api_base}/api/v1/generate/preview/{project_id}"
            logger.info(f"🔗 Using proxy URL: {proxy_url} (bypasses Supabase CSP)")
            return proxy_url
            
        except Exception as e:
            logger.error(f"Failed to create web preview: {e}")
            return None
    
    def _create_web_launcher(self, project_id: str) -> str:
        """Create a simple batch file launcher for Windows that auto-starts a local server"""
        launcher = f'''@echo off
echo ========================================
echo    Gamora AI - Game Launcher
echo ========================================
echo.
echo Starting local server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://www.python.org/
    echo Or use one of these alternatives:
    echo   1. Install Python and add it to PATH
    echo   2. Use Node.js: npm install -g http-server, then run: http-server -p 8000
    echo   3. Use VS Code Live Server extension
    echo.
    pause
    exit /b 1
)

REM Start Python HTTP server in background
start /B python -m http.server 8000

REM Wait a moment for server to start
timeout /t 2 /nobreak >nul

REM Open browser
start http://localhost:8000/index.html

echo.
echo Game should open in your browser!
echo.
echo To stop the server, close this window or press Ctrl+C
echo.
pause
'''
        return launcher
    
    async def _update_export_preset(self, presets_path: Path, new_preset: str, preset_id: str):
        """Helper to update or add export preset"""
        existing_presets = ""
        if presets_path.exists():
            with open(presets_path, "r") as f:
                existing_presets = f.read()
        
        if preset_id not in existing_presets:
            # Append new preset
            with open(presets_path, "a") as f:
                f.write("\n" + new_preset)
        else:
            # Replace existing preset
            lines = existing_presets.split('\n')
            new_lines = []
            skip_until_next_preset = False
            for line in lines:
                if line.strip() == preset_id:
                    skip_until_next_preset = True
                    new_lines.append(new_preset)
                    continue
                if skip_until_next_preset:
                    if line.strip().startswith("[preset.") and line.strip() != preset_id:
                        skip_until_next_preset = False
                        new_lines.append(line)
                    continue
                new_lines.append(line)
            with open(presets_path, "w") as f:
                f.write('\n'.join(new_lines))
