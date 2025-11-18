"""
GDScript Generator Service
Converts AI-generated game mechanics into working GDScript code
"""

import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class GDScriptGenerator:
    """
    Generate GDScript files from AI-generated game mechanics
    Creates player scripts, enemy AI, game managers, and more
    """
    
    def generate_player_script(self, mechanics: Dict[str, Any], game_design: Dict[str, Any] = None) -> str:
        """Generate refined player controller script with professional game feel"""
        
        # Check if this should be 3D
        dimension = game_design.get('dimension', '2D') if game_design else '2D'
        genre = game_design.get('genre', 'platformer') if game_design else 'platformer'
        
        is_3d = (
            dimension == '3D' or 
            '3d' in genre.lower() or
            'runner' in genre.lower()
        )
        
        if is_3d:
            return self.generate_3d_player_script(mechanics, game_design)
        
        # 2D player script
        movement = mechanics.get('player_movement', {})
        abilities = mechanics.get('player_abilities', ['jump', 'move'])
        
        # Extract and validate movement values with proper defaults
        speed = movement.get('speed', 300.0)
        jump_force = movement.get('jump_force', -400.0)
        acceleration = movement.get('acceleration', 1500.0)
        friction = movement.get('friction', 1200.0)
        
        # Validate and clamp values to prevent broken mechanics
        # Speed should be reasonable (100-600)
        speed = max(100.0, min(600.0, float(speed)))
        # Jump force should be negative and reasonable (-200 to -600)
        jump_force = max(-600.0, min(-200.0, float(jump_force)))
        # Acceleration should be high enough for responsive movement (1000-3000)
        acceleration = max(1000.0, min(3000.0, float(acceleration)))
        # Friction should be high enough to stop quickly (800-2000)
        friction = max(800.0, min(2000.0, float(friction)))
        
        script = f'''extends CharacterBody2D

## ============================================
## REFINED PLAYER CONTROLLER
## Professional game feel with modern mechanics
## ============================================

# Movement Constants
const SPEED: float = {speed}
const JUMP_VELOCITY: float = {jump_force}
const ACCELERATION: float = {acceleration}
const FRICTION: float = {friction}
const GRAVITY: float = 980.0
const MAX_FALL_SPEED: float = 1000.0

# Advanced Movement Features
const COYOTE_TIME: float = 0.15  # Time after leaving ground where jump still works
const JUMP_BUFFER_TIME: float = 0.1  # Time before landing where jump input is remembered
const AIR_CONTROL: float = 0.6  # Movement control in air (0.0-1.0)
const VARIABLE_JUMP_MULTIPLIER: float = 0.5  # Jump height reduction on early release

# Player State
var health: int = 100
var score: int = 0
var is_invulnerable: bool = false
var power_ups: Array = []

# Advanced Jump Mechanics
var coyote_timer: float = 0.0
var jump_buffer_timer: float = 0.0
var was_on_floor: bool = false
var is_jumping: bool = false
var jump_released: bool = true

# Visual Feedback
@onready var sprite: Sprite2D = $Sprite2D if has_node("Sprite2D") else null

# Signals
signal health_changed(new_health)
signal score_changed(new_score)
signal player_died()
signal landed()
signal jumped()

func _ready():
    add_to_group("player")
    was_on_floor = is_on_floor()

func _physics_process(delta):
    # Update timers
    coyote_timer -= delta
    jump_buffer_timer -= delta
    
    # Track floor state for coyote time
    var on_floor_now = is_on_floor()
    if on_floor_now and not was_on_floor:
        # Just landed
        emit_signal("landed")
        is_jumping = false
        coyote_timer = COYOTE_TIME
    elif not on_floor_now and was_on_floor:
        # Just left ground
        coyote_timer = COYOTE_TIME
        is_jumping = true
    
    was_on_floor = on_floor_now
    
    # Apply gravity with max fall speed
    if not on_floor_now:
        velocity.y += GRAVITY * delta
        velocity.y = min(velocity.y, MAX_FALL_SPEED)
    else:
        velocity.y = 0
        is_jumping = false
    
    # Variable jump height - reduce jump if button released early
    if is_jumping and velocity.y < 0:
        if jump_released:
            velocity.y += GRAVITY * VARIABLE_JUMP_MULTIPLIER * delta
    
    # Get input direction
    var input_direction = Input.get_axis("ui_left", "ui_right")
    
    # Fallback for web compatibility
    if input_direction == 0:
        if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
            input_direction = -1.0
        if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
            input_direction = 1.0
    
    # Apply movement with air control
    var control_factor = 1.0 if on_floor_now else AIR_CONTROL
    var target_speed = input_direction * SPEED
    
    if input_direction != 0:
        velocity.x = move_toward(velocity.x, target_speed, ACCELERATION * control_factor * delta)
        # Flip sprite based on direction
        if sprite:
            sprite.flip_h = input_direction < 0
    else:
        velocity.x = move_toward(velocity.x, 0, FRICTION * control_factor * delta)
    
    # Handle jump input
    var jump_pressed = Input.is_action_pressed("ui_accept") or Input.is_action_pressed("jump") or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)
    var jump_just_pressed = Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("jump")
    
    # Fallback for direct key detection
    if not jump_just_pressed:
        var space_just = Input.is_key_pressed(KEY_SPACE) and not has_meta("space_held")
        var w_just = Input.is_key_pressed(KEY_W) and not has_meta("w_held")
        var up_just = Input.is_key_pressed(KEY_UP) and not has_meta("up_held")
        
        if space_just or w_just or up_just:
            jump_just_pressed = true
            set_meta("space_held", true)
            set_meta("w_held", true)
            set_meta("up_held", true)
        
        if not Input.is_key_pressed(KEY_SPACE):
            remove_meta("space_held")
        if not Input.is_key_pressed(KEY_W):
            remove_meta("w_held")
        if not Input.is_key_pressed(KEY_UP):
            remove_meta("up_held")
    
    # Track jump release for variable jump
    if not jump_pressed:
        jump_released = true
    else:
        jump_released = false
    
    # Jump buffer - remember jump input before landing
    if jump_just_pressed:
        jump_buffer_timer = JUMP_BUFFER_TIME
    
    # Execute jump if conditions are met
    if jump_buffer_timer > 0:
        if on_floor_now or coyote_timer > 0:
            velocity.y = JUMP_VELOCITY
            jump_buffer_timer = 0
            coyote_timer = 0
            is_jumping = true
            jump_released = false
            emit_signal("jumped")
    
    move_and_slide()

func take_damage(amount: int):
    if is_invulnerable:
        return
    
    health = max(0, health - amount)
    emit_signal("health_changed", health)
    
    if health <= 0:
        die()
    else:
        # Temporary invulnerability with visual feedback
        is_invulnerable = true
        _start_invulnerability_effect()
        await get_tree().create_timer(1.0).timeout
        is_invulnerable = false
        _stop_invulnerability_effect()

func _start_invulnerability_effect():
    # Visual feedback for invulnerability (flashing effect)
    if sprite:
        var tween = create_tween()
        tween.set_loops(10)
        tween.tween_property(sprite, "modulate:a", 0.5, 0.1)
        tween.tween_property(sprite, "modulate:a", 1.0, 0.1)

func _stop_invulnerability_effect():
    if sprite:
        sprite.modulate.a = 1.0

func add_score(points: int):
    score += points
    emit_signal("score_changed", score)

func collect_item(item_type: String):
    match item_type:
        "coin":
            add_score(10)
        "gem":
            add_score(50)
        "health":
            health = min(health + 25, 100)
            emit_signal("health_changed", health)
        "power_up":
            power_ups.append(item_type)
            _apply_power_up(item_type)

func _apply_power_up(power_type: String):
    match power_type:
        "speed_boost":
            pass
        "double_jump":
            pass

func die():
    emit_signal("player_died")
    await get_tree().create_timer(0.5).timeout
    queue_free()
'''
        
        return script
    
    def generate_3d_player_script(self, mechanics: Dict[str, Any], game_design: Dict[str, Any] = None) -> str:
        """Generate professional 3D player controller for runners/3D games"""
        
        movement = mechanics.get('player_movement', {})
        genre = game_design.get('genre', 'endless_runner') if game_design else 'endless_runner'
        
        # For 3D runners, use different defaults
        forward_speed = movement.get('speed', 500.0)  # Forward movement speed
        lane_switch_speed = movement.get('lane_switch_speed', 800.0)  # Lateral movement
        jump_force = movement.get('jump_force', 8.0)  # Positive for 3D
        slide_duration = movement.get('slide_duration', 0.5)
        
        # Validate values
        forward_speed = max(300.0, min(800.0, float(forward_speed)))
        lane_switch_speed = max(500.0, min(1200.0, float(lane_switch_speed)))
        jump_force = max(6.0, min(12.0, float(jump_force)))
        
        is_runner = 'runner' in genre.lower()
        
        if is_runner:
            # Endless runner style (like Subway Surfers)
            script = f'''extends CharacterBody3D

## ============================================
## PROFESSIONAL 3D RUNNER CONTROLLER
## Subway Surfers / Temple Run style
## ============================================

# Movement Constants
const FORWARD_SPEED: float = {forward_speed}
const LANE_SWITCH_SPEED: float = {lane_switch_speed}
const JUMP_FORCE: float = {jump_force}
const GRAVITY: float = 20.0
const LANE_WIDTH: float = 2.0

# Lane positions (3 lanes: left, center, right)
const LANES: Array[float] = [-2.0, 0.0, 2.0]

# Player State
var current_lane: int = 1  # Start in center lane (0=left, 1=center, 2=right)
var target_lane_x: float = 0.0
var is_jumping: bool = false
var is_sliding: bool = false
var slide_timer: float = 0.0
var health: int = 100
var score: int = 0

# Input state tracking to prevent multiple triggers per frame
var left_key_was_pressed: bool = false
var right_key_was_pressed: bool = false
var jump_key_was_pressed: bool = false
var slide_key_was_pressed: bool = false

# Signals
signal health_changed(new_health)
signal score_changed(new_score)
signal player_died()

@onready var mesh_instance: MeshInstance3D = $MeshInstance3D
@onready var animation_player: AnimationPlayer = $AnimationPlayer if has_node("AnimationPlayer") else null

func _ready():
    add_to_group("player")
    target_lane_x = LANES[current_lane]

func _physics_process(delta):
    # Always move forward
    velocity.z = -FORWARD_SPEED
    
    # Handle lane switching with smooth interpolation
    var current_x = global_position.x
    if abs(current_x - target_lane_x) > 0.05:
        var direction = sign(target_lane_x - current_x)
        velocity.x = direction * LANE_SWITCH_SPEED
    else:
        velocity.x = 0
        global_position.x = target_lane_x
    
    # Handle jumping
    if not is_on_floor():
        velocity.y -= GRAVITY * delta
    else:
        if is_jumping:
            is_jumping = false
        velocity.y = 0
    
    # Handle sliding
    if is_sliding:
        slide_timer -= delta
        if slide_timer <= 0:
            is_sliding = false
    
    # Input handling - swipe controls for web
    handle_input()
    
    # Check for collisions with obstacles
    check_obstacle_collisions()
    
    move_and_slide()
    
    # Check for collectible collisions (after movement)
    check_collectible_collisions()

func check_obstacle_collisions():
    """Check if player collides with obstacles"""
    for i in range(get_slide_collision_count()):
        var collision = get_slide_collision(i)
        var collider = collision.get_collider()
        
        if collider and (collider.is_in_group("obstacles") or collider.name.begins_with("Obstacle_")):
            # Hit an obstacle - take damage
            take_damage(10)
            # Push player back slightly to prevent getting stuck
            var push_back = -collision.get_normal() * 1.5
            global_position += push_back
            # Destroy the obstacle
            if is_instance_valid(collider):
                collider.queue_free()

func check_collectible_collisions():
    """Check if player overlaps with collectibles using Area3D detection"""
    # Collectibles use Area3D body_entered signal, but we also check here as backup
    var space_state = get_world_3d().direct_space_state
    if not space_state:
        return
    
    var query = PhysicsShapeQueryParameters3D.new()
    var collision_shape = $CollisionShape3D
    if not collision_shape or not collision_shape.shape:
        return
    
    query.shape = collision_shape.shape
    query.transform = global_transform
    query.collision_mask = 2  # Check collectible layer
    
    var results = space_state.intersect_shape(query, 10)
    for result in results:
        var collider = result.collider
        if collider and collider.is_in_group("collectibles") and not collider.get("collected"):
            # Collect the item
            collect_item("coin")
            add_score(10)
            if is_instance_valid(collider):
                collider.set("collected", true)
                collider.queue_free()

func handle_input():
    # Left/Right movement - only trigger on NEW press (not held)
    var left_pressed = Input.is_action_just_pressed("ui_left") or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A)
    var right_pressed = Input.is_action_just_pressed("ui_right") or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)
    
    # Only switch lane if key was JUST pressed (not held from previous frame)
    if left_pressed and not left_key_was_pressed:
        switch_lane(-1)
    if right_pressed and not right_key_was_pressed:
        switch_lane(1)
    
    left_key_was_pressed = left_pressed
    right_key_was_pressed = right_pressed
    
    # Jump - only trigger on NEW press
    var jump_pressed = (Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("jump") or 
        Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP))
    
    if jump_pressed and not jump_key_was_pressed and is_on_floor() and not is_jumping:
        jump()
    
    jump_key_was_pressed = jump_pressed
    
    # Slide - only trigger on NEW press
    var slide_pressed = Input.is_action_just_pressed("ui_down") or Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN)
    
    if slide_pressed and not slide_key_was_pressed and is_on_floor() and not is_sliding:
        slide()
    
    slide_key_was_pressed = slide_pressed

func switch_lane(direction: int):
    """Switch to adjacent lane"""
    var new_lane = current_lane + direction
    new_lane = clamp(new_lane, 0, LANES.size() - 1)
    
    if new_lane != current_lane:
        current_lane = new_lane
        target_lane_x = LANES[current_lane]

func jump():
    """Jump action"""
    if is_on_floor() and not is_sliding:
        velocity.y = JUMP_FORCE
        is_jumping = true
        if animation_player:
            animation_player.play("jump")

func slide():
    """Slide action (duck under obstacles)"""
    if is_on_floor() and not is_jumping:
        is_sliding = true
        slide_timer = {slide_duration}
        # Scale down collision shape
        if animation_player:
            animation_player.play("slide")

func take_damage(amount: int):
    health = max(0, health - amount)
    emit_signal("health_changed", health)
    
    if health <= 0:
        die()

func add_score(points: int):
    score += points
    emit_signal("score_changed", score)

func collect_item(item_type: String):
    match item_type:
        "coin":
            add_score(10)
        "gem":
            add_score(50)
        "power_up":
            # Speed boost, magnet, etc.
            pass

func die():
    emit_signal("player_died")
    # Stop forward movement
    velocity.z = 0
'''
        else:
            # 3D platformer style
            script = f'''extends CharacterBody3D

## ============================================
## PROFESSIONAL 3D PLATFORMER CONTROLLER
## 3D movement with proper physics
## ============================================

# Movement Constants
const SPEED: float = {forward_speed}
const JUMP_VELOCITY: float = {jump_force}
const ACCELERATION: float = 20.0
const FRICTION: float = 15.0
const GRAVITY: float = 20.0

# Player State
var health: int = 100
var score: int = 0

# Signals
signal health_changed(new_health)
signal score_changed(new_score)
signal player_died()

@onready var mesh_instance: MeshInstance3D = $MeshInstance3D

func _ready():
    add_to_group("player")

func _physics_process(delta):
    # Apply gravity
    if not is_on_floor():
        velocity.y -= GRAVITY * delta
    else:
        velocity.y = 0
    
    # Get input direction
    var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    # Apply movement
    if direction:
        velocity.x = move_toward(velocity.x, direction.x * SPEED, ACCELERATION * delta)
        velocity.z = move_toward(velocity.z, direction.z * SPEED, ACCELERATION * delta)
    else:
        velocity.x = move_toward(velocity.x, 0, FRICTION * delta)
        velocity.z = move_toward(velocity.z, 0, FRICTION * delta)
    
    # Handle jump
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    
    move_and_slide()

func take_damage(amount: int):
    health = max(0, health - amount)
    emit_signal("health_changed", health)
    
    if health <= 0:
        die()

func add_score(points: int):
    score += points
    emit_signal("score_changed", score)

func die():
    emit_signal("player_died")
'''
        
        return script
    
    def generate_enemy_script(self, mechanics: Dict[str, Any]) -> str:
        """Generate enemy AI script"""
        
        enemy_behaviors = mechanics.get('enemy_behaviors', ['patrol', 'chase'])
        
        script = '''extends CharacterBody2D

## ============================================
## REFINED ENEMY AI
## Professional state machine with smooth behavior
## ============================================

enum State { PATROL, CHASE, ATTACK, IDLE, RETURN }

# Enemy Properties
@export var health: int = 50
@export var patrol_speed: float = 100.0
@export var chase_speed: float = 150.0
@export var detection_range: float = 300.0
@export var attack_range: float = 50.0
@export var attack_damage: int = 10
@export var patrol_points: Array[Vector2] = []
@export var attack_cooldown: float = 1.0

var current_state: State = State.PATROL
var current_patrol_index: int = 0
var player: CharacterBody2D = null
var gravity: float = 980.0
var attack_timer: float = 0.0
var start_position: Vector2
var last_seen_player_pos: Vector2

@onready var sprite: Sprite2D = $Sprite2D if has_node("Sprite2D") else null

func _ready():
    add_to_group("enemies")
    start_position = global_position
    # Find player
    await get_tree().process_frame
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        player = players[0]

func _physics_process(delta):
    # Update timers
    attack_timer -= delta
    
    # Apply gravity
    if not is_on_floor():
        velocity.y += gravity * delta
    else:
        velocity.y = 0
    
    # Update state machine
    update_state()
    
    # Execute current state behavior
    match current_state:
        State.PATROL:
            patrol_behavior(delta)
        State.CHASE:
            chase_behavior(delta)
        State.ATTACK:
            attack_behavior(delta)
        State.IDLE:
            idle_behavior(delta)
        State.RETURN:
            return_behavior(delta)
    
    # Flip sprite based on movement direction
    if sprite and velocity.x != 0:
        sprite.flip_h = velocity.x < 0
    
    move_and_slide()

func update_state():
    if not player:
        current_state = State.PATROL
        return
    
    var distance_to_player = global_position.distance_to(player.global_position)
    
    if distance_to_player <= attack_range and attack_timer <= 0:
        current_state = State.ATTACK
        last_seen_player_pos = player.global_position
    elif distance_to_player <= detection_range:
        current_state = State.CHASE
        last_seen_player_pos = player.global_position
    else:
        # Return to patrol if player is far
        if current_state == State.CHASE:
            current_state = State.RETURN
        else:
            current_state = State.PATROL

func patrol_behavior(delta):
    if patrol_points.is_empty():
        velocity.x = 0
        return
    
    var target = patrol_points[current_patrol_index]
    var direction = sign(target.x - global_position.x)
    
    # Smooth movement
    velocity.x = move_toward(velocity.x, direction * patrol_speed, 500.0 * delta)
    
    if abs(global_position.x - target.x) < 10:
        current_patrol_index = (current_patrol_index + 1) % patrol_points.size()

func chase_behavior(delta):
    if not player:
        return
    
    var direction = sign(player.global_position.x - global_position.x)
    velocity.x = move_toward(velocity.x, direction * chase_speed, 800.0 * delta)

func attack_behavior(delta):
    velocity.x = move_toward(velocity.x, 0, 1000.0 * delta)
    # Attack logic handled by collision
    if attack_timer <= 0:
        attack_timer = attack_cooldown

func return_behavior(delta):
    # Return to start position
    var direction = sign(start_position.x - global_position.x)
    velocity.x = move_toward(velocity.x, direction * patrol_speed, 500.0 * delta)
    
    if abs(global_position.x - start_position.x) < 20:
        current_state = State.PATROL

func idle_behavior(delta):
    velocity.x = move_toward(velocity.x, 0, 1000.0 * delta)

func take_damage(amount: int):
    health -= amount
    # Visual feedback
    if sprite:
        sprite.modulate = Color.RED
        await get_tree().create_timer(0.1).timeout
        sprite.modulate = Color.WHITE
    
    if health <= 0:
        die()

func die():
    # Drop items, play animation, etc.
    queue_free()

func _on_hitbox_body_entered(body):
    if body.is_in_group("player") and attack_timer <= 0:
        body.take_damage(attack_damage)
        attack_timer = attack_cooldown
'''
        
        return script
    
    def generate_game_manager_script(self, mechanics: Dict[str, Any], design: Dict[str, Any]) -> str:
        """Generate main game manager script"""
        
        scoring = mechanics.get('scoring_system', 'Points per item')
        win_condition = design.get('win_condition', 'Collect all items')
        dimension = design.get('dimension', '2D')
        genre = design.get('genre', 'platformer')
        is_3d = dimension == '3D' or '3d' in genre.lower()
        is_runner = 'runner' in genre.lower()
        
        # Determine player type
        player_type = "CharacterBody3D" if is_3d else "CharacterBody2D"
        
        # Convert boolean to GDScript boolean string
        runner_bool = "true" if is_runner else "false"
        
        script = f'''extends Node

## ============================================
## REFINED GAME MANAGER
## Professional game state management
## ============================================

# Game State
var current_level: int = 1
var total_score: int = 0
var game_over: bool = false
var game_won: bool = false
var time_elapsed: float = 0.0
var best_time: float = 0.0

# Level tracking
var collectibles_total: int = 0
var collectibles_collected: int = 0

# Performance tracking
var frame_count: int = 0
var fps: float = 60.0

# References
var player: {player_type}
var ui_manager: Node

# Signals
signal game_started()
signal game_over_triggered()
signal game_won_triggered()
signal level_completed()
signal collectible_collected(total: int, collected: int)

func _ready():
    # Find player and UI
    await get_tree().process_frame
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        player = players[0]
        if player.has_signal("health_changed"):
            player.connect("health_changed", _on_player_health_changed)
        if player.has_signal("score_changed"):
            player.connect("score_changed", _on_player_score_changed)
        if player.has_signal("player_died"):
            player.connect("player_died", _on_player_died)
    
    # Find UI manager to update labels directly
    ui_manager = get_node_or_null("/root/Main/UI")
    if not ui_manager:
        ui_manager = get_node_or_null("UI")
    
    # Update UI labels directly if found
    if ui_manager:
        var score_label = ui_manager.get_node_or_null("ScoreLabel")
        var health_label = ui_manager.get_node_or_null("HealthLabel")
        if score_label:
            score_label.text = "Score: 0"
        if health_label:
            health_label.text = "Health: 100"
    
    # Initialize spawning for runners
    if {runner_bool}:
        start_obstacle_spawning()
        start_collectible_spawning()
    
    # Count collectibles
    count_collectibles()
    emit_signal("game_started")

func _process(delta):
    if not game_over and not game_won:
        time_elapsed += delta
    
    # Calculate FPS for performance monitoring
    frame_count += 1
    if frame_count % 60 == 0:
        fps = 1.0 / delta if delta > 0 else 60.0

func count_collectibles():
    var items = get_tree().get_nodes_in_group("collectibles")
    collectibles_total = items.size()
    collectibles_collected = 0

func start_obstacle_spawning():
    """Start spawning obstacles for runner games"""
    # Spawn obstacles periodically
    var spawn_timer = Timer.new()
    spawn_timer.wait_time = 2.0  # Spawn every 2 seconds
    spawn_timer.timeout.connect(_spawn_obstacle)
    spawn_timer.autostart = true
    add_child(spawn_timer)

func start_collectible_spawning():
    """Start spawning collectibles for runner games"""
    # Spawn collectibles periodically
    var spawn_timer = Timer.new()
    spawn_timer.wait_time = 1.5  # Spawn every 1.5 seconds
    spawn_timer.timeout.connect(_spawn_collectible)
    spawn_timer.autostart = true
    add_child(spawn_timer)

func _spawn_obstacle():
    """Spawn an obstacle ahead of the player"""
    if not player or game_over:
        return
    
    var obstacles_node = get_node_or_null("/root/Main/Obstacles")
    if not obstacles_node:
        return
    
    # Create obstacle with professional look and movement script
    var obstacle = CharacterBody3D.new()  # Use CharacterBody3D so it can move
    obstacle.name = "Obstacle_" + str(randi())
    obstacle.add_to_group("obstacles")
    
    # Create mesh (taller, more visible)
    var mesh_instance = MeshInstance3D.new()
    var box_mesh = BoxMesh.new()
    box_mesh.size = Vector3(0.8, 2.0, 0.8)
    mesh_instance.mesh = box_mesh
    
    # Create professional material with metallic/roughness
    var material = StandardMaterial3D.new()
    material.albedo_color = Color(0.8, 0.1, 0.1, 1)  # Dark red
    material.metallic = 0.3
    material.roughness = 0.6
    material.emission_enabled = true
    material.emission = Color(1, 0.2, 0.2, 0.3)
    material.emission_energy_multiplier = 0.5
    mesh_instance.set_surface_override_material(0, material)
    
    # Create collision
    var collision = CollisionShape3D.new()
    var box_shape = BoxShape3D.new()
    box_shape.size = Vector3(0.8, 2.0, 0.8)
    collision.shape = box_shape
    
    obstacle.add_child(mesh_instance)
    obstacle.add_child(collision)
    
    # Add movement script to obstacle (moves backward toward player)
    # Create inline script for obstacle movement
    var obstacle_script = GDScript.new()
    obstacle_script.source_code = """
extends CharacterBody3D

var forward_speed: float = 500.0

func _ready():
    var player = get_node_or_null("/root/Main/Player")
    if player:
        # Get player's forward speed constant
        var player_script = player.get_script()
        if player_script and player_script.has_constant("FORWARD_SPEED"):
            forward_speed = player_script.get_constant("FORWARD_SPEED")
        elif player.has_constant("FORWARD_SPEED"):
            forward_speed = player.get("FORWARD_SPEED")
    add_to_group("obstacles")

func _physics_process(delta):
    # Move backward (toward player) at same speed as player moves forward
    velocity.z = forward_speed
    move_and_slide()
    
    # Remove if too far behind player
    var player = get_node_or_null("/root/Main/Player")
    if player and global_position.z > player.global_position.z + 20:
        queue_free()
"""
    obstacle.set_script(obstacle_script)
    
    # Position ahead of player in random lane
    var lanes = [-2.0, 0.0, 2.0]
    var lane = lanes[randi() % lanes.size()]
    obstacle.global_position = Vector3(lane, 0.75, player.global_position.z - 30)
    
    obstacles_node.add_child(obstacle)

func _spawn_collectible():
    """Spawn a collectible ahead of the player"""
    if not player or game_over:
        return
    
    var collectibles_node = get_node_or_null("/root/Main/Collectibles")
    if not collectibles_node:
        return
    
    # Create collectible with professional look and movement
    var collectible = Area3D.new()
    collectible.name = "Collectible_" + str(randi())
    collectible.add_to_group("collectibles")
    collectible.monitoring = true
    collectible.monitorable = true
    collectible.collision_layer = 2  # Set collision layer
    collectible.collision_mask = 1   # Detect player layer
    
    # Create mesh (larger, more visible)
    var mesh_instance = MeshInstance3D.new()
    var sphere_mesh = SphereMesh.new()
    sphere_mesh.radius = 0.4
    sphere_mesh.height = 0.8
    sphere_mesh.radial_segments = 16
    sphere_mesh.rings = 12
    mesh_instance.mesh = sphere_mesh
    
    # Create professional gold material with metallic properties
    var material = StandardMaterial3D.new()
    material.albedo_color = Color(1, 0.84, 0, 1)  # Gold
    material.metallic = 0.8
    material.roughness = 0.2
    material.metallic_specular = 0.9
    material.emission_enabled = true
    material.emission = Color(1, 0.9, 0.3, 1)
    material.emission_energy_multiplier = 2.0
    mesh_instance.set_surface_override_material(0, material)
    
    # Create collision
    var collision = CollisionShape3D.new()
    var sphere_shape = SphereShape3D.new()
    sphere_shape.radius = 0.4
    collision.shape = sphere_shape
    
    collectible.add_child(mesh_instance)
    collectible.add_child(collision)
    
    # Add movement script to collectible
    var collectible_script = GDScript.new()
    collectible_script.source_code = """
extends Area3D

var forward_speed: float = 500.0
var rotation_speed: float = 2.0
var bob_speed: float = 3.0
var bob_amount: float = 0.2
var start_y: float
var time: float = 0.0
var collected: bool = false

func _ready():
    start_y = global_position.y
    var player = get_node_or_null("/root/Main/Player")
    if player:
        # Get player's forward speed constant
        var player_script = player.get_script()
        if player_script and player_script.has_constant("FORWARD_SPEED"):
            forward_speed = player_script.get_constant("FORWARD_SPEED")
        elif player.has_constant("FORWARD_SPEED"):
            forward_speed = player.get("FORWARD_SPEED")
    body_entered.connect(_on_body_entered)

func _process(delta):
    if collected:
        return
    
    time += delta
    
    # Move backward (toward player) at same speed as player moves forward
    global_position.z += forward_speed * delta
    
    # Bobbing animation
    global_position.y = start_y + sin(time * bob_speed) * bob_amount
    
    # Rotation animation
    rotate_y(rotation_speed * delta)
    
    # Remove if too far behind player
    var player = get_node_or_null("/root/Main/Player")
    if player and global_position.z > player.global_position.z + 20:
        queue_free()

func _on_body_entered(body):
    if body and body.is_in_group("player") and not collected:
        collected = true
        # Call game manager to handle collection
        var game_manager = get_node_or_null("/root/Main/GameManager")
        if game_manager and game_manager.has_method("_on_collectible_collected"):
            game_manager._on_collectible_collected(self, body)
        elif game_manager and game_manager.has_method("collect_item"):
            game_manager.collect_item()
        # Also notify player if it has add_score method
        if body.has_method("add_score"):
            body.add_score(10)
        queue_free()
"""
    collectible.set_script(collectible_script)
    
    # Position ahead of player in random lane
    var lanes = [-2.0, 0.0, 2.0]
    var lane = lanes[randi() % lanes.size()]
    collectible.global_position = Vector3(lane, 1.5, player.global_position.z - 25)
    
    collectibles_node.add_child(collectible)

func _on_collectible_collected(collectible: Area3D, body: Node):
    """Handle collectible collection"""
    if body.is_in_group("player"):
        collect_item()
        if player and player.has_method("add_score"):
            player.add_score(10)
        collectible.queue_free()

func _on_player_health_changed(new_health):
    # Update UI directly
    if ui_manager:
        var health_label = ui_manager.get_node_or_null("HealthLabel")
        if health_label:
            health_label.text = "Health: " + str(new_health)
        # Also try UI manager method if it exists
        if ui_manager.has_method("update_health"):
            ui_manager.update_health(new_health)

func _on_player_score_changed(new_score):
    total_score = new_score
    # Update UI directly
    if ui_manager:
        var score_label = ui_manager.get_node_or_null("ScoreLabel")
        if score_label:
            score_label.text = "Score: " + str(new_score)
        # Also try UI manager method if it exists
        if ui_manager.has_method("update_score"):
            ui_manager.update_score(new_score)

func _on_player_died():
    trigger_game_over()

func collect_item():
    collectibles_collected += 1
    emit_signal("collectible_collected", collectibles_total, collectibles_collected)
    
    # Check win condition
    if collectibles_collected >= collectibles_total and collectibles_total > 0:
        check_win_condition()

func check_win_condition():
    game_won = true
    # Update best time if this is better
    if best_time == 0.0 or time_elapsed < best_time:
        best_time = time_elapsed
    emit_signal("game_won_triggered")
    emit_signal("level_completed")

func trigger_game_over():
    game_over = true
    emit_signal("game_over_triggered")

func restart_game():
    # Reset game state
    game_over = false
    game_won = false
    time_elapsed = 0.0
    collectibles_collected = 0
    get_tree().reload_current_scene()

func next_level():
    current_level += 1
    game_won = false
    collectibles_collected = 0
    time_elapsed = 0.0
    # Load next level scene
    # get_tree().change_scene_to_file("res://scenes/levels/level_" + str(current_level) + ".tscn")
'''
        
        return script
    
    def generate_collectible_script(self, mechanics: Dict[str, Any]) -> str:
        """Generate refined collectible item script with animations"""
        
        script = '''extends Area2D

## ============================================
## REFINED COLLECTIBLE SYSTEM
## Professional item collection with feedback
## ============================================

@export var item_type: String = "coin"
@export var points_value: int = 10
@export var auto_collect: bool = true
@export var rotation_speed: float = 2.0
@export var bob_speed: float = 3.0
@export var bob_amount: float = 10.0

signal item_collected(type, value)

var start_y: float
var time: float = 0.0
var collected: bool = false

@onready var sprite: Sprite2D = $Sprite2D if has_node("Sprite2D") else null

func _ready():
    add_to_group("collectibles")
    start_y = global_position.y
    body_entered.connect(_on_body_entered)
    
    # Start idle animation
    _start_idle_animation()

func _process(delta):
    if collected:
        return
    
    time += delta
    
    # Bobbing animation
    if sprite:
        var offset = sin(time * bob_speed) * bob_amount
        sprite.position.y = offset
        sprite.rotation += rotation_speed * delta

func _start_idle_animation():
    # Pulse/glow effect
    if sprite:
        var tween = create_tween()
        tween.set_loops()
        tween.tween_property(sprite, "scale", Vector2(1.1, 1.1), 0.5)
        tween.tween_property(sprite, "scale", Vector2(1.0, 1.0), 0.5)

func _on_body_entered(body):
    if collected:
        return
        
    if body.is_in_group("player") and auto_collect:
        collect(body)

func collect(player):
    if collected:
        return
    
    collected = true
    
    # Notify player
    if player.has_method("collect_item"):
        player.collect_item(item_type)
    
    # Notify game manager
    var game_manager = get_node_or_null("/root/Main/GameManager")
    if not game_manager:
        game_manager = get_node_or_null("/root/GameManager")
    if game_manager and game_manager.has_method("collect_item"):
        game_manager.collect_item()
    
    emit_signal("item_collected", item_type, points_value)
    
    # Collection animation
    _play_collect_animation()

func _play_collect_animation():
    # Scale up and fade out
    if sprite:
        var tween = create_tween()
        tween.parallel().tween_property(sprite, "scale", Vector2(1.5, 1.5), 0.2)
        tween.parallel().tween_property(sprite, "modulate:a", 0.0, 0.2)
        await tween.finished
    
    queue_free()
'''
        
        return script
    
    def generate_ui_manager_script(self) -> str:
        """Generate UI manager script"""
        
        script = '''extends CanvasLayer

# UI Elements
@onready var score_label = $ScoreLabel
@onready var health_label = $HealthLabel
@onready var game_over_panel = $GameOverPanel
@onready var victory_panel = $VictoryPanel

func _ready():
    # Hide panels initially
    if game_over_panel:
        game_over_panel.visible = false
    if victory_panel:
        victory_panel.visible = false
    
    # Connect to game manager
    var game_manager = get_node_or_null("/root/GameManager")
    if game_manager:
        game_manager.connect("game_over_triggered", _on_game_over)
        game_manager.connect("game_won_triggered", _on_game_won)

func update_score(score: int):
    if score_label:
        score_label.text = "Score: " + str(score)

func update_health(health: int):
    if health_label:
        health_label.text = "Health: " + str(health)

func _on_game_over():
    if game_over_panel:
        game_over_panel.visible = true

func _on_game_won():
    if victory_panel:
        victory_panel.visible = true

func _on_restart_button_pressed():
    get_tree().reload_current_scene()

func _on_menu_button_pressed():
    get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
'''
        
        return script
    
    def generate_camera_controller_script(self, game_design: Dict[str, Any] = None) -> str:
        """Generate camera controller that follows player"""
        
        # Check if 3D
        dimension = game_design.get('dimension', '2D') if game_design else '2D'
        is_3d = dimension == '3D' or '3d' in (game_design.get('genre', '') if game_design else '').lower()
        
        if is_3d:
            return self.generate_3d_camera_controller_script(game_design)
        
        # 2D camera
        
        script = '''extends Camera2D

@export var follow_speed: float = 5.0
@export var look_ahead: float = 50.0
@export var dead_zone: Vector2 = Vector2(50, 30)

var player: CharacterBody2D

func _ready():
    # Find player
    await get_tree().process_frame
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        player = players[0]

func _process(delta):
    if not player:
        return
    
    # Smooth camera follow with look-ahead
    var target_pos = player.global_position
    
    # Add look-ahead based on player velocity
    if player.velocity.x != 0:
        target_pos.x += sign(player.velocity.x) * look_ahead
    
    # Smooth camera movement
    global_position = global_position.lerp(target_pos, follow_speed * delta)
'''
        
        return script
    
    def generate_3d_camera_controller_script(self, game_design: Dict[str, Any] = None) -> str:
        """Generate 3D camera controller for runners/3D games"""
        
        genre = game_design.get('genre', 'endless_runner') if game_design else 'endless_runner'
        is_runner = 'runner' in genre.lower()
        
        if is_runner:
            # Follow-behind camera for runners (looks ahead, not at player)
            script = '''extends Camera3D

## ============================================
## 3D RUNNER CAMERA CONTROLLER
## Follows player from behind, looks ahead
## ============================================

@onready var player: CharacterBody3D = get_parent()
var follow_distance: float = 8.0
var follow_height: float = 4.0
var look_ahead_distance: float = 10.0
var smooth_speed: float = 8.0

func _ready():
    # Camera is already positioned in scene
    current = true  # Make this the active camera

func _process(delta):
    if not player:
        return
    
    # Follow player from behind and above
    var target_position = player.global_position + Vector3(0, follow_height, follow_distance)
    global_position = global_position.lerp(target_position, smooth_speed * delta)
    
    # Look ahead of player (forward direction for runner)
    var look_target = player.global_position + Vector3(0, 0, -look_ahead_distance)
    look_at(look_target, Vector3.UP)
'''
        else:
            # Free-look camera for 3D platformers
            script = '''extends Camera3D

## ============================================
## 3D PLATFORMER CAMERA CONTROLLER
## Follows player with smooth movement
## ============================================

@onready var player: CharacterBody3D = get_parent()
var follow_distance: float = 8.0
var follow_height: float = 4.0
var smooth_speed: float = 3.0

func _ready():
    pass

func _process(delta):
    if not player:
        return
    
    # Follow player from behind and above
    var target_position = player.global_position + Vector3(0, follow_height, follow_distance)
    global_position = global_position.lerp(target_position, smooth_speed * delta)
    
    # Look slightly ahead of player
    var look_target = player.global_position + player.velocity.normalized() * 2.0
    look_at(look_target, Vector3.UP)
'''
        
        return script
    
    def generate_all_scripts(
        self,
        game_design: Dict[str, Any],
        game_mechanics: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate all game scripts
        
        Returns:
            Dictionary mapping script paths to script content
        """
        
        # Determine script paths based on dimension
        dimension = game_design.get('dimension', '2D')
        is_3d = dimension == '3D' or '3d' in game_design.get('genre', '').lower()
        
        if is_3d:
            player_script_path = "scripts/player/player_3d.gd"
            camera_script_path = "scripts/camera_controller_3d.gd"
        else:
            player_script_path = "scripts/player/player.gd"
            camera_script_path = "scripts/camera_controller.gd"
        
        scripts = {
            player_script_path: self.generate_player_script(game_mechanics, game_design),
            "scripts/enemies/enemy.gd": self.generate_enemy_script(game_mechanics),
            "scripts/managers/game_manager.gd": self.generate_game_manager_script(game_mechanics, game_design),
            "scripts/managers/ui_manager.gd": self.generate_ui_manager_script(),
            "scripts/items/collectible.gd": self.generate_collectible_script(game_mechanics),
            camera_script_path: self.generate_camera_controller_script(game_design)
        }
        
        logger.info(f"✅ Generated {len(scripts)} GDScript files")
        return scripts
