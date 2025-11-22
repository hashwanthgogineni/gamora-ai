import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DimensionDetector:
    # Detects game dimension from user prompts
    # Keywords that strongly indicate 3D
    THREE_D_KEYWORDS = [
        '3d', '3-d', 'three-dimensional', 'three dimensional',
        '3 dimensional', '3-dimensional', 'third dimension',
        'isometric', 'perspective', 'depth', 'z-axis', 'z axis',
        'camera', '3d graphics', '3d graphics', 'webgl',
        'three.js', 'babylon', 'unity', 'unreal'
    ]
    
    # Keywords that strongly indicate 2D
    TWO_D_KEYWORDS = [
        '2d', '2-d', 'two-dimensional', 'two dimensional',
        '2 dimensional', '2-dimensional', 'side-scrolling',
        'side scrolling', 'side-scroller', 'platformer',
        'pixel art', 'sprite', 'canvas', 'flat'
    ]
    
    # Game genres that are typically 3D
    THREE_D_GENRES = [
        'first-person', 'first person', 'fps', 'third-person',
        'third person', 'tps', 'open world', 'open-world',
        'sandbox', 'simulation', 'driving', 'racing 3d',
        'flight simulator', 'vr', 'virtual reality'
    ]
    
    # Game genres that are typically 2D
    TWO_D_GENRES = [
        'platformer', 'puzzle', 'match-3', 'match 3',
        'endless runner', 'side-scroller', 'retro',
        'pixel', 'arcade', 'classic'
    ]
    
    @classmethod
    def detect_dimension(cls, user_prompt: str, game_design: Optional[Dict] = None) -> str:
        # Detects if game should be 2D or 3D from user prompt
        if not user_prompt:
            return '2D'
        
        prompt_lower = user_prompt.lower()
        
        # Check game_design first if available
        if game_design:
            dimension = game_design.get('dimension', '').upper()
            if dimension in ['2D', '3D']:
                logger.info(f"Dimension from game_design: {dimension}")
                return dimension
        
        # Count 3D indicators
        three_d_score = 0
        for keyword in cls.THREE_D_KEYWORDS:
            if keyword in prompt_lower:
                three_d_score += 2  # Strong indicator
                logger.debug(f"Found 3D keyword: {keyword}")
        
        for genre in cls.THREE_D_GENRES:
            if genre in prompt_lower:
                three_d_score += 1
                logger.debug(f"Found 3D genre: {genre}")
        
        # Count 2D indicators
        two_d_score = 0
        for keyword in cls.TWO_D_KEYWORDS:
            if keyword in prompt_lower:
                two_d_score += 2  # Strong indicator
                logger.debug(f"Found 2D keyword: {keyword}")
        
        for genre in cls.TWO_D_GENRES:
            if genre in prompt_lower:
                two_d_score += 1
                logger.debug(f"Found 2D genre: {genre}")
        
        # Check for explicit "3d" or "2d" mentions (highest priority)
        if re.search(r'\b3d\b|\b3-d\b|three.dimensional', prompt_lower):
            three_d_score += 5
        if re.search(r'\b2d\b|\b2-d\b|two.dimensional', prompt_lower):
            two_d_score += 5
        
        # Decision logic
        if three_d_score > two_d_score:
            dimension = '3D'
        elif two_d_score > three_d_score:
            dimension = '2D'
        else:
            # Ambiguous - default to 2D (simpler, more reliable)
            dimension = '2D'
            logger.info("Dimension ambiguous, defaulting to 2D")
        
        logger.info(f"Dimension detected: {dimension} (3D score: {three_d_score}, 2D score: {two_d_score})")
        return dimension
    
    @classmethod
    def normalize_dimension(cls, dimension: str) -> str:
        # Normalizes dimension string to '2D' or '3D'
        if not dimension:
            return '2D'
        
        dim_upper = str(dimension).upper().strip()
        
        # Handle numeric
        if dim_upper in ['2', '2D', 'TWO', 'TWO-D', 'TWO-DIMENSIONAL']:
            return '2D'
        elif dim_upper in ['3', '3D', 'THREE', 'THREE-D', 'THREE-DIMENSIONAL']:
            return '3D'
        elif '4' in dim_upper or '5' in dim_upper or dim_upper in ['4', '5', '6', '7', '8', '9']:
            # Convert invalid dimensions to 3D
            logger.info(f"Converting {dimension} to 3D (only 2D and 3D supported)")
            return '3D'
        else:
            # Default to 2D
            return '2D'

