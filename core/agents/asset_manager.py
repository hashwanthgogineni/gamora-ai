"""
Asset Manager Agent - DALL-E 3 Integration + Free Asset Store Integration
Generates game assets using DALL-E 3, free asset stores, and enhanced procedural generation
"""

from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from io import BytesIO
from pathlib import Path
import httpx
import os
import logging
import json
import re
import colorsys

logger = logging.getLogger(__name__)


class AssetManagerAgent:
    """Asset generation with DALL-E 3 + Free Asset Stores + Enhanced Procedural"""
    
    def __init__(self, openai_client, storage_service):
        self.openai = openai_client
        self.storage = storage_service
        
        # Asset storage configuration
        self.asset_bucket = "gamoraai-assets"  # Separate bucket for assets
        self.use_supabase_assets = True  # Fetch from Supabase Storage instead of local files
        
        # Local fallback (for development/testing)
        self.curated_assets_dir = Path(__file__).parent.parent / "assets" / "curated"
        self.asset_index_path = self.curated_assets_dir / "metadata" / "index.json"
        self.asset_index = None
        
        # Free asset store URLs (open source, CC0/public domain)
        self.asset_sources = {
            "kenney": "https://kenney.nl/assets",  # CC0 assets
            "opengameart": "https://opengameart.org",  # Various licenses
            "itchio_free": "https://itch.io/game-assets/free",  # Free assets
            "craftpix": "https://craftpix.net/freebies",  # Free game assets
        }
        
        logger.info("✅ Asset Manager initialized with Supabase Storage + DALL-E 3")
    
    async def generate_assets(self, game_design: Dict, user_tier: str = "premium", deepseek_client=None):
        """
        Generate assets using Curated Asset Library (Priority 1):
        - First: Match and use curated assets from library
        - Fallback: Enhanced procedural generation
        - Premium: DALL-E 3 for hero (optional, if curated not available)
        
        Strategy:
        1. Load curated asset index
        2. Match game design to curated assets
        3. Copy selected assets from library
        4. Fallback to procedural if no matches
        """
        
        assets = []
        
        # Priority 1: Use curated assets from library
        curated_assets = await self._get_curated_assets(game_design)
        if curated_assets:
            assets.extend(curated_assets)
            logger.info(f"✅ Matched {len(curated_assets)} assets from curated library")
        
        # If we have all essential assets, return them
        essential_types = ['player', 'enemy', 'collectible', 'platform']
        found_types = {asset.get('type', '') for asset in assets}
        if all(etype in found_types for etype in essential_types):
            logger.info("✅ All essential assets found in curated library")
            return self._validate_assets(assets)
        
        # Fallback: Generate missing assets procedurally
        missing_types = [etype for etype in essential_types if etype not in found_types]
        if missing_types:
            logger.info(f"⚠️  Missing asset types, generating procedurally: {missing_types}")
            try:
                # Use AI descriptions for better procedural generation
                if deepseek_client:
                    asset_descriptions = await self._generate_asset_descriptions_with_ai(game_design, deepseek_client)
                else:
                    asset_descriptions = self._generate_basic_asset_descriptions(game_design)
                
                procedural = await self._generate_enhanced_procedural_assets(game_design, asset_descriptions)
                if procedural:
                    assets.extend(procedural)
            except Exception as e:
                logger.error(f"Failed to generate procedural assets: {e}", exc_info=True)
                fallback_assets = self._generate_fallback_assets(game_design)
                assets.extend(fallback_assets)
        
        # Ensure we have at least basic assets
        if len(assets) == 0:
            logger.warning("No assets generated, creating fallback assets")
            fallback_assets = self._generate_fallback_assets(game_design)
            assets.extend(fallback_assets)
        
        validated_assets = self._validate_assets(assets)
        logger.info(f"✅ Generated {len(validated_assets)} validated assets (tier: {user_tier})")
        return validated_assets
    
    def _validate_assets(self, assets: List[Dict]) -> List[Dict]:
        """Validate all assets have required fields"""
        validated_assets = []
        for asset in assets:
            if not isinstance(asset, dict):
                logger.warning(f"Invalid asset format: {asset}")
                continue
            if 'path' not in asset:
                logger.warning(f"Asset missing path: {asset}")
                continue
            if 'data' not in asset and 'content' not in asset:
                logger.warning(f"Asset missing data/content: {asset.get('path', 'unknown')}")
                continue
            validated_assets.append(asset)
        return validated_assets
    
    def _load_asset_index(self) -> Dict:
        """Load asset index from Supabase Storage or local fallback"""
        if self.asset_index is not None:
            return self.asset_index
        
        # Try Supabase Storage first
        if self.use_supabase_assets and self.storage and self.storage.client:
            try:
                # Download index.json from Supabase Storage
                index_data = self.storage.client.storage.from_(self.asset_bucket).download("metadata/index.json")
                if index_data:
                    self.asset_index = json.loads(index_data.decode('utf-8'))
                    logger.info(f"✅ Loaded asset index from Supabase: {len(self.asset_index.get('assets', []))} assets")
                    return self.asset_index
            except Exception as e:
                logger.warning(f"Failed to load asset index from Supabase: {e}, trying local fallback...")
        
        # Local fallback
        if not self.asset_index_path.exists():
            logger.warning(f"Asset index not found: {self.asset_index_path}")
            return {"assets": []}
        
        try:
            with open(self.asset_index_path, 'r', encoding='utf-8') as f:
                self.asset_index = json.load(f)
            logger.info(f"✅ Loaded asset index from local: {len(self.asset_index.get('assets', []))} assets")
            return self.asset_index
        except Exception as e:
            logger.error(f"Failed to load asset index: {e}")
            return {"assets": []}
    
    def _match_assets_to_game(self, game_design: Dict) -> Dict[str, List[Dict]]:
        """Match curated assets to game design"""
        index = self._load_asset_index()
        all_assets = index.get('assets', [])
        
        if not all_assets:
            return {}
        
        # Extract game design requirements
        art_style = game_design.get('art_style', 'pixel_art').lower()
        theme = game_design.get('theme', '').lower()
        genre = game_design.get('genre', 'platformer').lower()
        color_scheme = game_design.get('color_scheme', {})
        
        # Category mapping
        category_map = {
            'player': 'player',
            'enemy': 'enemy',
            'collectible': 'collectible',
            'platform': 'platform',
            'background': 'background',
            'obstacle': 'obstacle',
            'item': 'collectible'
        }
        
        matches = {
            'player': [],
            'enemy': [],
            'collectible': [],
            'platform': [],
            'background': [],
            'obstacle': []
        }
        
        # Score and match assets
        for asset in all_assets:
            score = 0
            asset_category = asset.get('category', '').lower()
            asset_style = asset.get('style', '').lower()
            asset_themes = [t.lower() for t in asset.get('themes', [])]
            asset_genres = [g.lower() for g in asset.get('genres', [])]
            
            # Style match (high weight)
            if art_style in asset_style or asset_style in art_style:
                score += 10
            
            # Theme match
            if theme and any(theme in t or t in theme for t in asset_themes):
                score += 5
            
            # Genre match
            if genre in asset_genres:
                score += 5
            
            # Color similarity (if available)
            if color_scheme and asset.get('colors'):
                color_score = self._calculate_color_similarity(color_scheme, asset.get('colors', {}))
                score += color_score * 2
            
            # Map category to our types
            target_type = category_map.get(asset_category, None)
            if target_type and score > 0 and target_type in matches:
                matches[target_type].append({
                    'asset': asset,
                    'score': score
                })
        
        # Sort by score and select best matches
        selected = {}
        for asset_type, candidates in matches.items():
            if candidates:
                candidates.sort(key=lambda x: x['score'], reverse=True)
                # Select top 3 candidates
                selected[asset_type] = [c['asset'] for c in candidates[:3]]
        
        return selected
    
    def _calculate_color_similarity(self, game_colors: Dict, asset_colors: Dict) -> float:
        """Calculate color similarity score (0-1)"""
        try:
            def hex_to_rgb(hex_color: str) -> tuple:
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            game_primary = game_colors.get('primary', '#4A90E2')
            asset_primary = asset_colors.get('primary', '#4A90E2')
            
            if isinstance(game_primary, str):
                game_rgb = hex_to_rgb(game_primary)
            else:
                game_rgb = game_primary
            
            if isinstance(asset_primary, str):
                asset_rgb = hex_to_rgb(asset_primary)
            else:
                asset_rgb = asset_primary
            
            # Calculate Euclidean distance in RGB space
            distance = sum((a - b) ** 2 for a, b in zip(game_rgb, asset_rgb)) ** 0.5
            # Normalize to 0-1 (max distance in RGB is ~441)
            similarity = 1 - min(distance / 441, 1)
            return similarity
        except:
            return 0.5  # Default similarity
    
    async def _get_curated_assets(self, game_design: Dict) -> List[Dict]:
        """Get curated assets matching game design"""
        try:
            matches = self._match_assets_to_game(game_design)
            
            if not matches:
                logger.warning("No curated assets matched")
                return []
            
            # Safety check: ensure matches is a dict
            if not isinstance(matches, dict):
                logger.warning("Invalid matches format, returning empty list")
                return []
            
            assets = []
            
            # Select one asset per type (best match)
            for asset_type, candidates in matches.items():
                if not candidates:
                    continue
                
                # Use the best match (first in sorted list)
                selected_asset = candidates[0]
                asset_path = selected_asset.get('path', '')
                
                if not asset_path:
                    continue
                
                # Fetch asset from Supabase Storage or local fallback
                asset_data = None
                
                # Try Supabase Storage first
                if self.use_supabase_assets and self.storage and self.storage.client:
                    try:
                        storage_path = f"curated/{asset_path.replace('\\', '/')}"
                        asset_data = self.storage.client.storage.from_(self.asset_bucket).download(storage_path)
                        if asset_data:
                            logger.debug(f"✅ Fetched {asset_type} from Supabase: {storage_path}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch {asset_path} from Supabase: {e}, trying local fallback...")
                
                # Local fallback
                if not asset_data:
                    full_path = self.curated_assets_dir / asset_path
                    if not full_path.exists():
                        logger.warning(f"Asset file not found: {full_path}")
                        continue
                    
                    try:
                        with open(full_path, 'rb') as f:
                            asset_data = f.read()
                        logger.debug(f"✅ Loaded {asset_type} from local: {full_path}")
                    except Exception as e:
                        logger.error(f"Failed to read asset {full_path}: {e}")
                        continue
                
                if asset_data:
                    # Map to expected format
                    type_to_path = {
                        'player': 'assets/sprites/player.png',
                        'enemy': 'assets/sprites/enemy.png',
                        'collectible': 'assets/sprites/collectible.png',
                        'platform': 'assets/sprites/platform.png',
                        'background': 'assets/sprites/background.png'
                    }
                    
                    assets.append({
                        'type': asset_type,
                        'path': type_to_path.get(asset_type, f'assets/sprites/{asset_type}.png'),
                        'data': asset_data,
                        'source': 'curated_supabase' if self.use_supabase_assets and self.storage and self.storage.client else 'curated_local'
                    })
                else:
                    logger.warning(f"Failed to load asset data for {asset_path}")
                    continue
            
            return assets
            
        except Exception as e:
            logger.error(f"Failed to get curated assets: {e}", exc_info=True)
            return []
    
    async def _generate_asset_descriptions_with_ai(self, game_design: Dict, deepseek_client) -> Dict:
        """Use AI to generate detailed visual descriptions for all game assets"""
        
        import json
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a game asset designer. Create detailed visual descriptions for all game assets that match the game's style.

Game Context:
- Title: {game_design.get('title', 'Game')}
- Genre: {game_design.get('genre', 'platformer')}
- Art Style: {game_design.get('art_style', '')}
- Color Scheme: {json.dumps(game_design.get('color_scheme', {}))}
- Player Description: {game_design.get('player_description', '')}
- Enemy Description: {game_design.get('enemy_description', '')}
- Environment: {game_design.get('environment_description', '')}

Your Task:
Generate detailed visual descriptions for each asset type that:
1. Match the game's art style exactly
2. Use the specified color scheme
3. Are consistent with each other
4. Are detailed enough to generate procedurally or with DALL-E

Return JSON with:
- player: {{description: string, colors: [hex], style_notes: string, size: "64x64"}}
- enemy: {{description: string, colors: [hex], style_notes: string, variants: [string], size: "64x64"}}
- collectible: {{description: string, colors: [hex], style_notes: string, types: [{{name: string, description: string}}], size: "32x32"}}
- platform: {{description: string, colors: [hex], style_notes: string, texture: string, size: "128x32"}}
- background: {{description: string, colors: [hex], style_notes: string, layers: [string], size: "1920x1080"}}
- ui_elements: {{button: string, panel: string, icon: string}}

Create REFINED, DETAILED descriptions that will produce high-quality assets:"""
            }
        ]
        
        try:
            response = await deepseek_client.generate(messages, temperature=0.4, max_tokens=4000)
            content = response.get('content', '')
            
            if not content:
                logger.warning("Empty response from AI, using fallback descriptions")
                return self._generate_basic_asset_descriptions(game_design)
            
            # Extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # Try to extract from any code block
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
                    # Remove language identifier if present
                    if content.startswith("json"):
                        content = content[4:].strip()
            
            # Try to find JSON object in the content
            if not content.startswith('{'):
                # Look for JSON object in the text
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    content = content[start_idx:end_idx+1]
            
            if not content or not content.strip():
                logger.warning("No JSON found in AI response, using fallback descriptions")
                return self._generate_basic_asset_descriptions(game_design)
            
            # Repair truncated/incomplete JSON
            content = self._repair_json(content)
            
            # Validate JSON before parsing
            if not self._is_valid_json(content):
                logger.warning("JSON validation failed, attempting repair...")
                content = self._repair_json_aggressive(content)
            
            descriptions = json.loads(content)
            
            # Validate that we got a dictionary
            if not isinstance(descriptions, dict):
                logger.warning("AI response is not a dictionary, using fallback descriptions")
                return self._generate_basic_asset_descriptions(game_design)
            
            logger.info("✅ Successfully parsed AI-generated asset descriptions")
            return descriptions
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            content_preview = content[:500] if 'content' in locals() and content else 'N/A'
            logger.debug(f"Content preview: {content_preview}")
            # Try one more time with aggressive repair
            try:
                if 'content' in locals() and content:
                    repaired = self._repair_json_aggressive(content)
                    if repaired and self._is_valid_json(repaired):
                        descriptions = json.loads(repaired)
                        if isinstance(descriptions, dict):
                            logger.info("✅ Successfully parsed after aggressive repair")
                            return descriptions
            except Exception as repair_error:
                logger.warning(f"Repair attempt failed: {repair_error}")
            # Always return fallback to prevent endless loading
            logger.info("Using fallback asset descriptions")
            return self._generate_basic_asset_descriptions(game_design)
        except Exception as e:
            logger.warning(f"Failed to generate asset descriptions: {e}", exc_info=True)
            return self._generate_basic_asset_descriptions(game_design)
    
    def _repair_json(self, content: str) -> str:
        """Repair common JSON issues like unclosed strings, brackets, etc."""
        if not content:
            return content
        
        # Remove any trailing incomplete strings
        # Find the last complete string
        content = content.strip()
        
        # Count brackets to see if JSON is balanced
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        # If missing closing braces, add them
        if open_braces > close_braces:
            content += '}' * (open_braces - close_braces)
        
        # Fix unterminated strings - find strings that aren't closed
        # Look for patterns like: "text... (end of content)
        # This is complex, so we'll use a simpler approach
        return content
    
    def _repair_json_aggressive(self, content: str) -> str:
        """Aggressively repair truncated/incomplete JSON"""
        if not content:
            return "{}"
        
        content = content.strip()
        
        # If content doesn't start with {, try to find it
        if not content.startswith('{'):
            start_idx = content.find('{')
            if start_idx != -1:
                content = content[start_idx:]
            else:
                return "{}"
        
        # Handle unterminated strings - this is the most common issue
        # Find all quote positions and check if they're balanced
        quote_positions = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(content):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                if not in_string:
                    # Opening quote
                    quote_positions.append((i, 'open'))
                    in_string = True
                else:
                    # Closing quote
                    quote_positions.append((i, 'close'))
                    in_string = False
        
        # If we ended in a string (odd number of unescaped quotes), close it
        if in_string and quote_positions:
            last_quote_pos = quote_positions[-1][0]
            # Close the string and add a placeholder value
            content = content[:last_quote_pos+1] + '"'
        
        # Count and balance braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces > close_braces:
            # Find the last incomplete object
            # Look for the last complete key-value pair
            # Remove trailing incomplete content
            last_comma = content.rfind(',')
            last_colon = content.rfind(':')
            
            # If we have an incomplete value after the last colon
            if last_colon > last_comma or (last_comma == -1 and last_colon != -1):
                # Find where the value starts (after the colon)
                value_start = last_colon + 1
                value_part = content[value_start:].strip()
                
                # If value is incomplete (unterminated string or missing closing)
                if value_part and not value_part.endswith(('"', '}', ']', ',')):
                    # Try to find a safe cut point
                    # Look for the last complete element before this
                    # Find the last complete key-value pair
                    safe_cut = last_colon
                    # Look backwards for the key
                    key_start = content.rfind('"', 0, last_colon)
                    if key_start != -1:
                        # Find the opening quote of this key
                        for i in range(key_start-1, -1, -1):
                            if content[i] == '"' and (i == 0 or content[i-1] != '\\'):
                                # Found key start, remove incomplete value
                                content = content[:key_start-1].rstrip().rstrip(',')
                                break
            
            # Add missing closing braces
            content += '}' * (open_braces - close_braces)
        
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # Final validation - if still invalid, return minimal valid JSON
        try:
            json.loads(content)
            return content
        except:
            # Last resort - return a minimal valid structure
            # Try to extract at least some keys
            if '"' in content:
                # Find first few complete key-value pairs
                matches = re.findall(r'"([^"]+)":\s*"([^"]*)"', content)
                if matches:
                    repaired = '{'
                    for key, value in matches[:5]:  # Limit to 5 pairs
                        if repaired != '{':
                            repaired += ','
                        repaired += f'"{key}": "{value}"'
                    repaired += '}'
                    return repaired
            return "{}"
    
    def _is_valid_json(self, content: str) -> bool:
        """Check if content is valid JSON"""
        if not content or not content.strip():
            return False
        try:
            json.loads(content)
            return True
        except:
            return False
    
    def _generate_basic_asset_descriptions(self, game_design: Dict) -> Dict:
        """Fallback: Generate basic asset descriptions"""
        return {
            "player": {
                "description": game_design.get('player_description', 'A heroic character'),
                "colors": ["#4A90E2"],
                "size": "64x64"
            },
            "enemy": {
                "description": game_design.get('enemy_description', 'An enemy character'),
                "colors": ["#FF6464"],
                "size": "64x64"
            },
            "collectible": {
                "description": "A shiny collectible item",
                "colors": ["#FFD700"],
                "size": "32x32"
            }
        }
    
    def _generate_procedural_assets_with_descriptions(self, game_design: Dict, descriptions: Dict) -> List[Dict]:
        """Generate procedural assets using AI descriptions"""
        # This will be enhanced to use the descriptions
        return self._generate_procedural_ui()
    
    async def _generate_dalle_hero(self, game_design: Dict, player_desc: Dict = None) -> Dict:
        """Generate custom hero sprite with DALL-E 3 using AI-generated descriptions"""
        
        if player_desc:
            description = player_desc.get('description', game_design.get('player_description', 'hero character'))
            style_notes = player_desc.get('style_notes', '')
        else:
            description = game_design.get('player_description', 'hero character')
            style_notes = ''
        
        prompt = f"""
        {game_design.get('art_style', 'Pixel art')} video game sprite: {description}
        {style_notes}
        Style: {game_design.get('art_style', 'pixel art')}
        64x64 pixel sprite, transparent background, game-ready, centered, high quality
        """
        
        try:
            # Call DALL-E 3
            response = await self.openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard"
            )
            
            # Download image
            image_url = response.data[0].url
            async with httpx.AsyncClient(timeout=30.0) as client:
                img_data = await client.get(image_url)
                image_bytes = img_data.content
            
            # Resize to 64x64
            img = Image.open(BytesIO(image_bytes))
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format="PNG")
            
            logger.info("✅ DALL-E hero generated")
            
            return {
                "type": "player",
                "path": "assets/sprites/player.png",
                "data": output.getvalue(),
                "source": "dalle3"
            }
            
        except Exception as e:
            logger.error(f"DALL-E failed: {e}")
            return self._create_placeholder("player")
    
    def _generate_procedural_ui(self) -> List[Dict]:
        """Generate simple UI elements procedurally (legacy method)"""
        # This is now handled by _generate_enhanced_procedural_assets
        return []
    
    async def _fetch_free_assets(self, game_design: Dict, descriptions: Dict, deepseek_client=None) -> List[Dict]:
        """Fetch free assets from open source repositories based on game style"""
        
        genre = game_design.get('genre', 'platformer')
        art_style = game_design.get('art_style', '').lower()
        dimension = game_design.get('dimension', '2D')
        
        # Use AI to determine what assets to search for
        if deepseek_client:
            search_terms = await self._generate_asset_search_terms(game_design, descriptions, deepseek_client)
        else:
            search_terms = self._generate_basic_search_terms(game_design)
        
        assets = []
        
        # Try to find and download matching free assets
        # For now, we'll use enhanced procedural generation
        # In production, you'd integrate with actual asset store APIs
        
        logger.info(f"🔍 Searching for free assets: {search_terms}")
        logger.info("💡 Using enhanced procedural generation (free asset API integration can be added)")
        
        return assets
    
    async def _generate_asset_search_terms(self, game_design: Dict, descriptions: Dict, deepseek_client) -> Dict:
        """Use AI to generate search terms for finding free assets"""
        
        messages = [
            {
                "role": "user",
                "content": f"""Generate search terms for finding free game assets that match this game.

Game: {game_design.get('title', 'Game')}
Genre: {game_design.get('genre', 'platformer')}
Art Style: {game_design.get('art_style', '')}
Dimension: {game_design.get('dimension', '2D')}

Return JSON with search terms for:
- player: [terms for player character]
- enemy: [terms for enemies]
- collectible: [terms for collectibles]
- platform: [terms for platforms/ground]
- background: [terms for backgrounds]
- ui: [terms for UI elements]

Use terms that would match free assets on OpenGameArt, Kenney.nl, or itch.io:"""
            }
        ]
        
        try:
            response = await deepseek_client.generate(messages, temperature=0.3)
            content = response.get('content', '')
            
            if not content:
                return self._generate_basic_search_terms(game_design)
            
            # Extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    content = parts[1].strip()
                    if content.startswith("json"):
                        content = content[4:].strip()
            
            # Try to find JSON object
            if not content.startswith('{'):
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    content = content[start_idx:end_idx+1]
            
            if not content or not content.strip():
                return self._generate_basic_search_terms(game_design)
            
            # Repair truncated/incomplete JSON
            content = self._repair_json(content)
            
            # Validate JSON before parsing
            if not self._is_valid_json(content):
                logger.warning("Search terms JSON validation failed, attempting repair...")
                content = self._repair_json_aggressive(content)
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse search terms JSON: {e}")
            # Try aggressive repair
            try:
                if 'content' in locals() and content:
                    repaired = self._repair_json_aggressive(content)
                    if repaired and self._is_valid_json(repaired):
                        result = json.loads(repaired)
                        if isinstance(result, dict):
                            logger.info("✅ Successfully parsed search terms after aggressive repair")
                            return result
            except Exception as repair_error:
                logger.warning(f"Search terms repair attempt failed: {repair_error}")
            # Always return fallback to prevent endless loading
            logger.info("Using fallback search terms")
            return self._generate_basic_search_terms(game_design)
        except Exception as e:
            logger.warning(f"Failed to generate search terms: {e}")
            return self._generate_basic_search_terms(game_design)
    
    def _generate_basic_search_terms(self, game_design: Dict) -> Dict:
        """Fallback search terms"""
        genre = game_design.get('genre', 'platformer')
        return {
            "player": [f"{genre} character", "player sprite"],
            "enemy": [f"{genre} enemy", "obstacle"],
            "collectible": ["coin", "gem", "collectible"],
            "platform": ["platform", "ground", "tile"],
            "background": [f"{genre} background", "game background"]
        }
    
    async def _generate_enhanced_procedural_assets(self, game_design: Dict, descriptions: Dict) -> List[Dict]:
        """Generate enhanced procedural assets with rich, detailed textures"""
        
        assets = []
        
        # Generate rich textures for each asset type
        if 'player' in descriptions:
            player_asset = self._generate_rich_texture_sprite(
                descriptions['player'],
                size=(64, 64),
                asset_type="player"
            )
            if player_asset:
                assets.append({
                    "type": "player",
                    "path": "assets/sprites/player.png",
                    "data": player_asset,
                    "source": "enhanced_procedural"
                })
        
        if 'enemy' in descriptions:
            enemy_asset = self._generate_rich_texture_sprite(
                descriptions['enemy'],
                size=(64, 64),
                asset_type="enemy"
            )
            if enemy_asset:
                assets.append({
                    "type": "enemy",
                    "path": "assets/sprites/enemy.png",
                    "data": enemy_asset,
                    "source": "enhanced_procedural"
                })
        
        if 'collectible' in descriptions:
            collectible_asset = self._generate_rich_texture_sprite(
                descriptions['collectible'],
                size=(32, 32),
                asset_type="collectible"
            )
            if collectible_asset:
                assets.append({
                    "type": "collectible",
                    "path": "assets/sprites/collectible.png",
                    "data": collectible_asset,
                    "source": "enhanced_procedural"
                })
        
        if 'platform' in descriptions:
            platform_asset = self._generate_rich_texture_sprite(
                descriptions['platform'],
                size=(128, 32),
                asset_type="platform"
            )
            if platform_asset:
                assets.append({
                    "type": "platform",
                    "path": "assets/sprites/platform.png",
                    "data": platform_asset,
                    "source": "enhanced_procedural"
                })
        
        # Generate UI elements
        ui_assets = self._generate_rich_ui_elements(game_design, descriptions)
        assets.extend(ui_assets)
        
        return assets
    
    def _generate_rich_texture_sprite(self, description: Dict, size: tuple, asset_type: str) -> Optional[bytes]:
        """Generate rich, detailed texture sprite with gradients, shadows, and details"""
        
        try:
            width, height = size
            colors = description.get('colors', ['#4A90E2'])
            style_notes = description.get('style_notes', '')
            
            # Parse colors
            if colors and len(colors) > 0:
                primary_color = self._hex_to_rgb(colors[0])
                secondary_color = self._hex_to_rgb(colors[1]) if len(colors) > 1 else primary_color
            else:
                primary_color = (74, 144, 226)
                secondary_color = (80, 200, 120)
            
            # Create base image with gradient background
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            if asset_type == "player":
                # Rich player sprite with 3D effect
                # Main body
                draw.ellipse([4, 4, width-4, height-4], fill=(*primary_color, 255))
                # Gradient highlight
                for i in range(8, width//2):
                    alpha = int(200 * (1 - i / (width//2)))
                    color = (min(255, primary_color[0] + 30), min(255, primary_color[1] + 30), min(255, primary_color[2] + 30), alpha)
                    draw.ellipse([i, i, width-i, height-i], fill=color)
                # Shadow
                shadow = Image.new('RGBA', size, (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.ellipse([6, 6, width-2, height-2], fill=(0, 0, 0, 120))
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=3))
                img = Image.alpha_composite(img, shadow)
                # Eyes/details
                eye_size = width // 8
                draw.ellipse([width//3 - eye_size//2, height//3 - eye_size//2, width//3 + eye_size//2, height//3 + eye_size//2], fill=(255, 255, 255, 255))
                draw.ellipse([2*width//3 - eye_size//2, height//3 - eye_size//2, 2*width//3 + eye_size//2, height//3 + eye_size//2], fill=(255, 255, 255, 255))
                
            elif asset_type == "enemy":
                # Rich enemy sprite
                draw.rectangle([4, 4, width-4, height-4], fill=(*primary_color, 255))
                # Angry eyes
                draw.rectangle([width//4, height//3, width//4 + 4, height//3 + 4], fill=(255, 0, 0, 255))
                draw.rectangle([3*width//4 - 4, height//3, 3*width//4, height//3 + 4], fill=(255, 0, 0, 255))
                # Shadow
                shadow = Image.new('RGBA', size, (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rectangle([6, 6, width-2, height-2], fill=(0, 0, 0, 100))
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
                img = Image.alpha_composite(img, shadow)
                
            elif asset_type == "collectible":
                # Rich collectible (shiny coin/gem)
                # Outer glow
                draw.ellipse([0, 0, width, height], fill=(255, 215, 0, 180))
                # Main body
                draw.ellipse([2, 2, width-2, height-2], fill=(255, 200, 0, 255))
                # Inner highlight
                draw.ellipse([4, 4, width-4, height-4], fill=(255, 240, 150, 255))
                # Center shine
                draw.ellipse([width//3, height//3, 2*width//3, 2*height//3], fill=(255, 255, 255, 200))
                # Sparkle effect
                import random
                for i in range(3):
                    x = width // 4 + (i * width // 4)
                    y = height // 4 + (i % 2) * height // 2
                    draw.ellipse([x-1, y-1, x+1, y+1], fill=(255, 255, 255, 255))
                
            elif asset_type == "platform":
                # Rich platform texture
                # Base
                draw.rectangle([0, 0, width, height], fill=(*primary_color, 255))
                # Texture pattern
                for i in range(0, width, 8):
                    draw.line([(i, 0), (i, height)], fill=(min(255, primary_color[0] + 20), min(255, primary_color[1] + 20), min(255, primary_color[2] + 20), 100), width=1)
                # Top highlight
                draw.rectangle([0, 0, width, 4], fill=(min(255, primary_color[0] + 50), min(255, primary_color[1] + 50), min(255, primary_color[2] + 50), 255))
                # Bottom shadow
                draw.rectangle([0, height-4, width, height], fill=(max(0, primary_color[0] - 30), max(0, primary_color[1] - 30), max(0, primary_color[2] - 30), 255))
                # Add noise texture
                import random
                for _ in range(width * height // 20):
                    x = random.randint(0, width-1)
                    y = random.randint(0, height-1)
                    draw.point((x, y), fill=(*primary_color, random.randint(200, 255)))
            
            # Enhance image
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            # Save
            output = BytesIO()
            img.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate rich texture: {e}")
            return None
    
    def _generate_rich_ui_elements(self, game_design: Dict, descriptions: Dict) -> List[Dict]:
        """Generate rich UI elements with detailed textures"""
        
        assets = []
        ui_desc = descriptions.get('ui_elements', {})
        
        # Generate button texture
        button_img = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
        draw = ImageDraw.Draw(button_img)
        # Base
        try:
            draw.rounded_rectangle([0, 0, 200, 50], radius=8, fill=(74, 144, 226, 255))
        except:
            # Fallback if rounded_rectangle not available
            draw.rectangle([0, 0, 200, 50], fill=(74, 144, 226, 255))
        # Highlight
        try:
            draw.rounded_rectangle([0, 0, 200, 25], radius=8, fill=(94, 164, 246, 255))
        except:
            draw.rectangle([0, 0, 200, 25], fill=(94, 164, 246, 255))
        # Shadow
        shadow = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        try:
            shadow_draw.rounded_rectangle([2, 2, 202, 52], radius=8, fill=(0, 0, 0, 100))
        except:
            shadow_draw.rectangle([2, 2, 202, 52], fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
        button_img = Image.alpha_composite(button_img, shadow)
        
        button_bytes = BytesIO()
        button_img.save(button_bytes, format='PNG')
        assets.append({
            "type": "ui_button",
            "path": "assets/ui/button.png",
            "data": button_bytes.getvalue(),
            "source": "enhanced_procedural"
        })
        
        return assets
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (74, 144, 226)  # Default blue
    
    def _generate_fallback_assets(self, game_design: Dict) -> List[Dict]:
        """Generate basic fallback assets if all else fails"""
        
        assets = []
        color_scheme = game_design.get('color_scheme', {})
        if isinstance(color_scheme, dict):
            primary_color = self._hex_to_rgb(color_scheme.get('primary', '#4A90E2'))
        else:
            primary_color = (74, 144, 226)
        
        # Player
        player_img = Image.new('RGBA', (64, 64), (*primary_color, 255))
        player_bytes = BytesIO()
        player_img.save(player_bytes, format='PNG')
        assets.append({
            "type": "player",
            "path": "assets/sprites/player.png",
            "data": player_bytes.getvalue(),
            "source": "fallback"
        })
        
        # Enemy
        enemy_img = Image.new('RGBA', (64, 64), (220, 50, 50, 255))
        enemy_bytes = BytesIO()
        enemy_img.save(enemy_bytes, format='PNG')
        assets.append({
            "type": "enemy",
            "path": "assets/sprites/enemy.png",
            "data": enemy_bytes.getvalue(),
            "source": "fallback"
        })
        
        # Collectible
        collectible_img = Image.new('RGBA', (32, 32), (255, 215, 0, 255))
        collectible_bytes = BytesIO()
        collectible_img.save(collectible_bytes, format='PNG')
        assets.append({
            "type": "collectible",
            "path": "assets/sprites/collectible.png",
            "data": collectible_bytes.getvalue(),
            "source": "fallback"
        })
        
        # Platform
        platform_img = Image.new('RGBA', (128, 32), (100, 150, 100, 255))
        platform_bytes = BytesIO()
        platform_img.save(platform_bytes, format='PNG')
        assets.append({
            "type": "platform",
            "path": "assets/sprites/platform.png",
            "data": platform_bytes.getvalue(),
            "source": "fallback"
        })
        
        logger.info("✅ Generated fallback assets")
        return assets
    
    def _create_placeholder(self, name: str) -> Dict:
        """Create colored placeholder"""
        
        try:
            img = Image.new('RGBA', (32, 32), (100, 150, 255, 255))
            output = BytesIO()
            img.save(output, format="PNG")
            
            return {
                "type": name,
                "path": f"assets/sprites/{name}.png",
                "data": output.getvalue(),
                "source": "placeholder"
            }
        except Exception as e:
            logger.error(f"Failed to create placeholder for {name}: {e}")
            # Return minimal valid asset
            return {
                "type": name,
                "path": f"assets/sprites/{name}.png",
                "data": b'',  # Empty but valid
                "source": "placeholder_error"
        }
