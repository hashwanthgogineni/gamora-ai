"""
AI-Powered Code Generator
Uses AI to generate GDScript code directly with smart prompts, validation, and fallbacks
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
from services.gdscript_generator import GDScriptGenerator  # Fallback

logger = logging.getLogger(__name__)


class AICodeGenerator:
    """
    Hybrid AI code generator:
    - Uses AI to generate unique, flexible code for each game
    - Includes best practices in prompts
    - Validates and repairs AI output
    - Falls back to templates if AI fails
    """
    
    def __init__(self, deepseek_client):
        self.deepseek = deepseek_client
        self.fallback_generator = GDScriptGenerator()  # Template-based fallback
    
    async def generate_all_scripts(
        self,
        game_design: Dict[str, Any],
        game_mechanics: Dict[str, Any],
        use_ai: bool = True
    ) -> Dict[str, str]:
        """
        Generate all game scripts using AI with fallback to templates
        
        Args:
            game_design: Complete game design from AI
            game_mechanics: Game mechanics from AI
            use_ai: If True, use AI generation. If False, use templates only.
        
        Returns:
            Dictionary mapping script paths to script content
        """
        
        dimension = game_design.get('dimension', '2D')
        genre = game_design.get('genre', 'platformer')
        is_3d = dimension == '3D' or '3d' in genre.lower()
        
        if is_3d:
            player_script_path = "scripts/player/player_3d.gd"
            camera_script_path = "scripts/camera_controller_3d.gd"
        else:
            player_script_path = "scripts/player/player.gd"
            camera_script_path = "scripts/camera_controller.gd"
        
        scripts = {}
        
        if use_ai:
            try:
                logger.info("🤖 Using AI to generate unique game code...")
                
                # Generate all scripts with AI
                ai_scripts = await self._generate_scripts_with_ai(
                    game_design,
                    game_mechanics,
                    is_3d
                )
                
                if ai_scripts and len(ai_scripts) > 0:
                    # Validate AI-generated scripts
                    validated_scripts = self._validate_and_repair_scripts(ai_scripts, game_design)
                    scripts.update(validated_scripts)
                    logger.info(f"✅ AI generated {len(scripts)} scripts")
                else:
                    raise ValueError("AI returned empty scripts")
                    
            except Exception as e:
                logger.warning(f"⚠️  AI code generation failed: {e}, using template fallback")
                use_ai = False
        
        # Fallback to templates if AI failed or was disabled
        if not use_ai or len(scripts) == 0:
            logger.info("📝 Using template-based code generation (fallback)")
            template_scripts = self.fallback_generator.generate_all_scripts(
                game_design,
                game_mechanics
            )
            scripts.update(template_scripts)
        
        # Ensure we have all required scripts
        required_scripts = {
            player_script_path: scripts.get(player_script_path),
            "scripts/managers/game_manager.gd": scripts.get("scripts/managers/game_manager.gd"),
            "scripts/items/collectible.gd": scripts.get("scripts/items/collectible.gd"),
            camera_script_path: scripts.get(camera_script_path),
            "scripts/enemies/enemy.gd": scripts.get("scripts/enemies/enemy.gd"),
            "scripts/managers/ui_manager.gd": scripts.get("scripts/managers/ui_manager.gd")
        }
        
        # Fill missing scripts with fallback
        for script_path, script_content in required_scripts.items():
            if not script_content or len(script_content.strip()) == 0:
                logger.warning(f"⚠️  Missing script {script_path}, generating fallback")
                if script_path == player_script_path:
                    required_scripts[script_path] = self.fallback_generator.generate_player_script(
                        game_mechanics, game_design
                    )
                elif "game_manager" in script_path:
                    required_scripts[script_path] = self.fallback_generator.generate_game_manager_script(
                        game_mechanics, game_design
                    )
                elif "collectible" in script_path:
                    required_scripts[script_path] = self.fallback_generator.generate_collectible_script(
                        game_mechanics
                    )
                elif "camera" in script_path:
                    required_scripts[script_path] = self.fallback_generator.generate_camera_controller_script(
                        game_design
                    )
                elif "enemy" in script_path:
                    required_scripts[script_path] = self.fallback_generator.generate_enemy_script(
                        game_mechanics
                    )
                elif "ui_manager" in script_path:
                    # UI manager is optional, create a basic one if missing
                    required_scripts[script_path] = """extends Node

func update_score(score: int):
    var label = get_node_or_null("UI/ScoreLabel")
    if label:
        label.text = "Score: " + str(score)

func update_health(health: int):
    var label = get_node_or_null("UI/HealthLabel")
    if label:
        label.text = "Health: " + str(health)
"""
        
        return required_scripts
    
    async def _generate_scripts_with_ai(
        self,
        game_design: Dict[str, Any],
        game_mechanics: Dict[str, Any],
        is_3d: bool
    ) -> Dict[str, str]:
        """Generate all GDScript files using AI with comprehensive prompts"""
        
        dimension = "3D" if is_3d else "2D"
        genre = game_design.get('genre', 'platformer')
        title = game_design.get('title', 'Game')
        
        # Build comprehensive prompt with best practices
        prompt = f"""You are an expert Godot game developer. Generate COMPLETE, WORKING GDScript code for a {dimension} {genre} game.

GAME CONTEXT:
- Title: {title}
- Genre: {genre}
- Dimension: {dimension}
- Game Style: {game_design.get('game_style', '')}
- Referenced Game: {game_design.get('referenced_game', 'None')}

GAME MECHANICS:
{json.dumps(game_mechanics, indent=2)}

GAME DESIGN:
{json.dumps({k: v for k, v in game_design.items() if k not in ['assets', 'scripts']}, indent=2)}

REQUIREMENTS:
1. Generate COMPLETE, WORKING GDScript code (not pseudocode)
2. Use professional game development patterns
3. Include proper error handling
4. Use signals for decoupled communication
5. Implement proper physics and collision detection
6. Add visual feedback (animations, effects)
7. Make controls responsive and polished
8. Include proper state management
9. Use groups for object identification
10. Add proper cleanup and memory management

SCRIPT STRUCTURE:
Generate a JSON object with these script paths as keys and complete GDScript code as values:
{{
  "scripts/player/{"player_3d.gd" if is_3d else "player.gd"}": "complete player controller code",
  "scripts/managers/game_manager.gd": "complete game manager code",
  "scripts/items/collectible.gd": "complete collectible code",
  "scripts/camera_controller{"_3d" if is_3d else ""}.gd": "complete camera controller code",
  "scripts/enemies/enemy.gd": "complete enemy AI code",
  "scripts/managers/ui_manager.gd": "complete UI manager code"
}}

IMPORTANT:
- Each script must be COMPLETE and WORKING
- Use proper GDScript syntax
- Include all necessary extends, signals, constants, variables
- Implement all required functions
- Make code REFINED and POLISHED
- Handle edge cases
- Add comments for complex logic

Generate code that matches the game's style and mechanics exactly. Be creative but ensure it works!"""

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await self.deepseek.generate(
                messages,
                temperature=0.7,  # Higher temperature for creativity
                max_tokens=8000  # Large token limit for complete code
            )
            
            content = response.get('content', '')
            
            # Extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
                    if content.startswith("json"):
                        content = content[4:].strip()
            
            # Try to find JSON object in content
            if not content.startswith('{'):
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
            
            # Repair JSON if needed
            content = self._repair_json(content)
            
            scripts_dict = json.loads(content)
            
            if not isinstance(scripts_dict, dict):
                raise ValueError("AI response is not a dictionary")
            
            logger.info(f"✅ AI generated {len(scripts_dict)} scripts")
            return scripts_dict
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            # Try aggressive repair
            try:
                repaired = self._repair_json_aggressive(content)
                scripts_dict = json.loads(repaired)
                if isinstance(scripts_dict, dict):
                    logger.info("✅ Repaired and parsed AI response")
                    return scripts_dict
            except:
                pass
            raise ValueError(f"Could not parse AI response: {e}")
        except Exception as e:
            logger.error(f"AI code generation failed: {e}", exc_info=True)
            raise
    
    def _repair_json(self, content: str) -> str:
        """Repair common JSON issues"""
        if not content:
            return "{}"
        
        content = content.strip()
        
        # Balance braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces > close_braces:
            content += '}' * (open_braces - close_braces)
        
        # Remove trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        return content
    
    def _repair_json_aggressive(self, content: str) -> str:
        """Aggressively repair broken JSON"""
        if not content:
            return "{}"
        
        # Try to extract script paths and code blocks
        # Look for patterns like "scripts/player/player.gd": "code here"
        script_pattern = r'"scripts/[^"]+\.gd"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'
        matches = re.findall(script_pattern, content, re.DOTALL)
        
        if matches:
            # Try to reconstruct JSON
            repaired = "{"
            # This is a simplified repair - in production, use a more robust approach
            return content
        
        return self._repair_json(content)
    
    def _validate_and_repair_scripts(
        self,
        scripts: Dict[str, str],
        game_design: Dict[str, Any]
    ) -> Dict[str, str]:
        """Validate and repair AI-generated scripts"""
        
        validated = {}
        
        for script_path, script_content in scripts.items():
            if not script_content or len(script_content.strip()) == 0:
                logger.warning(f"⚠️  Empty script content for {script_path}")
                continue
            
            # Basic validation
            if not script_content.strip().startswith('extends'):
                logger.warning(f"⚠️  Script {script_path} doesn't start with 'extends', attempting repair")
                # Try to add extends if missing
                if 'CharacterBody' in script_path or 'player' in script_path.lower():
                    if '3d' in script_path.lower():
                        script_content = 'extends CharacterBody3D\n\n' + script_content
                    else:
                        script_content = 'extends CharacterBody2D\n\n' + script_content
                elif 'manager' in script_path.lower():
                    script_content = 'extends Node\n\n' + script_content
                elif 'camera' in script_path.lower():
                    if '3d' in script_path.lower():
                        script_content = 'extends Camera3D\n\n' + script_content
                    else:
                        script_content = 'extends Camera2D\n\n' + script_content
                elif 'enemy' in script_path.lower():
                    if '3d' in script_path.lower():
                        script_content = 'extends CharacterBody3D\n\n' + script_content
                    else:
                        script_content = 'extends CharacterBody2D\n\n' + script_content
                elif 'collectible' in script_path.lower():
                    if '3d' in script_path.lower():
                        script_content = 'extends Area3D\n\n' + script_content
                    else:
                        script_content = 'extends Area2D\n\n' + script_content
            
            # Remove markdown code blocks if present
            if script_content.strip().startswith('```'):
                lines = script_content.split('\n')
                if lines[0].startswith('```'):
                    script_content = '\n'.join(lines[1:])
                if script_content.strip().endswith('```'):
                    script_content = script_content.rsplit('```', 1)[0].strip()
            
            validated[script_path] = script_content
        
        return validated

