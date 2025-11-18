"""
Asset Processor Service
Processes AI-generated assets (images, audio) for Godot Engine
Handles format conversion, optimization, and metadata generation
"""

import base64
import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import json

logger = logging.getLogger(__name__)


class AssetProcessor:
    """
    Process and optimize assets for Godot Engine
    """
    
    def __init__(self):
        self.supported_image_formats = ['.png', '.jpg', '.jpeg', '.webp']
        self.supported_audio_formats = ['.wav', '.ogg', '.mp3']
    
    def process_sprite_asset(
        self,
        asset_data: bytes,
        asset_name: str,
        target_size: Optional[tuple] = None
    ) -> tuple[bytes, str]:
        """
        Process sprite/texture for Godot
        
        Args:
            asset_data: Raw image bytes
            asset_name: Name for the asset
            target_size: Optional (width, height) to resize
        
        Returns:
            Tuple of (processed_bytes, import_metadata)
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(asset_data))
            
            # Convert to RGBA if needed
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Resize if needed
            if target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save as PNG (best for Godot)
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            processed_data = output.getvalue()
            
            # Generate Godot import metadata
            import_config = self._generate_texture_import_config(image.size)
            
            logger.info(f"✅ Processed sprite: {asset_name} ({image.size[0]}x{image.size[1]})")
            return processed_data, import_config
            
        except Exception as e:
            logger.error(f"❌ Failed to process sprite {asset_name}: {e}")
            # Return original data if processing fails
            return asset_data, ""
    
    def process_tileset_asset(
        self,
        asset_data: bytes,
        asset_name: str,
        tile_size: int = 32
    ) -> tuple[bytes, str]:
        """
        Process tileset texture for Godot
        
        Args:
            asset_data: Raw image bytes
            asset_name: Name for the tileset
            tile_size: Size of each tile in pixels
        
        Returns:
            Tuple of (processed_bytes, import_metadata)
        """
        try:
            image = Image.open(io.BytesIO(asset_data))
            
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Ensure dimensions are multiples of tile_size
            width = (image.size[0] // tile_size) * tile_size
            height = (image.size[1] // tile_size) * tile_size
            
            if width != image.size[0] or height != image.size[1]:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            processed_data = output.getvalue()
            
            import_config = self._generate_tileset_import_config(tile_size)
            
            logger.info(f"✅ Processed tileset: {asset_name} ({width}x{height}, tile: {tile_size})")
            return processed_data, import_config
            
        except Exception as e:
            logger.error(f"❌ Failed to process tileset {asset_name}: {e}")
            return asset_data, ""
    
    def create_placeholder_sprite(
        self,
        width: int = 64,
        height: int = 64,
        color: tuple = (100, 150, 255, 255)
    ) -> bytes:
        """Create a placeholder sprite when AI generation fails"""
        
        image = Image.new('RGBA', (width, height), color)
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
    
    def _generate_texture_import_config(self, size: tuple) -> str:
        """Generate .import file content for Godot texture"""
        
        config = f'''[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://generated"
path="res://.godot/imported/texture.png"

[deps]

source_file="res://assets/sprites/texture.png"
dest_files=["res://.godot/imported/texture.png"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
'''
        
        return config
    
    def _generate_tileset_import_config(self, tile_size: int) -> str:
        """Generate .import file for tileset"""
        
        config = f'''[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://tileset"
path="res://.godot/imported/tileset.png"

[deps]

source_file="res://assets/textures/tileset.png"
dest_files=["res://.godot/imported/tileset.png"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
'''
        
        return config
    
    def generate_procedural_sprites(
        self,
        game_design: Dict[str, Any]
    ) -> Dict[str, bytes]:
        """
        Generate high-quality procedural sprites/textures when DALL-E is not available
        Creates professional-looking assets with gradients, shadows, and details
        """
        
        sprites = {}
        from PIL import ImageDraw, ImageFilter
        
        # Get color scheme from design (handle both dict and string)
        color_scheme = game_design.get('color_scheme', {})
        if isinstance(color_scheme, str):
            color_scheme = {}
        primary_color = self._hex_to_rgb(color_scheme.get('primary', '#4A90E2') if isinstance(color_scheme, dict) else '#4A90E2')
        secondary_color = self._hex_to_rgb(color_scheme.get('secondary', '#50C878') if isinstance(color_scheme, dict) else '#50C878')
        
        # Check if 3D game
        dimension = game_design.get('dimension', '2D')
        is_3d = dimension == '3D' or '3d' in game_design.get('genre', '').lower()
        
        if is_3d:
            # For 3D games, we don't need 2D sprites, but we'll create texture maps
            # Generate a simple texture that can be used as albedo
            texture_img = Image.new('RGBA', (256, 256), (*primary_color, 255))
            draw = ImageDraw.Draw(texture_img)
            # Add some pattern/detail
            for i in range(0, 256, 32):
                draw.line([(i, 0), (i, 256)], fill=(*secondary_color, 50), width=1)
                draw.line([(0, i), (256, i)], fill=(*secondary_color, 50), width=1)
            texture_bytes = io.BytesIO()
            texture_img.save(texture_bytes, format='PNG')
            sprites['texture_albedo.png'] = texture_bytes.getvalue()
        else:
            # Generate high-quality 2D player sprite with gradient and shadow
            player_img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(player_img)
            # Main body with gradient effect
            draw.ellipse([8, 8, 56, 56], fill=(*primary_color, 255))
            # Highlight
            draw.ellipse([12, 12, 32, 32], fill=(min(255, primary_color[0] + 40), min(255, primary_color[1] + 40), min(255, primary_color[2] + 40), 200))
            # Shadow
            shadow_img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            shadow_draw.ellipse([10, 10, 58, 58], fill=(0, 0, 0, 100))
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=2))
            player_img = Image.alpha_composite(player_img, shadow_img)
            player_bytes = io.BytesIO()
            player_img.save(player_bytes, format='PNG')
            sprites['player.png'] = player_bytes.getvalue()
            
            # Generate enemy sprite with red gradient
            enemy_img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(enemy_img)
            draw.rectangle([8, 8, 56, 56], fill=(220, 50, 50, 255))
            draw.rectangle([12, 12, 28, 28], fill=(255, 100, 100, 200))
            enemy_bytes = io.BytesIO()
            enemy_img.save(enemy_bytes, format='PNG')
            sprites['enemy.png'] = enemy_bytes.getvalue()
            
            # Generate collectible sprite (shiny coin)
            collectible_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(collectible_img)
            # Outer ring
            draw.ellipse([2, 2, 30, 30], fill=(255, 200, 0, 255))
            # Inner highlight
            draw.ellipse([8, 8, 24, 24], fill=(255, 240, 150, 255))
            # Center shine
            draw.ellipse([12, 12, 20, 20], fill=(255, 255, 200, 255))
            collectible_bytes = io.BytesIO()
            collectible_img.save(collectible_bytes, format='PNG')
            sprites['collectible.png'] = collectible_bytes.getvalue()
            
            # Generate platform sprite with texture
            platform_img = Image.new('RGBA', (128, 32), (*secondary_color, 255))
            draw = ImageDraw.Draw(platform_img)
            # Add texture lines
            for i in range(0, 128, 8):
                draw.line([(i, 0), (i, 32)], fill=(min(255, secondary_color[0] + 20), min(255, secondary_color[1] + 20), min(255, secondary_color[2] + 20), 100), width=1)
            # Top highlight
            draw.rectangle([0, 0, 128, 4], fill=(min(255, secondary_color[0] + 40), min(255, secondary_color[1] + 40), min(255, secondary_color[2] + 40), 200))
            platform_bytes = io.BytesIO()
            platform_img.save(platform_bytes, format='PNG')
            sprites['platform.png'] = platform_bytes.getvalue()
            
            # Generate background with gradient
            bg_img = Image.new('RGBA', (800, 600), (0, 0, 0, 0))
            draw = ImageDraw.Draw(bg_img)
            # Gradient effect
            for y in range(600):
                alpha = int(100 + (y / 600) * 100)
                color = (primary_color[0], primary_color[1], primary_color[2], alpha)
                draw.line([(0, y), (800, y)], fill=color)
            bg_bytes = io.BytesIO()
            bg_img.save(bg_bytes, format='PNG')
            sprites['background.png'] = bg_bytes.getvalue()
        
        logger.info(f"✅ Generated {len(sprites)} high-quality procedural {'textures' if is_3d else 'sprites'}")
        return sprites
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def create_audio_placeholder(self, duration_ms: int = 1000) -> bytes:
        """Create a placeholder silent audio file"""
        # For now, return empty bytes - would need audio library for actual generation
        return b''
    
    def organize_assets(
        self,
        assets: List[Dict],
        procedural_sprites: Dict[str, bytes]
    ) -> Dict[str, Any]:
        """
        Organize all assets into Godot project structure
        
        Returns:
            Dictionary mapping file paths to content
        """
        
        organized = {}
        
        # Add AI-generated assets
        for asset in assets:
            if not isinstance(asset, dict):
                logger.warning(f"Invalid asset format (not a dict): {asset}")
                continue
                
            path = asset.get('path', '')
            if not path:
                logger.warning(f"Asset missing path: {asset}")
                continue
            
            # Handle both 'content' (base64) and 'data' (bytes) formats
            content = asset.get('content', '')
            data = asset.get('data', None)
            
            if data:
                # Direct bytes data
                try:
                    if isinstance(data, bytes):
                        organized[path] = data
                    else:
                        logger.warning(f"Asset data is not bytes for: {path}")
                except Exception as e:
                    logger.error(f"Failed to process asset data for {path}: {e}")
            elif content:
                # Base64 encoded content
                try:
                    asset_data = base64.b64decode(content)
                    organized[path] = asset_data
                except Exception as e:
                    logger.warning(f"Failed to decode base64 asset {path}: {e}")
            else:
                logger.warning(f"Asset has no content or data: {path}")
        
        # Add procedural sprites
        for name, data in procedural_sprites.items():
            path = f"assets/sprites/{name}"
            organized[path] = data
        
        logger.info(f"✅ Organized {len(organized)} assets")
        return organized
    
    def create_asset_manifest(
        self,
        project_path: Path,
        assets: Dict[str, Any]
    ) -> str:
        """Create a manifest of all assets in the project"""
        
        manifest = {
            "version": "1.0",
            "assets": [],
            "generated_at": "2024"
        }
        
        for path, _ in assets.items():
            asset_info = {
                "path": path,
                "type": self._detect_asset_type(path),
                "size": len(assets[path]) if isinstance(assets[path], bytes) else 0
            }
            manifest["assets"].append(asset_info)
        
        return json.dumps(manifest, indent=2)
    
    def _detect_asset_type(self, path: str) -> str:
        """Detect asset type from path"""
        path_lower = path.lower()
        
        if any(ext in path_lower for ext in ['.png', '.jpg', '.jpeg', '.webp']):
            if 'sprite' in path_lower:
                return 'sprite'
            elif 'texture' in path_lower or 'tileset' in path_lower:
                return 'texture'
            else:
                return 'image'
        elif any(ext in path_lower for ext in ['.wav', '.ogg', '.mp3']):
            if 'music' in path_lower:
                return 'music'
            else:
                return 'sound'
        elif '.gd' in path_lower:
            return 'script'
        elif '.tscn' in path_lower:
            return 'scene'
        else:
            return 'unknown'
