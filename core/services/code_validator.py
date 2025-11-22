import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CodeValidator:
    # Validates component keys
    def __init__(self):
        pass
    
    def validate_component_keys(self, components: Dict[str, any], required_keys: List[str]) -> List[str]:
        # Validates that required component keys exist
        missing = []
        for key in required_keys:
            if key not in components:
                missing.append(f"Missing component key: '{key}'")
                logger.error(f"❌ Missing component key: '{key}'")
        
        return missing


# Global validator instance
_validator = CodeValidator()


def validate_component_keys(components: Dict[str, any], required_keys: List[str]) -> List[str]:
    # Validates component keys
    return _validator.validate_component_keys(components, required_keys)
