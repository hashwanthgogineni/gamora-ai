"""
Professional Game Architecture Patterns
Implements best practices from industry-standard game development
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class GameArchitectureGenerator:
    """
    Generates professional game architecture patterns:
    - State machines for game logic
    - Event system for decoupled communication
    - Singleton patterns for managers
    - Component-based systems
    """
    
    def generate_game_state_manager(self, game_design: Dict[str, Any]) -> str:
        """Generate a professional game state manager with state machine pattern"""
        
        states = ["MENU", "PLAYING", "PAUSED", "GAME_OVER", "VICTORY"]
        if game_design.get('genre') == 'runner':
            states = ["MENU", "PLAYING", "PAUSED", "GAME_OVER"]
        
        script = f'''extends Node

## ============================================
## PROFESSIONAL GAME STATE MANAGER
## State Machine Pattern for Game Logic
## ============================================

enum GameState {{
    MENU,
    PLAYING,
    PAUSED,
    GAME_OVER,
    VICTORY
}}

var current_state: GameState = GameState.MENU
var previous_state: GameState = GameState.MENU

# State change signal
signal state_changed(new_state, old_state)

func _ready():
    change_state(GameState.MENU)

func change_state(new_state: GameState):
    """Change game state with validation"""
    if new_state == current_state:
        return
    
    previous_state = current_state
    current_state = new_state
    
    emit_signal("state_changed", new_state, previous_state)
    
    # Handle state entry
    match new_state:
        GameState.MENU:
            _enter_menu()
        GameState.PLAYING:
            _enter_playing()
        GameState.PAUSED:
            _enter_paused()
        GameState.GAME_OVER:
            _enter_game_over()
        GameState.VICTORY:
            _enter_victory()

func _enter_menu():
    """Enter menu state"""
    get_tree().paused = false
    var menu = get_node_or_null("/root/Main/UI/Menu")
    if menu:
        menu.visible = true

func _enter_playing():
    """Enter playing state"""
    get_tree().paused = false
    var menu = get_node_or_null("/root/Main/UI/Menu")
    if menu:
        menu.visible = false

func _enter_paused():
    """Enter paused state"""
    get_tree().paused = true

func _enter_game_over():
    """Enter game over state"""
    get_tree().paused = true
    var game_over_ui = get_node_or_null("/root/Main/UI/GameOver")
    if game_over_ui:
        game_over_ui.visible = true

func _enter_victory():
    """Enter victory state"""
    get_tree().paused = true
    var victory_ui = get_node_or_null("/root/Main/UI/Victory")
    if victory_ui:
        victory_ui.visible = true

func pause_game():
    """Pause the game"""
    if current_state == GameState.PLAYING:
        change_state(GameState.PAUSED)

func resume_game():
    """Resume the game"""
    if current_state == GameState.PAUSED:
        change_state(GameState.PLAYING)

func restart_game():
    """Restart the game"""
    get_tree().reload_current_scene()
'''
        return script
    
    def generate_event_system(self) -> str:
        """Generate an event-driven communication system"""
        
        script = '''extends Node

## ============================================
## PROFESSIONAL EVENT SYSTEM
## Decoupled communication between game systems
## ============================================

# Event bus singleton
signal player_died
signal player_health_changed(new_health, max_health)
signal player_score_changed(new_score)
signal collectible_collected(item_type, value)
signal obstacle_hit(obstacle_type, damage)
signal level_complete
signal game_over(final_score)
signal power_up_activated(power_type, duration)

# Event listeners dictionary
var event_listeners: Dictionary = {}

func _ready():
    # Make this a singleton/autoload
    pass

func subscribe(event_name: String, callback: Callable):
    """Subscribe to an event"""
    if not event_listeners.has(event_name):
        event_listeners[event_name] = []
    event_listeners[event_name].append(callback)

func unsubscribe(event_name: String, callback: Callable):
    """Unsubscribe from an event"""
    if event_listeners.has(event_name):
        event_listeners[event_name].erase(callback)

func emit_event(event_name: String, data: Variant = null):
    """Emit an event to all subscribers"""
    if event_listeners.has(event_name):
        for callback in event_listeners[event_name]:
            if callback.is_valid():
                if data != null:
                    callback.call(data)
                else:
                    callback.call()

# Convenience methods for common events
func notify_player_died():
    emit_signal("player_died")
    emit_event("player_died")

func notify_health_changed(new_health: int, max_health: int):
    emit_signal("player_health_changed", new_health, max_health)
    emit_event("player_health_changed", {"health": new_health, "max_health": max_health})

func notify_score_changed(new_score: int):
    emit_signal("player_score_changed", new_score)
    emit_event("player_score_changed", new_score)

func notify_collectible_collected(item_type: String, value: int):
    emit_signal("collectible_collected", item_type, value)
    emit_event("collectible_collected", {"type": item_type, "value": value})
'''
        return script
    
    def generate_physics_manager(self, game_design: Dict[str, Any]) -> str:
        """Generate a physics manager for consistent physics behavior"""
        
        dimension = game_design.get('dimension', '2D')
        is_3d = dimension == '3D'
        
        if is_3d:
            script = '''extends Node

## ============================================
## PROFESSIONAL PHYSICS MANAGER (3D)
## Manages physics layers, collision detection, and physics settings
## ============================================

# Physics layers (bit flags)
enum PhysicsLayer {
    PLAYER = 1,
    OBSTACLES = 2,
    COLLECTIBLES = 4,
    GROUND = 8,
    ENEMIES = 16,
    PROJECTILES = 32
}

# Collision masks
const PLAYER_MASK = PhysicsLayer.OBSTACLES | PhysicsLayer.GROUND | PhysicsLayer.ENEMIES
const OBSTACLE_MASK = PhysicsLayer.PLAYER
const COLLECTIBLE_MASK = PhysicsLayer.PLAYER
const GROUND_MASK = PhysicsLayer.PLAYER | PhysicsLayer.ENEMIES

func _ready():
    setup_physics_layers()

func setup_physics_layers():
    """Configure physics layers in project settings"""
    # This should be done in project.godot, but we can verify here
    pass

func get_layer_name(layer: PhysicsLayer) -> String:
    """Get human-readable layer name"""
    match layer:
        PhysicsLayer.PLAYER:
            return "Player"
        PhysicsLayer.OBSTACLES:
            return "Obstacles"
        PhysicsLayer.COLLECTIBLES:
            return "Collectibles"
        PhysicsLayer.GROUND:
            return "Ground"
        PhysicsLayer.ENEMIES:
            return "Enemies"
        PhysicsLayer.PROJECTILES:
            return "Projectiles"
        _:
            return "Unknown"

func is_valid_collision(layer_a: int, layer_b: int) -> bool:
    """Check if two layers should collide"""
    return (layer_a & layer_b) != 0
'''
        else:
            script = '''extends Node

## ============================================
## PROFESSIONAL PHYSICS MANAGER (2D)
## Manages physics layers, collision detection, and physics settings
## ============================================

# Physics layers (bit flags)
enum PhysicsLayer {
    PLAYER = 1,
    OBSTACLES = 2,
    COLLECTIBLES = 4,
    GROUND = 8,
    ENEMIES = 16,
    PROJECTILES = 32
}

# Collision masks
const PLAYER_MASK = PhysicsLayer.OBSTACLES | PhysicsLayer.GROUND | PhysicsLayer.ENEMIES
const OBSTACLE_MASK = PhysicsLayer.PLAYER
const COLLECTIBLE_MASK = PhysicsLayer.PLAYER
const GROUND_MASK = PhysicsLayer.PLAYER | PhysicsLayer.ENEMIES

func _ready():
    setup_physics_layers()

func setup_physics_layers():
    """Configure physics layers in project settings"""
    pass

func get_layer_name(layer: PhysicsLayer) -> String:
    """Get human-readable layer name"""
    match layer:
        PhysicsLayer.PLAYER:
            return "Player"
        PhysicsLayer.OBSTACLES:
            return "Obstacles"
        PhysicsLayer.COLLECTIBLES:
            return "Collectibles"
        PhysicsLayer.GROUND:
            return "Ground"
        PhysicsLayer.ENEMIES:
            return "Enemies"
        PhysicsLayer.PROJECTILES:
            return "Projectiles"
        _:
            return "Unknown"
'''
        return script
    
    def generate_audio_manager(self) -> str:
        """Generate an audio manager for sound effects and music"""
        
        script = '''extends Node

## ============================================
## PROFESSIONAL AUDIO MANAGER
## Handles sound effects, music, and audio settings
## ============================================

@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var sfx_player: AudioStreamPlayer = $SFXPlayer

var master_volume: float = 1.0
var music_volume: float = 0.7
var sfx_volume: float = 1.0

func _ready():
    # Create audio players if they don't exist
    if not music_player:
        music_player = AudioStreamPlayer.new()
        music_player.name = "MusicPlayer"
        add_child(music_player)
    
    if not sfx_player:
        sfx_player = AudioStreamPlayer.new()
        sfx_player.name = "SFXPlayer"
        add_child(sfx_player)
    
    update_volumes()

func play_music(stream: AudioStream, loop: bool = true):
    """Play background music"""
    if music_player:
        music_player.stream = stream
        music_player.volume_db = linear_to_db(music_volume * master_volume)
        if loop:
            music_player.stream.set_loop(true)
        music_player.play()

func play_sfx(stream: AudioStream, volume_scale: float = 1.0):
    """Play sound effect"""
    if sfx_player:
        sfx_player.stream = stream
        sfx_player.volume_db = linear_to_db(sfx_volume * master_volume * volume_scale)
        sfx_player.play()

func stop_music():
    """Stop background music"""
    if music_player:
        music_player.stop()

func set_master_volume(volume: float):
    """Set master volume (0.0 to 1.0)"""
    master_volume = clamp(volume, 0.0, 1.0)
    update_volumes()

func set_music_volume(volume: float):
    """Set music volume (0.0 to 1.0)"""
    music_volume = clamp(volume, 0.0, 1.0)
    update_volumes()

func set_sfx_volume(volume: float):
    """Set SFX volume (0.0 to 1.0)"""
    sfx_volume = clamp(volume, 0.0, 1.0)
    update_volumes()

func update_volumes():
    """Update all audio player volumes"""
    if music_player:
        music_player.volume_db = linear_to_db(music_volume * master_volume)
    if sfx_player:
        sfx_player.volume_db = linear_to_db(sfx_volume * master_volume)
'''
        return script
    
    def generate_pool_manager(self, object_type: str = "obstacle") -> str:
        """Generate an object pooling system for performance"""
        
        script = f'''extends Node

## ============================================
## PROFESSIONAL OBJECT POOL MANAGER
## Reuses objects for better performance
## ============================================

var pool_size: int = 20
var active_objects: Array = []
var inactive_objects: Array = []
var object_scene: PackedScene = null

func _ready():
    initialize_pool()

func initialize_pool():
    """Pre-instantiate objects for pooling"""
    for i in range(pool_size):
        var obj = create_object()
        obj.visible = false
        obj.set_process(false)
        obj.set_physics_process(false)
        inactive_objects.append(obj)
        add_child(obj)

func create_object() -> Node:
    """Create a new object instance"""
    # This should be overridden or set via set_object_scene()
    if object_scene:
        return object_scene.instantiate()
    else:
        # Fallback: create basic node
        var obj = Node.new()
        obj.name = "{object_type}_pooled"
        return obj

func set_object_scene(scene: PackedScene):
    """Set the scene to use for pooling"""
    object_scene = scene

func get_object() -> Node:
    """Get an object from the pool"""
    var obj: Node
    
    if inactive_objects.size() > 0:
        obj = inactive_objects.pop_back()
    else:
        # Pool exhausted, create new one
        obj = create_object()
        add_child(obj)
    
    active_objects.append(obj)
    obj.visible = true
    obj.set_process(true)
    obj.set_physics_process(true)
    
    return obj

func return_object(obj: Node):
    """Return an object to the pool"""
    if obj in active_objects:
        active_objects.erase(obj)
        inactive_objects.append(obj)
        obj.visible = false
        obj.set_process(false)
        obj.set_physics_process(false)
        # Reset object state
        if obj.has_method("reset"):
            obj.reset()

func clear_pool():
    """Clear all objects from the pool"""
    for obj in active_objects:
        obj.queue_free()
    for obj in inactive_objects:
        obj.queue_free()
    active_objects.clear()
    inactive_objects.clear()
'''
        return script

