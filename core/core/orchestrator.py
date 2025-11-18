"""
Master Orchestrator
Coordinates all AI agents and the Godot build pipeline
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import hashlib
import json

from models.chatgpt_client import ChatGPTClient
from models.deepseek_client import DeepSeekClient
from agents.asset_manager import AssetManagerAgent

logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """
    Orchestrates the complete game generation pipeline using DeepSeek R1:
    1. Analyze user prompt (DeepSeek R1)
    2. Generate game design (DeepSeek R1)
    3. Generate code/logic (DeepSeek R1)
    4. Generate assets (DALL-E + procedural)
    5. Build with Godot
    6. Upload to storage
    
    Cost optimization: Uses only DeepSeek R1 for all text/code generation
    """
    
    def __init__(
        self,
        openai_api_key: str,
        deepseek_api_key: str,
        cache_manager,
        godot_service,
        storage_service,
        ws_manager=None
    ):
        # AI Clients - Primary: DeepSeek R1 (cost-effective)
        # ChatGPT kept for asset generation (DALL-E) only
        self.chatgpt = ChatGPTClient(openai_api_key)
        self.deepseek = DeepSeekClient(deepseek_api_key)
        
        # Services
        self.cache = cache_manager
        self.godot = godot_service
        self.storage = storage_service
        self.ws_manager = ws_manager  # WebSocket manager for real-time updates
        
        # Agents
        self.asset_manager = AssetManagerAgent(self.chatgpt, storage_service)
        
        logger.info("🤖 Master Orchestrator initialized")
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing orchestrator...")
        # Any initialization needed
        logger.info("✅ Orchestrator ready")
    
    async def shutdown(self):
        """Cleanup"""
        await self.chatgpt.close()
        await self.deepseek.close()
        logger.info("🛑 Orchestrator shutdown")
    
    async def generate_game(
        self,
        project_id: str,
        user_prompt: str,
        user_tier: str = "free",
        db_manager = None
    ) -> Dict[str, Any]:
        """
        Main game generation pipeline
        
        Args:
            project_id: Unique project identifier
            user_prompt: User's game description
            user_tier: User tier (free/premium)
            db_manager: Database manager instance
        
        Returns:
            Complete game data with build URLs
        """
        logger.info(f"🎮 Starting game generation for: {project_id}")
        
        start_time = datetime.utcnow()
        
        try:
            # Update status
            await self._update_status(project_id, "analyzing", "Analyzing your idea...")
            
            # Step 1: Analyze intent and extract game concept (with fallback)
            try:
            game_concept = await self._analyze_intent(user_prompt)
                if not game_concept or not isinstance(game_concept, dict):
                    raise ValueError("Invalid concept returned")
            except Exception as e:
                logger.warning(f"Intent analysis failed, using fallback: {e}")
                game_concept = self._create_fallback_concept(user_prompt)
            await self._log_step(db_manager, project_id, "intent_analysis", "success", 
                               ai_model="deepseek-reasoner", metadata=game_concept)
            
            # Step 2: Generate comprehensive game design (with fallback)
            await self._update_status(project_id, "designing", "Designing your game...")
            try:
            game_design = await self._generate_game_design(game_concept, user_prompt)
                if not game_design or not isinstance(game_design, dict):  
                    raise ValueError("Invalid design returned")
                # Merge with concept to ensure we have all fields
                game_design = {**game_concept, **game_design}
            except Exception as e:
                logger.warning(f"Game design generation failed, using fallback: {e}")
                game_design = self._create_fallback_design(game_concept, user_prompt)
            await self._log_step(db_manager, project_id, "game_design", "success",
                               ai_model="deepseek-reasoner", metadata=game_design)
            
            # Step 3: Generate game mechanics and rules (with fallback)
            await self._update_status(project_id, "mechanics", "Creating game mechanics...")
            try:
            game_mechanics = await self._generate_game_mechanics(game_design)
                if not game_mechanics or not isinstance(game_mechanics, dict):
                    raise ValueError("Invalid mechanics returned")
            except Exception as e:
                logger.warning(f"Mechanics generation failed, using fallback: {e}")
                game_mechanics = self._create_fallback_mechanics(game_design)
            await self._log_step(db_manager, project_id, "game_mechanics", "success",
                               ai_model="deepseek-reasoner", metadata=game_mechanics)
            
            # Step 4: Generate GDScript code
            # Note: Actual scripts are generated by GodotService using GDScriptGenerator
            # This step just validates/prepares the structure
            await self._update_status(project_id, "coding", "Writing game code...")
            # This should never fail - _generate_game_code always returns a valid dict
            game_scripts = await self._generate_game_code(game_design, game_mechanics)
            # Validate it's a dict (should always be true)
            if not isinstance(game_scripts, dict):
                logger.error("CRITICAL: _generate_game_code returned non-dict, this should never happen!")
                game_scripts = {"scripts_generated_by": "godot_service", "custom_scripts": {}}
            await self._log_step(db_manager, project_id, "code_generation", "success",
                               ai_model="deepseek-reasoner")
            
            # Step 5: Generate game assets (with fallback)
            await self._update_status(project_id, "assets", "Creating game assets...")
            try:
                game_assets = await self.asset_manager.generate_assets(game_design, user_tier, self.deepseek)
                if not game_assets or not isinstance(game_assets, list):
                    raise ValueError("Invalid assets returned")
            except Exception as e:
                logger.warning(f"Asset generation failed, using fallback: {e}")
                game_assets = self.asset_manager._generate_fallback_assets(game_design)
            await self._log_step(db_manager, project_id, "asset_generation", "success",
                               ai_model="dall-e-3" if user_tier == "premium" else "procedural")
            
            # Step 6: Generate UI design (with fallback)
            await self._update_status(project_id, "ui", "Designing user interface...")
            try:
            ui_design = await self._generate_ui_design(game_design)
                if not ui_design or not isinstance(ui_design, dict):
                    raise ValueError("Invalid UI design returned")
            except Exception as e:
                logger.warning(f"UI design generation failed, using fallback: {e}")
                ui_design = self._create_fallback_ui_design(game_design)
            await self._log_step(db_manager, project_id, "ui_design", "success",
                               ai_model="deepseek-reasoner")
            
            # Step 7: Generate level design (with fallback)
            await self._update_status(project_id, "levels", "Building game levels...")
            try:
            level_design = await self._generate_level_design(game_design, game_mechanics)
                if not level_design or not isinstance(level_design, dict):
                    raise ValueError("Invalid level design returned")
            except Exception as e:
                logger.warning(f"Level design generation failed, using fallback: {e}")
                level_design = self._create_fallback_level_design(game_design)
            await self._log_step(db_manager, project_id, "level_design", "success",
                               ai_model="deepseek-reasoner")
            
            # Compile all AI-generated content
            ai_content = {
                "game_design": game_design,
                "game_mechanics": game_mechanics,
                "scripts": game_scripts,
                "assets": game_assets,
                "ui_design": ui_design,
                "level_design": level_design
            }
            
            # Step 8: Build with Godot Engine
            if not self.godot:
                await self._update_status(project_id, "building", "Godot not available - skipping build...")
                build_result = {
                    "success": False,
                    "error": "Godot Engine not installed. Please install Godot and set GODOT_PATH in .env",
                    "builds": {},
                    "web_preview_url": None
                }
            else:
            await self._update_status(project_id, "building", "Building your game with Godot...")
            build_result = await self.godot.build_game_from_ai_content(
                project_id,
                ai_content,
                    self.storage,
                    self.deepseek  # Pass DeepSeek client for AI code generation
            )
            
            if not build_result.get('success'):
                logger.warning(f"⚠️  Game build failed or skipped: {build_result.get('error')}")
                # Continue anyway - AI content is still saved
            
            await self._log_step(db_manager, project_id, "godot_build", "success",
                               metadata=build_result)
            
            # Step 9: Validate game content before saving
            validation_errors = await self._validate_game_content(ai_content, build_result)
            if validation_errors:
                logger.warning(f"⚠️  Validation warnings for {project_id}: {validation_errors}")
                # Continue anyway, but log warnings
            
            # Step 10: Save to database
            if db_manager:
                await db_manager.update_project(
                    project_id,
                    status="completed",
                    ai_content=ai_content,
                    completed_at=datetime.utcnow()
                )
                
                # Save build information
                for platform, url in build_result.get('builds', {}).items():
                    await db_manager.create_build(
                        project_id,
                        platform,
                        url,
                        web_preview_url=build_result.get('web_preview_url'),
                        status="completed"
                    )
            
            # Final status update
            await self._update_status(project_id, "completed", "Your game is ready!")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Game generated successfully in {duration:.2f}s: {project_id}")
            
            return {
                "success": True,
                "project_id": project_id,
                "ai_content": ai_content,
                "builds": build_result.get('builds', {}),
                "web_preview_url": build_result.get('web_preview_url'),
                "duration_seconds": duration,
                "timestamp": datetime.utcnow().isoformat(),
                "validation_warnings": validation_errors if validation_errors else []
            }
            
        except Exception as e:
            logger.error(f"❌ Game generation failed for {project_id}: {e}", exc_info=True)
            
            # Try to generate a minimal working game even on failure
            try:
                logger.info("🔄 Attempting to generate minimal fallback game...")
                await self._update_status(project_id, "recovering", "Recovering from error, generating basic game...")
                
                # Create minimal fallback content
                fallback_concept = self._create_fallback_concept(user_prompt)
                fallback_design = self._create_fallback_design(fallback_concept, user_prompt)
                fallback_mechanics = self._create_fallback_mechanics(fallback_design)
                fallback_scripts = self._create_fallback_scripts(fallback_design, fallback_mechanics)
                fallback_assets = self.asset_manager._generate_fallback_assets(fallback_design)
                fallback_ui = self._create_fallback_ui_design(fallback_design)
                fallback_levels = self._create_fallback_level_design(fallback_design)
                
                ai_content = {
                    "game_design": fallback_design,
                    "game_mechanics": fallback_mechanics,
                    "scripts": fallback_scripts,
                    "assets": fallback_assets,
                    "ui_design": fallback_ui,
                    "level_design": fallback_levels
                }
                
                # Try to build even with fallback content
                build_result = {"success": False, "builds": {}, "web_preview_url": None, "error": "Fallback mode"}
                if self.godot:
                    try:
                        build_result = await self.godot.build_game_from_ai_content(
                            project_id, ai_content, self.storage, self.deepseek
                        )
                    except Exception as build_error:
                        logger.warning(f"Fallback build also failed: {build_error}")
                
                # Save fallback content
                if db_manager:
                    await db_manager.update_project(
                        project_id,
                        status="completed",
                        ai_content=ai_content,
                        completed_at=datetime.utcnow()
                    )
                
                await self._update_status(project_id, "completed", "Generated basic game (recovery mode)")
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"✅ Fallback game generated in {duration:.2f}s: {project_id}")
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "ai_content": ai_content,
                    "builds": build_result.get('builds', {}),
                    "web_preview_url": build_result.get('web_preview_url'),
                    "duration_seconds": duration,
                    "timestamp": datetime.utcnow().isoformat(),
                    "recovery_mode": True,
                    "original_error": str(e)
                }
                
            except Exception as recovery_error:
                logger.error(f"❌ Recovery also failed: {recovery_error}", exc_info=True)
            await self._update_status(project_id, "failed", f"Generation failed: {str(e)}")
            
            if db_manager:
                await db_manager.update_project(project_id, status="failed")
                await self._log_step(db_manager, project_id, "generation", "failed", error=str(e))
            
            return {
                "success": False,
                "project_id": project_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_intent(self, user_prompt: str) -> Dict:
        """Step 1: Analyze user intent and extract game concept - Using DeepSeek R1"""
        
        # Game reference knowledge for popular games
        game_references = """
Popular Game References:
- Subway Surfers: Endless runner, swipe controls (left/right/up/down), collect coins, avoid obstacles, colorful 3D style, fast-paced
- Temple Run: Endless runner, tilt/swipe controls, collect coins, power-ups, jungle theme, dynamic camera
- Flappy Bird: Simple tap-to-jump, avoid pipes, pixel art, high score challenge
- Candy Crush: Match-3 puzzle, colorful candies, level-based progression, power-ups
- Angry Birds: Physics-based slingshot, destroy structures, colorful cartoon style
- Super Mario: Platformer, jump and run, collect coins, defeat enemies, power-ups (mushroom, fire flower)
- Sonic: Fast platformer, speed-based, collect rings, loop-de-loops, colorful
- Pac-Man: Maze game, collect dots, avoid ghosts, power pellets
- Tetris: Falling blocks puzzle, line clearing, increasing speed
- Crossy Road: Endless hopper, tap to move forward, avoid traffic, pixel art style
"""
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a game design expert with deep knowledge of popular games. Analyze the user's game idea and extract key concepts.

{game_references}

User's game request: {user_prompt}

IMPORTANT: If the user references a popular game (like "like Subway Surfers", "similar to Temple Run", "inspired by Flappy Bird"), extract the core mechanics, visual style, and gameplay feel of that game.

Return a JSON object with:
- genre: Game genre (platformer, puzzle, rpg, shooter, endless_runner, etc.)
- dimension: "2D" or "3D" - CRITICAL RULES:
  * If user mentions "2D", "2d", "two dimensional", "pixel art", "side-scrolling", set to "2D"
  * If user mentions "3D", "3d", "three dimensional", or references 3D games like Subway Surfers, set to "3D"
  * If user mentions "4D", "4d", "5D", "5d", or any higher dimension, convert to "3D" (we only support 2D and 3D)
  * Default to "2D" if unclear
- theme: Visual/story theme
- target_audience: Who is this for
- core_mechanic: Main gameplay mechanic (be specific - e.g., "endless running with swipe controls" not just "running")
- referenced_game: Name of popular game if mentioned (null if none)
- game_style: Visual style to match (e.g., "colorful 3D like Subway Surfers", "pixel art like Flappy Bird")
- difficulty: easy, medium, hard
- estimated_scope: small (this is a starter/kickoff game, not full scale)
- key_features: List of 3-5 key features that make this game unique or match the referenced game"""
            }
        ]
        
        response = await self.deepseek.generate(messages, temperature=0.5)
        
        try:
            # Parse JSON from response
            content = response['content']
            # Extract JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            concept = json.loads(content)
            
            # Normalize dimension: Convert 4D/5D to 3D, ensure 2D/3D only
            dimension = concept.get('dimension', '2D')
            if isinstance(dimension, str):
                dimension_upper = dimension.upper()
                if '4D' in dimension_upper or '5D' in dimension_upper or dimension_upper in ['4', '5', '6', '7', '8', '9']:
                    logger.info(f"Converting {dimension} to 3D (only 2D and 3D supported)")
                    concept['dimension'] = '3D'
                elif dimension_upper in ['2D', '2']:
                    concept['dimension'] = '2D'
                elif dimension_upper in ['3D', '3']:
                    concept['dimension'] = '3D'
                else:
                    # Default to 2D if unclear
                    concept['dimension'] = '2D'
            else:
                concept['dimension'] = '2D'
            
            # Ensure scope is small (starter game)
            concept['estimated_scope'] = 'small'
            
            return concept
        except Exception as e:
            logger.warning(f"Intent analysis error: {e}, using fallback")
            return self._create_fallback_concept(user_prompt)
    
    def _create_fallback_concept(self, user_prompt: str) -> Dict:
        """Create a fallback game concept from user prompt"""
        prompt_lower = user_prompt.lower()
        
        # Detect dimension
        dimension = "2D"
        if any(word in prompt_lower for word in ["3d", "3-d", "three dimensional", "subway", "temple run"]):
            dimension = "3D"
        elif any(word in prompt_lower for word in ["2d", "2-d", "two dimensional", "pixel", "side-scrolling"]):
            dimension = "2D"
        
        # Detect genre
        genre = "platformer"
        if "runner" in prompt_lower:
            genre = "endless_runner"
        elif "puzzle" in prompt_lower:
            genre = "puzzle"
        elif "shooter" in prompt_lower or "shoot" in prompt_lower:
            genre = "shooter"
        
            return {
            "genre": genre,
            "dimension": dimension,
                "theme": "adventure",
                "target_audience": "casual gamers",
            "core_mechanic": "jump and collect" if genre == "platformer" else "run and avoid",
                "difficulty": "medium",
            "estimated_scope": "small",
            "referenced_game": None,
            "game_style": "colorful and fun",
            "key_features": ["smooth controls", "collectibles", "progressive difficulty"]
            }
    
    async def _generate_game_design(self, concept: Dict, prompt: str) -> Dict:
        """Step 2: Generate detailed game design - Using DeepSeek R1"""
        
        referenced_game = concept.get('referenced_game')
        game_style = concept.get('game_style', '')
        key_features = concept.get('key_features', [])
        
        style_guidance = ""
        if referenced_game:
            style_guidance = f"""
CRITICAL: The user wants a game like "{referenced_game}". You MUST create a design that:
1. Matches the visual style and color palette of {referenced_game}
2. Uses similar gameplay mechanics and feel
3. Has the same level of polish and refinement
4. Creates a game that looks and plays like {referenced_game}

Key features to include: {', '.join(key_features) if key_features else 'Match the referenced game style'}
"""
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a professional game designer specializing in creating polished, refined games that match popular game styles.

Game concept: {json.dumps(concept)}
                
Original prompt: {prompt}

{style_guidance}

Return JSON with:
- title: Catchy game title that matches the style
- description: 2-3 sentence description emphasizing the gameplay feel
- genre: Game genre
- art_style: Visual style that matches the referenced game (e.g., "colorful 3D cartoon like Subway Surfers", "retro pixel art like Flappy Bird")
- color_scheme: Color palette matching the referenced game style (use hex codes)
- player_description: Detailed description of player character matching the visual style
- enemy_description: What enemies/obstacles look like (match the style)
- environment_description: Game world description matching the referenced game's environment
- win_condition: How to win (match the referenced game's win condition if applicable)
- lose_condition: How to lose (match the referenced game's lose condition)
- gameplay_loop: Core gameplay loop description (e.g., "Run forward, swipe to dodge obstacles, collect coins, avoid enemies")
- visual_effects: List of visual effects to include (particles, animations, etc.)

Create a REFINED game design that looks and plays like the referenced game:"""
            }
        ]
        
        response = await self.deepseek.generate(messages, max_tokens=2000, temperature=0.6)
        
        try:
            content = response['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            design = json.loads(content)
            return design
        except:
            return {
                "title": "Gamora AI Game",
                "description": prompt[:200],
                "genre": concept.get("genre", "platformer"),
                "art_style": "pixel art",
                "color_scheme": {"primary": "#4A90E2", "secondary": "#50C878"},
                "player_description": "A heroic character",
                "environment_description": "A colorful game world"
            }
    
    async def _generate_game_mechanics(self, design: Dict) -> Dict:
        """Step 3: Generate game mechanics with DeepSeek"""
        
        gameplay_loop = design.get('gameplay_loop', '')
        genre = design.get('genre', 'platformer')
        
        # Add specific mechanics guidance based on genre
        mechanics_guidance = ""
        if 'endless_runner' in genre.lower() or 'runner' in genre.lower():
            mechanics_guidance = """
For endless runner games (like Subway Surfers, Temple Run):
- player_movement: speed should be 400-600 (fast forward movement), jump_force around -500, acceleration 2000+
- Add lane_switching: true (left/right movement between lanes)
- Add swipe_controls: true (up=jump, down=slide, left/right=switch lanes)
- obstacles: Should spawn dynamically, move toward player
- collectibles: Coins/items spawn in lanes, need to collect while avoiding obstacles
- progression: Speed increases over time, obstacles spawn more frequently
- camera: Follows player, moves forward automatically
"""
        elif 'platformer' in genre.lower():
            mechanics_guidance = """
For platformer games (like Super Mario, Sonic):
- player_movement: speed 300-400, jump_force -400 to -500, smooth acceleration/friction
- Add wall_jump: false (can enable for advanced platformers)
- Add double_jump: false (can enable for advanced platformers)
- obstacles: Static platforms, moving platforms, spikes
- collectibles: Coins, gems, power-ups scattered on platforms
- progression: Level-based, increasing difficulty
"""
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a game mechanics designer. Create REFINED, POLISHED game mechanics that match the style and feel of popular games.

Game: {design.get('title', 'Game')}
Genre: {genre}
Description: {design.get('description', '')}
Gameplay Loop: {gameplay_loop}
Art Style: {design.get('art_style', '')}

{mechanics_guidance}

Return JSON with REFINED mechanics:
- player_movement: {{speed: float (300-600 based on game type), jump_force: float (-400 to -600), acceleration: float (1500-2500), friction: float (1000-1500), max_fall_speed: float}}
- player_abilities: List of abilities (e.g., ["jump", "move", "slide", "lane_switch"] for runners)
- enemy_behaviors: List of enemy patterns matching the game style
- collectibles: List with types, values, spawn rates (e.g., [{{"type": "coin", "value": 10, "spawn_rate": 0.3}}])
- power_ups: List of power-ups matching the game style
- obstacles: List of obstacles with descriptions
- game_rules: Core rules that define gameplay
- scoring_system: Detailed scoring (points per item, multipliers, combos)
- progression: How difficulty/pace increases
- camera_behavior: How camera follows player (for runners: "forward_follow", for platformers: "smooth_follow")
- lane_system: For runners, number of lanes (usually 3)
- spawn_system: How obstacles/collectibles spawn (for runners: "continuous_forward", for platformers: "static_placement")

Make mechanics REFINED and match the polished feel of popular games:"""
            }
        ]
        
        response = await self.deepseek.generate(messages, temperature=0.3)
        
        try:
            content = response['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            mechanics = json.loads(content)
            return mechanics
        except:
            return {
                "player_movement": {
                    "speed": 300.0,
                    "jump_force": -400.0,
                    "acceleration": 1500.0,
                    "friction": 1200.0
                },
                "player_abilities": ["jump", "move"],
                "game_rules": ["Collect items", "Avoid obstacles"],
                "scoring_system": "Points per item collected"
            }
    
    async def _generate_game_code(self, design: Dict, mechanics: Dict) -> Dict:
        """Step 4: Generate GDScript code using AI with hybrid approach"""
        
        # Use AI to generate code directly, but return structure for GodotService
        # GodotService will use AICodeGenerator which has AI + fallback templates
        try:
            # Return structure indicating AI-powered generation
            return {
                "scripts_generated_by": "ai_with_fallback",
                "use_ai": True,  # Flag to use AI generation
                "game_design": design,
                "game_mechanics": mechanics,
                "custom_scripts": {},
                "status": "ready_for_ai_generation"
            }
        except Exception as e:
            logger.error(f"Unexpected error in _generate_game_code: {e}", exc_info=True)
            return {
                "scripts_generated_by": "template_fallback",
                "use_ai": False,  # Fallback to templates
                "custom_scripts": {},
                "status": "ready_for_godot_generation",
                "error": str(e)
            }
    
    async def _generate_ui_design(self, design: Dict) -> Dict:
        """Step 6: Generate UI design with AI-powered detailed layouts"""
        
        genre = design.get('genre', 'platformer')
        game_style = design.get('game_style', '')
        referenced_game = design.get('referenced_game', '')
        color_scheme = design.get('color_scheme', {})
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a UI/UX designer for games. Design a REFINED, POLISHED user interface that matches the game's style and genre.

Game Context:
- Title: {design.get('title', 'Game')}
- Genre: {genre}
- Style: {game_style}
- Referenced Game: {referenced_game if referenced_game else 'None'}
- Color Scheme: {json.dumps(color_scheme)}
- Art Style: {design.get('art_style', '')}

Your Task:
Design a complete UI system that:
1. Matches the visual style of the game
2. Is intuitive and easy to use
3. Provides clear feedback to the player
4. Includes all necessary HUD elements
5. Has a cohesive design language
6. Works well for the game genre

Return JSON with:
- menu_style: Style description (e.g., "modern", "retro", "minimalist", "colorful")
- font_style: Font characteristics (e.g., "bold", "rounded", "pixelated")
- font_size: Base font size (number)
- button_style: Button design (e.g., "rounded", "sharp", "gradient", "outlined")
- hud_layout: Object with:
  - score_position: "top_left" | "top_right" | "top_center"
  - health_position: "top_left" | "top_right" | "top_center"
  - health_display: "bar" | "number" | "icons"
  - minimap: true/false
  - power_up_indicators: true/false
- color_theme: Object with:
  - primary: Primary UI color (hex)
  - secondary: Secondary UI color (hex)
  - accent: Accent color (hex)
  - background: Background color/transparency
  - text: Text color (hex)
- ui_elements: Array of UI element objects:
  - type: "button", "label", "panel", "icon"
  - name: Element name
  - position: [x, y] or "top_left", "top_right", etc.
  - size: [width, height]
  - style: Style description
  - animation: Animation type (e.g., "pulse", "slide", "fade")
- menu_screens: Array of menu screen objects:
  - name: "main_menu", "pause_menu", "game_over", "settings"
  - layout: Layout description
  - buttons: Array of button objects with labels and actions
- feedback_effects: Array of visual feedback types (e.g., "score_popup", "damage_flash", "collectible_glow")

Create a REFINED, POLISHED UI design that enhances the gameplay experience:"""
            }
        ]
        
        try:
            response = await self.deepseek.generate(messages, temperature=0.4)
            content = response['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            ui_data = json.loads(content)
            return ui_data
        except Exception as e:
            logger.warning(f"Failed to generate UI design: {e}")
            # Fallback
        return {
            "menu_style": "modern",
            "font_size": 24,
            "button_style": "rounded",
                "color_theme": color_scheme,
                "hud_layout": {
                    "score_position": "top_left",
                    "health_position": "top_left",
                    "health_display": "number"
                }
        }
    
    async def _generate_level_design(self, design: Dict, mechanics: Dict) -> Dict:
        """Step 7: Generate level layouts with AI-powered detailed design"""
        
        genre = design.get('genre', 'platformer')
        gameplay_loop = design.get('gameplay_loop', '')
        referenced_game = design.get('referenced_game', '')
        game_style = design.get('game_style', '')
        dimension = design.get('dimension', '2D')
        
        # For endless runners, generate spawn patterns instead of static levels
        if 'endless_runner' in genre.lower() or 'runner' in genre.lower() or dimension == '3D':
            messages = [
                {
                    "role": "user",
                    "content": f"""Design level/spawn patterns for an endless runner game.

Game: {design.get('title', 'Game')}
Gameplay: {gameplay_loop}
Mechanics: {json.dumps(mechanics.get('obstacles', []))}

Return JSON with:
- spawn_patterns: List of obstacle/collectible patterns that repeat
- lane_configuration: Number of lanes (usually 3)
- difficulty_curve: How spawn rate increases over time
- obstacle_combinations: Common obstacle combinations
- collectible_placement: Where collectibles typically spawn

Create patterns that feel polished and balanced:"""
                }
            ]
            
            try:
                response = await self.deepseek.generate(messages, temperature=0.4)
                content = response['content']
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                level_data = json.loads(content)
                return level_data
            except:
                pass
        
        # For platformers, generate traditional level layouts (MAX 2 levels for starter game)
        messages = [
            {
                "role": "user",
                "content": f"""Design level layouts for a platformer game. This is a STARTER/KICKOFF game, not a full-scale game.

Game: {design.get('title', 'Game')}
Genre: {genre}
Mechanics: {json.dumps(mechanics)}

Return JSON with:
- levels: Array of EXACTLY 2 level objects (starter game, not full scale), each with:
  - name: Level name
  - difficulty: easy/medium (first easy, second can be medium)
  - platforms: Array of platform objects with position [x, y] and size [width, height]
  - enemies: Array of enemy objects with position [x, y] and type
  - collectibles: Array of collectible objects with position [x, y] and type
  - spawn_point: [x, y] for player start
  - goal: [x, y] for level end

IMPORTANT: Generate EXACTLY 2 levels maximum. This is a starter game. Make layouts REFINED, POLISHED, and error-free:"""
            }
        ]
        
        try:
            response = await self.deepseek.generate(messages, temperature=0.4)
            content = response['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            level_data = json.loads(content)
            
            # Limit to maximum 2 levels (starter game)
            if 'levels' in level_data and isinstance(level_data['levels'], list):
                if len(level_data['levels']) > 2:
                    logger.info(f"Limiting levels from {len(level_data['levels'])} to 2 (starter game)")
                    level_data['levels'] = level_data['levels'][:2]
            
            return level_data
        except Exception as e:
            logger.warning(f"Failed to generate level design: {e}")
            # Fallback - exactly 2 levels for starter game
        return {
            "levels": [
                {
                    "name": "Level 1",
                    "difficulty": "easy",
                        "platforms": [[0, 500, 200, 64], [300, 400, 200, 64], [600, 300, 200, 64]],
                        "enemies": [[400, 350]],
                        "collectibles": [[150, 450], [350, 350], [650, 250]],
                        "spawn_point": [100, 400],
                        "goal": [800, 200]
                    },
                    {
                        "name": "Level 2",
                        "difficulty": "medium",
                        "platforms": [[0, 500, 200, 64], [250, 400, 200, 64], [500, 300, 200, 64], [750, 200, 200, 64]],
                        "enemies": [[350, 350], [600, 250]],
                        "collectibles": [[100, 450], [300, 350], [550, 250], [800, 150]],
                        "spawn_point": [100, 400],
                        "goal": [900, 150]
                }
            ]
        }
    
    async def _update_status(self, project_id: str, status: str, message: str):
        """Update generation status and notify via WebSocket"""
        logger.info(f"[{project_id}] {status}: {message}")
        
        # Update cache
        await self.cache.set_generation_status(
            project_id,
            {
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send WebSocket update if manager is available
        if self.ws_manager:
            await self.ws_manager.send_message(project_id, {
                "type": "progress",
                "data": {
                "status": status,
                "message": message
                }
            })
    
    async def _validate_game_content(self, ai_content: Dict, build_result: Dict) -> List[str]:
        """Validate game content for errors and issues before completion
        
        Returns:
            List of error/warning messages (empty if all good)
        """
        
        errors = []
        warnings = []
        
        # Check game design
        game_design = ai_content.get('game_design', {})
        if not game_design:
            errors.append("Missing game_design")
        else:
            if not game_design.get('title'):
                warnings.append("Game title is missing")
            if not game_design.get('genre'):
                warnings.append("Game genre is missing")
            dimension = game_design.get('dimension', '2D')
            if dimension not in ['2D', '3D']:
                errors.append(f"Invalid dimension: {dimension} (must be 2D or 3D)")
                # Auto-fix: convert to 3D if invalid
                if dimension and ('4' in str(dimension) or '5' in str(dimension)):
                    game_design['dimension'] = '3D'
                    logger.info(f"Auto-fixed dimension from {dimension} to 3D")
                else:
                    game_design['dimension'] = '2D'
        
        # Check level design - limit to 2 levels
        level_design = ai_content.get('level_design', {})
        if 'levels' in level_design:
            levels = level_design['levels']
            if not isinstance(levels, list):
                errors.append("Levels must be an array")
            elif len(levels) > 2:
                warnings.append(f"Too many levels ({len(levels)}), limiting to 2 for starter game")
                level_design['levels'] = levels[:2]
            elif len(levels) == 0:
                warnings.append("No levels generated")
        
        # Check game mechanics
        game_mechanics = ai_content.get('game_mechanics', {})
        if not game_mechanics:
            warnings.append("Missing game_mechanics")
        else:
            player_movement = game_mechanics.get('player_movement', {})
            if player_movement:
                speed = player_movement.get('speed', 0)
                if speed <= 0 or speed > 1000:
                    warnings.append(f"Player speed seems invalid: {speed}")
                    # Auto-fix: set reasonable default
                    if speed <= 0:
                        player_movement['speed'] = 300.0
                    elif speed > 1000:
                        player_movement['speed'] = 600.0
        
        # Check build result
        if not build_result.get('success'):
            error_msg = build_result.get('error', 'Unknown build error')
            warnings.append(f"Build had issues: {error_msg}")
        
        # Check assets
        assets = ai_content.get('assets', [])
        if not assets or len(assets) == 0:
            warnings.append("No assets generated")
        
        # Log errors and warnings
        if errors:
            logger.error(f"❌ Validation errors: {errors}")
        if warnings:
            logger.warning(f"⚠️  Validation warnings: {warnings}")
        
        return errors + warnings
    
    def _create_fallback_design(self, concept: Dict, prompt: str) -> Dict:
        """Create fallback game design that matches user intent"""
        genre = concept.get('genre', 'platformer')
        dimension = concept.get('dimension', '2D')
        theme = concept.get('theme', 'adventure')
        
        return {
            "title": f"{genre.title()} Adventure",
            "description": prompt[:200] if prompt else f"A fun {genre} game",
            "genre": genre,
            "dimension": dimension,
            "art_style": "colorful and polished" if dimension == "3D" else "pixel art",
            "color_scheme": {
                "primary": "#4A90E2" if dimension == "2D" else "#5CB3FF",
                "secondary": "#FFD700",
                "background": "#2C3E50" if dimension == "2D" else "#87CEEB",
                "accent": "#FF6464"
            },
            "player_description": "A heroic character ready for adventure",
            "enemy_description": "Challenging obstacles to overcome",
            "environment_description": f"A {theme} world full of adventure",
            "win_condition": "Complete all levels",
            "lose_condition": "Health reaches zero",
            "gameplay_loop": "Move, jump, collect items, avoid enemies",
            "visual_effects": ["particles", "animations", "screen shake"],
            "referenced_game": concept.get('referenced_game'),
            "game_style": concept.get('game_style', 'colorful and fun'),
            "key_features": concept.get('key_features', [])
        }
    
    def _create_fallback_mechanics(self, design: Dict) -> Dict:
        """Create fallback game mechanics"""
        genre = design.get('genre', 'platformer')
        dimension = design.get('dimension', '2D')
        
        if 'runner' in genre.lower():
            return {
                "player_movement": {
                    "speed": 400.0,
                    "jump_force": -500.0,
                    "acceleration": 2000.0,
                    "friction": 1500.0,
                    "max_fall_speed": 800.0
                },
                "player_abilities": ["jump", "move", "slide", "lane_switch"],
                "enemy_behaviors": ["static_obstacle", "moving_obstacle"],
                "collectibles": [{"type": "coin", "value": 10, "spawn_rate": 0.3}],
                "power_ups": [],
                "obstacles": ["barrier", "hole"],
                "game_rules": ["Run forward", "Avoid obstacles", "Collect coins"],
                "scoring_system": {"coin": 10, "distance": 1},
                "progression": "Speed increases over time",
                "camera_behavior": "forward_follow",
                "lane_system": 3,
                "spawn_system": "continuous_forward"
            }
        else:
            return {
                "player_movement": {
                    "speed": 300.0,
                    "jump_force": -400.0,
                    "acceleration": 1500.0,
                    "friction": 1200.0,
                    "max_fall_speed": 600.0
                },
                "player_abilities": ["jump", "move"],
                "enemy_behaviors": ["patrol", "chase"],
                "collectibles": [{"type": "coin", "value": 10, "spawn_rate": 0.2}],
                "power_ups": [],
                "obstacles": ["spike", "platform"],
                "game_rules": ["Move and jump", "Collect items", "Avoid enemies"],
                "scoring_system": {"coin": 10},
                "progression": "Level-based difficulty increase",
                "camera_behavior": "smooth_follow",
                "spawn_system": "static_placement"
            }
    
    def _create_fallback_scripts(self, design: Dict, mechanics: Dict) -> Dict:
        """Create fallback game scripts using the script generator"""
        try:
            from services.gdscript_generator import GDScriptGenerator
            generator = GDScriptGenerator()
            scripts = generator.generate_all_scripts(design, mechanics)
            logger.info(f"✅ Generated {len(scripts)} fallback scripts using GDScriptGenerator")
            return scripts
        except Exception as e:
            logger.error(f"Failed to generate fallback scripts with generator: {e}", exc_info=True)
            # Return a valid dict structure (scripts will be generated by GodotService)
            return {
                "scripts_generated_by": "godot_service_fallback",
                "custom_scripts": {},
                "note": "Scripts will be generated by GodotService using GDScriptGenerator"
            }
    
    def _create_fallback_ui_design(self, design: Dict) -> Dict:
        """Create fallback UI design"""
        return {
            "menu_style": "modern",
            "font_size": 24,
            "button_style": "rounded",
            "color_theme": {
                "primary": design.get('color_scheme', {}).get('primary', '#4A90E2') if isinstance(design.get('color_scheme'), dict) else '#4A90E2',
                "secondary": "#FFD700",
                "accent": "#FF6464",
                "background": "transparent",
                "text": "#FFFFFF"
            },
            "hud_layout": {
                "score_position": "top_left",
                "health_position": "top_left",
                "health_display": "number"
            },
            "ui_elements": [],
            "menu_screens": [],
            "feedback_effects": ["score_popup"]
        }
    
    def _create_fallback_level_design(self, design: Dict) -> Dict:
        """Create fallback level design (2 levels for starter game)"""
        dimension = design.get('dimension', '2D')
        genre = design.get('genre', 'platformer')
        
        if 'runner' in genre.lower() or dimension == '3D':
            return {
                "spawn_patterns": [
                    {"obstacle_type": "barrier", "spawn_rate": 0.3, "lane": "random"},
                    {"obstacle_type": "hole", "spawn_rate": 0.2, "lane": "random"}
                ],
                "collectible_placement": "scattered",
                "lane_configuration": 3,
                "difficulty_curve": "gradual"
            }
        else:
            return {
                "levels": [
                    {
                        "name": "Level 1",
                        "difficulty": "easy",
                        "platforms": [[0, 500, 200, 64], [300, 400, 200, 64], [600, 300, 200, 64]],
                        "enemies": [[400, 350]],
                        "collectibles": [[150, 450], [350, 350], [650, 250]],
                        "spawn_point": [100, 400],
                        "goal": [800, 200]
                    },
                    {
                        "name": "Level 2",
                        "difficulty": "medium",
                        "platforms": [[0, 500, 200, 64], [250, 400, 200, 64], [500, 300, 200, 64], [750, 200, 200, 64]],
                        "enemies": [[350, 350], [600, 250]],
                        "collectibles": [[100, 450], [300, 350], [550, 250], [800, 150]],
                        "spawn_point": [100, 400],
                        "goal": [900, 150]
                    }
                ]
            }
    
    async def _log_step(
        self,
        db_manager,
        project_id: str,
        step: str,
        status: str,
        **kwargs
    ):
        """Log generation step to database"""
        if db_manager:
            await db_manager.log_generation_step(
                project_id,
                step,
                status,
                **kwargs
            )
