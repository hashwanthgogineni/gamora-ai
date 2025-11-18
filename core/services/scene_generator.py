"""
Godot Scene Generator
Creates .tscn (Godot scene) files from AI-generated level designs
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SceneGenerator:
    """
    Generate Godot scene files (.tscn) from AI content
    Supports both 2D and 3D games
    """
    
    def __init__(self):
        self.resource_counter = 1
    
    def generate_main_scene(
        self,
        game_design: Dict[str, Any],
        level_design: Dict[str, Any]
    ) -> str:
        """Generate the main game scene using AI-generated level design"""
        
        # Check if this should be a 3D game
        dimension = game_design.get('dimension', '2D')
        genre = game_design.get('genre', 'platformer')
        game_style = game_design.get('game_style', '')
        
        # Normalize dimension: Convert 4D/5D to 3D, ensure only 2D or 3D
        if dimension and isinstance(dimension, str):
            dimension_upper = dimension.upper()
            if '4D' in dimension_upper or '5D' in dimension_upper or dimension_upper in ['4', '5', '6', '7', '8', '9']:
                logger.info(f"Converting {dimension} to 3D (only 2D and 3D supported)")
                dimension = '3D'
            elif dimension_upper not in ['2D', '3D', '2', '3']:
                dimension = '2D'  # Default to 2D if invalid
        
        # Detect 3D games
        is_3d = (
            dimension == '3D' or 
            dimension == '3' or
            '3d' in game_style.lower() or 
            '3d' in genre.lower() or
            ('runner' in genre.lower() and ('3d' in game_style.lower() or 'subway' in game_style.lower() or 'temple' in game_style.lower()))
        )
        
        # Ensure 2D if explicitly requested
        is_2d = (
            dimension == '2D' or 
            dimension == '2' or
            '2d' in game_style.lower() or
            'pixel art' in game_style.lower() or
            'side-scrolling' in game_style.lower()
        )
        
        if is_2d:
            is_3d = False
        
        if is_3d:
            return self.generate_3d_scene(game_design, level_design)
        
        # Default to 2D
        return self.generate_2d_scene(game_design, level_design)
    
    def generate_2d_scene(
        self,
        game_design: Dict[str, Any],
        level_design: Dict[str, Any]
    ) -> str:
        """Generate a 2D game scene"""
        
        # Extract level data from AI-generated level_design
        # Try to get first level or use main level data
        levels = level_design.get('levels', [])
        if levels and len(levels) > 0:
            # Use first level's data
            level_data = levels[0]
            platforms = level_data.get('platforms', [])
            collectibles = level_data.get('collectibles', [])
            spawn_point = level_data.get('spawn_point', [100, 400])
        else:
            # Fallback to default if no level data
            platforms = []
            collectibles = []
            spawn_point = [100, 400]
        
        # Generate platforms and collectibles from AI data
        platforms_data = self._parse_platforms_from_level(platforms)
        collectibles_data = self._parse_collectibles_from_level(collectibles)
        
        # Generate collectibles SubResources and nodes
        collectibles_subresources, collectibles_nodes = self._generate_collectibles_nodes_from_data(collectibles_data)
        
        # Generate platform SubResources and nodes dynamically
        platforms_subresources, platforms_nodes = self._generate_platforms_from_data(platforms_data)
        
        # Count total load_steps
        num_platforms = len(platforms_data) if platforms_data else 3
        num_collectibles = len(collectibles_data) if collectibles_data else 6
        total_load_steps = 7 + num_platforms + num_collectibles
        
        # Get spawn point coordinates
        spawn_x, spawn_y = spawn_point[0], spawn_point[1]
        
        scene = f'''[gd_scene load_steps={total_load_steps} format=3 uid="uid://main_scene"]

[ext_resource type="Script" path="res://scripts/player/player.gd" id="1"]
[ext_resource type="Script" path="res://scripts/managers/game_manager.gd" id="2"]
[ext_resource type="Script" path="res://scripts/camera_controller.gd" id="3"]
[ext_resource type="Texture2D" path="res://assets/sprites/player.png" id="4"]
[ext_resource type="Texture2D" path="res://assets/sprites/platform.png" id="5"]
[ext_resource type="Script" path="res://scripts/items/collectible.gd" id="6"]
[ext_resource type="Texture2D" path="res://assets/sprites/platform.png" id="7"]

[sub_resource type="RectangleShape2D" id="player_collision"]
size = Vector2(48, 48)

{platforms_subresources}

{collectibles_subresources}

[node name="Main" type="Node2D"]

[node name="Background" type="ColorRect" parent="."]
offset_right = 1920.0
offset_bottom = 1080.0
color = Color(0.2, 0.3, 0.5, 1)

[node name="GameManager" type="Node" parent="."]
script = ExtResource("2")

[node name="Player" type="CharacterBody2D" parent="."]
position = Vector2({spawn_x}, {spawn_y})
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="Player"]
texture = ExtResource("4")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("player_collision")

[node name="Camera2D" type="Camera2D" parent="Player"]
script = ExtResource("3")
zoom = Vector2(1.5, 1.5)
position_smoothing_enabled = true

[node name="Level" type="Node2D" parent="."]

{platforms_nodes.rstrip()}

[node name="Collectibles" type="Node2D" parent="."]
{collectibles_nodes.rstrip()}

[node name="UI" type="CanvasLayer" parent="."]

[node name="ScoreLabel" type="Label" parent="UI"]
offset_left = 20.0
offset_top = 20.0
offset_right = 200.0
offset_bottom = 60.0
text = "Score: 0"
theme_override_font_sizes/font_size = 24

[node name="HealthLabel" type="Label" parent="UI"]
offset_left = 20.0
offset_top = 60.0
offset_right = 200.0
offset_bottom = 100.0
text = "Health: 100"
theme_override_font_sizes/font_size = 24
'''
        
        return scene
    
    def generate_3d_scene(
        self,
        game_design: Dict[str, Any],
        level_design: Dict[str, Any]
    ) -> str:
        """Generate a professional 3D game scene (for runners, 3D platformers, etc.)"""
        
        # Extract level data
        levels = level_design.get('levels', [])
        spawn_patterns = level_design.get('spawn_patterns', [])
        lane_config = level_design.get('lane_configuration', 3)
        genre = game_design.get('genre', 'endless_runner')
        
        is_runner = 'runner' in genre.lower()
        
        # For 3D runners, we need a professional scene structure
        scene = f'''[gd_scene load_steps=45 format=3 uid="uid://3d_main_scene"]

[ext_resource type="Script" path="res://scripts/player/player_3d.gd" id="1"]
[ext_resource type="Script" path="res://scripts/managers/game_manager.gd" id="2"]
[ext_resource type="Script" path="res://scripts/camera_controller_3d.gd" id="3"]

[sub_resource type="ProceduralSkyMaterial" id="sky_material"]
sky_top_color = Color(0.4, 0.6, 0.9, 1)
sky_horizon_color = Color(0.6, 0.8, 1.0, 1)
ground_bottom_color = Color(0.3, 0.4, 0.5, 1)
ground_horizon_color = Color(0.5, 0.6, 0.7, 1)
sun_angle_max = 45.0

[sub_resource type="Sky" id="sky"]
sky_material = SubResource("sky_material")

[sub_resource type="Environment" id="environment"]
background_mode = 2
sky = SubResource("sky")
ambient_light_source = 2
ambient_light_color = Color(0.9, 0.9, 1.0, 1)
ambient_light_energy = 0.4
fog_enabled = true
fog_light_color = Color(0.8, 0.85, 0.9, 1)
fog_sun_color = Color(1, 0.95, 0.9, 1)
fog_density = 0.01
fog_aerial_perspective = 0.5
tonemap_mode = 2
tonemap_white = 1.5

[sub_resource type="CapsuleMesh" id="player_mesh"]
radius = 0.4
height = 1.8
radial_segments = 16
rings = 8

[sub_resource type="CapsuleShape3D" id="player_collision"]
radius = 0.4
height = 1.8

[sub_resource type="BoxMesh" id="lane_mesh"]
size = Vector3(2.2, 0.15, 200)

[sub_resource type="BoxShape3D" id="lane_collision"]
size = Vector3(2.2, 0.15, 200)

[sub_resource type="StandardMaterial3D" id="lane_material"]
albedo_color = Color(0.4, 0.4, 0.45, 1)
metallic = 0.1
roughness = 0.8
metallic_specular = 0.5

[sub_resource type="StandardMaterial3D" id="player_material"]
albedo_color = Color(0.2, 0.7, 1.0, 1)
metallic = 0.3
roughness = 0.4
metallic_specular = 0.8
emission_enabled = true
emission = Color(0.1, 0.3, 0.5, 1)
emission_energy_multiplier = 0.3

[sub_resource type="StandardMaterial3D" id="lane_center_material"]
albedo_color = Color(0.5, 0.5, 0.55, 1)
metallic = 0.05
roughness = 0.9

[sub_resource type="StandardMaterial3D" id="lane_edge_material"]
albedo_color = Color(0.9, 0.9, 0.2, 1)
emission_enabled = true
emission = Color(0.9, 0.9, 0.2, 1)
emission_energy_multiplier = 1.5

[sub_resource type="BoxMesh" id="lane_edge_mesh"]
size = Vector3(0.1, 0.2, 200)

[sub_resource type="Gradient" id="trail_emission"]
offsets = PackedFloat32Array(0, 1)
colors = PackedColorArray(1, 1, 1, 1, 1, 1, 1, 0)

[sub_resource type="ParticleProcessMaterial" id="trail_particle_material"]
direction = Vector3(0, 1, 0)
initial_velocity_min = 0.5
initial_velocity_max = 1.0
gravity = Vector3(0, -2, 0)
scale_min = 0.1
scale_max = 0.3
color = Color(0.2, 0.7, 1, 0.8)
emission = SubResource("trail_emission")

[sub_resource type="QuadMesh" id="trail_particle_mesh"]
size = Vector2(0.2, 0.2)

[sub_resource type="StyleBoxFlat" id="ui_panel_style"]
bg_color = Color(0, 0, 0, 0.7)
border_width_left = 2
border_width_top = 2
border_width_right = 2
border_width_bottom = 2
border_color = Color(0.2, 0.7, 1, 1)
corner_radius_top_left = 8
corner_radius_top_right = 8
corner_radius_bottom_right = 8
corner_radius_bottom_left = 8

[node name="Main" type="Node3D"]

[node name="WorldEnvironment" type="WorldEnvironment" parent="."]
environment = SubResource("environment")

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.707107, 0.707107, 0, -0.707107, 0.707107, 0, 12, 0)
light_color = Color(1, 0.98, 0.95, 1)
shadow_enabled = true
shadow_opacity = 0.7
directional_shadow_mode = 1
directional_shadow_max_distance = 50.0

[node name="OmniLight3D" type="OmniLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 8, 0)
light_color = Color(0.8, 0.85, 1.0, 1)
light_energy = 0.5
shadow_enabled = true

[node name="GameManager" type="Node" parent="."]
script = ExtResource("2")

[node name="Player" type="CharacterBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0)
collision_layer = 1
collision_mask = 1
script = ExtResource("1")

[node name="MeshInstance3D" type="MeshInstance3D" parent="Player"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
mesh = SubResource("player_mesh")
surface_material_override/0 = SubResource("player_material")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Player"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
shape = SubResource("player_collision")

[node name="TrailParticles" type="GPUParticles3D" parent="Player"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.5, 0)
emitting = true
amount = 50
lifetime = 0.5
one_shot = false
preprocess = 0.0
speed_scale = 1.0
explosiveness = 0.0
randomness = 0.0
visibility_aabb = AABB(-1, -1, -1, 2, 2, 2)
process_material = SubResource("trail_particle_material")
draw_pass_1 = SubResource("trail_particle_mesh")

[node name="Camera3D" type="Camera3D" parent="Player"]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 3, 5)
fov = 75.0
script = ExtResource("3")

[node name="Track" type="Node3D" parent="."]

[node name="Lane1" type="StaticBody3D" parent="Track"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2, 0, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Track/Lane1"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
mesh = SubResource("lane_mesh")
surface_material_override/0 = SubResource("lane_material")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Track/Lane1"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
shape = SubResource("lane_collision")

[node name="LeftEdge" type="MeshInstance3D" parent="Track/Lane1"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="RightEdge" type="MeshInstance3D" parent="Track/Lane1"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="Lane2" type="StaticBody3D" parent="Track"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Track/Lane2"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
mesh = SubResource("lane_mesh")
surface_material_override/0 = SubResource("lane_center_material")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Track/Lane2"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
shape = SubResource("lane_collision")

[node name="LeftEdge" type="MeshInstance3D" parent="Track/Lane2"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="RightEdge" type="MeshInstance3D" parent="Track/Lane2"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="Lane3" type="StaticBody3D" parent="Track"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2, 0, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Track/Lane3"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
mesh = SubResource("lane_mesh")
surface_material_override/0 = SubResource("lane_material")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Track/Lane3"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
shape = SubResource("lane_collision")

[node name="LeftEdge" type="MeshInstance3D" parent="Track/Lane3"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="RightEdge" type="MeshInstance3D" parent="Track/Lane3"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.1, 0.1, 0)
mesh = SubResource("lane_edge_mesh")
surface_material_override/0 = SubResource("lane_edge_material")

[node name="Obstacles" type="Node3D" parent="."]

[node name="Collectibles" type="Node3D" parent="."]

[node name="UI" type="CanvasLayer" parent="."]

[node name="ScorePanel" type="Panel" parent="UI"]
offset_left = 20.0
offset_top = 20.0
offset_right = 320.0
offset_bottom = 80.0
theme_override_styles/panel = SubResource("ui_panel_style")

[node name="ScoreLabel" type="Label" parent="UI/ScorePanel"]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 20.0
offset_top = 10.0
offset_right = -20.0
offset_bottom = -10.0
text = "Score: 0"
horizontal_alignment = 1
theme_override_font_sizes/font_size = 36
theme_override_colors/font_color = Color(1, 1, 1, 1)
theme_override_colors/font_shadow_color = Color(0, 0, 0, 0.5)
theme_override_constants/shadow_offset_x = 2
theme_override_constants/shadow_offset_y = 2

[node name="HealthPanel" type="Panel" parent="UI"]
offset_left = 20.0
offset_top = 90.0
offset_right = 320.0
offset_bottom = 150.0
theme_override_styles/panel = SubResource("ui_panel_style")

[node name="HealthLabel" type="Label" parent="UI/HealthPanel"]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 20.0
offset_top = 10.0
offset_right = -20.0
offset_bottom = -10.0
text = "Health: 100"
horizontal_alignment = 1
theme_override_font_sizes/font_size = 36
theme_override_colors/font_color = Color(1, 1, 1, 1)
theme_override_colors/font_shadow_color = Color(0, 0, 0, 0.5)
theme_override_constants/shadow_offset_x = 2
theme_override_constants/shadow_offset_y = 2
'''
        
        return scene
    
    def _parse_platforms_from_level(self, platforms: List) -> List[Dict]:
        """Parse platform data from level design"""
        if not platforms:
            # Return default platforms if none provided
            return [
                {"position": [400, 500], "size": [256, 64]},
                {"position": [700, 400], "size": [256, 64]},
                {"position": [500, 600], "size": [1000, 64]}  # Ground
            ]
        
        parsed = []
        for platform in platforms:
            if isinstance(platform, list) and len(platform) >= 2:
                # Format: [x, y, width, height] or [x, y]
                if len(platform) >= 4:
                    parsed.append({
                        "position": [platform[0], platform[1]],
                        "size": [platform[2], platform[3]]
                    })
                else:
                    parsed.append({
                        "position": [platform[0], platform[1]],
                        "size": [256, 64]  # Default size
                    })
            elif isinstance(platform, dict):
                parsed.append(platform)
        
        # Ensure at least one ground platform
        if not any(p.get("position", [0])[1] > 550 for p in parsed if isinstance(p.get("position"), list)):
            parsed.append({"position": [500, 600], "size": [1000, 64]})
        
        return parsed
    
    def _parse_collectibles_from_level(self, collectibles: List) -> List[Dict]:
        """Parse collectible data from level design"""
        if not collectibles:
            return [
                {"position": [300, 450], "type": "coin"},
                {"position": [450, 350], "type": "coin"},
                {"position": [600, 350], "type": "coin"},
                {"position": [750, 300], "type": "coin"},
                {"position": [900, 250], "type": "coin"},
                {"position": [400, 200], "type": "coin"}
            ]
        
        parsed = []
        for item in collectibles:
            if isinstance(item, list) and len(item) >= 2:
                # Format: [x, y, type] or [x, y]
                item_type = item[2] if len(item) >= 3 else "coin"
                parsed.append({
                    "position": [item[0], item[1]],
                    "type": item_type
                })
            elif isinstance(item, dict):
                parsed.append(item)
        
        return parsed
    
    def _generate_collectibles_nodes_from_data(self, collectibles_data: List[Dict]) -> tuple[str, str]:
        """Generate collectible nodes from parsed data"""
        if not collectibles_data:
            return self._generate_collectibles_nodes()
        
        # Define all SubResources first
        sub_resources = ""
        for i in range(1, len(collectibles_data) + 1):
            sub_resources += f'''[sub_resource type="CircleShape2D" id="circle_shape_{i}"]
radius = 16.0
'''
        
        # Then define nodes
        nodes = ""
        for i, item in enumerate(collectibles_data, 1):
            pos = item.get("position", [0, 0])
            if isinstance(pos, list):
                x, y = pos[0], pos[1]
            else:
                x, y = 0, 0
            
            nodes += f'''
[node name="Collectible{i}" type="Area2D" parent="Collectibles"]
position = Vector2({x}, {y})
script = ExtResource("6")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Collectibles/Collectible{i}"]
shape = SubResource("circle_shape_{i}")

[node name="Sprite2D" type="Sprite2D" parent="Collectibles/Collectible{i}"]
texture = ExtResource("7")
modulate = Color(1, 0.85, 0, 1)
'''
        
        return sub_resources, nodes
    
    def _generate_platforms_from_data(self, platforms_data: List[Dict]) -> tuple[str, str]:
        """Generate platform nodes from parsed data"""
        if not platforms_data:
            # Use default platforms
            platforms_data = [
                {"position": [400, 500], "size": [256, 64]},
                {"position": [700, 400], "size": [256, 64]},
                {"position": [500, 600], "size": [1000, 64]}  # Ground
            ]
        
        # Define all SubResources first
        sub_resources = ""
        for i, platform in enumerate(platforms_data, 1):
            size = platform.get("size", [256, 64])
            if isinstance(size, list):
                width, height = size[0], size[1]
            else:
                width, height = 256, 64
            sub_resources += f'''[sub_resource type="RectangleShape2D" id="platform_shape_{i}"]
size = Vector2({width}, {height})
'''
        
        # Then define nodes
        nodes = ""
        for i, platform in enumerate(platforms_data, 1):
            pos = platform.get("position", [0, 0])
            size = platform.get("size", [256, 64])
            if isinstance(pos, list):
                x, y = pos[0], pos[1]
            else:
                x, y = 0, 0
            if isinstance(size, list):
                width, height = size[0], size[1]
            else:
                width, height = 256, 64
            
            platform_name = "Ground" if y > 550 else f"Platform{i}"
            nodes += f'''
[node name="{platform_name}" type="StaticBody2D" parent="Level"]
position = Vector2({x}, {y})

[node name="Sprite2D" type="Sprite2D" parent="Level/{platform_name}"]
texture = ExtResource("5")
region_enabled = true
region_rect = Rect2(0, 0, {width}, {height})

[node name="CollisionShape2D" type="CollisionShape2D" parent="Level/{platform_name}"]
shape = SubResource("platform_shape_{i}")
'''
        
        return sub_resources, nodes
    
    def _generate_collectibles_nodes(self) -> tuple[str, str]:
        """Generate collectible item nodes
        
        Returns:
            tuple: (sub_resources_string, nodes_string)
        """
        
        positions = [
            (300, 450), (450, 350), (600, 350),
            (750, 300), (900, 250), (400, 200)
        ]
        
        # Define all SubResources first (return separately)
        sub_resources = ""
        for i, (x, y) in enumerate(positions, 1):
            sub_resources += f'''[sub_resource type="CircleShape2D" id="circle_shape_{i}"]
radius = 16.0
'''
        
        # Then define nodes that use them
        nodes = ""
        for i, (x, y) in enumerate(positions, 1):
            nodes += f'''[node name="Collectible{i}" type="Area2D" parent="Collectibles"]
position = Vector2({x}, {y})
script = ExtResource("6")

[node name="Sprite2D" type="Sprite2D" parent="Collectibles/Collectible{i}"]
texture = ExtResource("7")
modulate = Color(1, 0.85, 0, 1)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Collectibles/Collectible{i}"]
shape = SubResource("circle_shape_{i}")

'''
        
        return sub_resources, nodes
    
    def generate_level_scene(
        self,
        level_number: int,
        level_data: Dict[str, Any]
    ) -> str:
        """Generate a specific level scene"""
        
        platforms = level_data.get('platforms', [])
        enemies = level_data.get('enemies', [])
        collectibles = level_data.get('collectibles', [])
        
        scene = f'''[gd_scene load_steps=5 format=3 uid="uid://level_{level_number}"]

[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="1"]
[ext_resource type="Texture2D" path="res://assets/sprites/platform.png" id="2"]
[ext_resource type="Texture2D" path="res://assets/sprites/enemy.png" id="3"]

[node name="Level{level_number}" type="Node2D"]

[node name="Player" parent="." instance=ExtResource("1")]
position = Vector2(100, 400)

[node name="Platforms" type="Node2D" parent="."]
{self._generate_platforms(platforms)}

[node name="Enemies" type="Node2D" parent="."]
{self._generate_enemies(enemies)}

[node name="Collectibles" type="Node2D" parent="."]
{self._generate_level_collectibles(collectibles)}
'''
        
        return scene
    
    def _generate_platforms(self, platforms: List[Dict]) -> str:
        """Generate platform nodes from level data"""
        
        if not platforms:
            # Default platforms
            platforms = [
                {"position": [400, 500], "size": [256, 64]},
                {"position": [700, 400], "size": [256, 64]},
                {"position": [500, 600], "size": [1000, 64]}  # Ground
            ]
        
        platform_nodes = ""
        # Define all SubResources first
        for i, platform in enumerate(platforms, 1):
            size = platform.get('size', [128, 32])
            platform_nodes += f'''
[sub_resource type="RectangleShape2D" id="platform_shape_{i}"]
size = Vector2({size[0]}, {size[1]})
'''
        
        # Then define nodes that use them
        for i, platform in enumerate(platforms, 1):
            pos = platform.get('position', [0, 0])
            size = platform.get('size', [128, 32])
            
            platform_nodes += f'''
[node name="Platform{i}" type="StaticBody2D" parent="Platforms"]
position = Vector2({pos[0]}, {pos[1]})

[node name="CollisionShape2D" type="CollisionShape2D" parent="Platforms/Platform{i}"]
shape = SubResource("platform_shape_{i}")

[node name="Sprite2D" type="Sprite2D" parent="Platforms/Platform{i}"]
modulate = Color(0.3, 0.6, 0.3, 1)
region_enabled = true
region_rect = Rect2(0, 0, {size[0]}, {size[1]})
'''
        
        return platform_nodes
    
    def _generate_enemies(self, enemies: List[Dict]) -> str:
        """Generate enemy nodes from level data"""
        
        if not enemies:
            # Default enemies
            enemies = [
                {"position": [500, 450], "type": "patrol"},
                {"position": [800, 350], "type": "patrol"}
            ]
        
        enemy_nodes = ""
        # Define all SubResources first
        for i, enemy in enumerate(enemies, 1):
            enemy_nodes += f'''
[sub_resource type="RectangleShape2D" id="enemy_shape_{i}"]
size = Vector2(48, 48)
'''
        
        # Then define nodes that use them
        for i, enemy in enumerate(enemies, 1):
            pos = enemy.get('position', [0, 0])
            
            enemy_nodes += f'''
[node name="Enemy{i}" type="CharacterBody2D" parent="Enemies"]
position = Vector2({pos[0]}, {pos[1]})
script = ExtResource("enemy_script")

[node name="Sprite2D" type="Sprite2D" parent="Enemies/Enemy{i}"]
texture = ExtResource("3")
modulate = Color(1, 0.3, 0.3, 1)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Enemies/Enemy{i}"]
shape = SubResource("enemy_shape_{i}")
'''
        
        return enemy_nodes
    
    def _generate_level_collectibles(self, collectibles: List[Dict]) -> str:
        """Generate collectible nodes for level"""
        
        if not collectibles:
            # Default collectibles
            collectibles = [
                {"position": [300, 450], "type": "coin"},
                {"position": [450, 350], "type": "coin"},
                {"position": [600, 350], "type": "coin"}
            ]
        
        collectible_nodes = ""
        # Define all SubResources first
        for i, item in enumerate(collectibles, 1):
            collectible_nodes += f'''
[sub_resource type="CircleShape2D" id="collectible_shape_{i}"]
radius = 16.0
'''
        
        # Then define nodes that use them
        for i, item in enumerate(collectibles, 1):
            pos = item.get('position', [0, 0])
            
            collectible_nodes += f'''
[node name="Collectible{i}" type="Area2D" parent="Collectibles"]
position = Vector2({pos[0]}, {pos[1]})
script = ExtResource("collectible_script")

[node name="Sprite2D" type="Sprite2D" parent="Collectibles/Collectible{i}"]
modulate = Color(1, 0.85, 0, 1)

[node name="CollisionShape2D" type="CollisionShape2D" parent="Collectibles/Collectible{i}"]
shape = SubResource("collectible_shape_{i}")
'''
        
        return collectible_nodes
    
    def generate_menu_scene(self, game_design: Dict[str, Any]) -> str:
        """Generate main menu scene"""
        
        title = game_design.get('title', 'Gamora AI Game')
        
        scene = f'''[gd_scene load_steps=2 format=3 uid="uid://menu"]

[node name="MainMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.15, 0.2, 0.3, 1)

[node name="VBoxContainer" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -150.0
offset_top = -150.0
offset_right = 150.0
offset_bottom = 150.0

[node name="Title" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "{title}"
theme_override_font_sizes/font_size = 48
horizontal_alignment = 1

[node name="Spacer" type="Control" parent="VBoxContainer"]
custom_minimum_size = Vector2(0, 50)
layout_mode = 2

[node name="PlayButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "PLAY"
theme_override_font_sizes/font_size = 32

[node name="QuitButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "QUIT"
theme_override_font_sizes/font_size = 32

[connection signal="pressed" from="VBoxContainer/PlayButton" to="." method="_on_play_button_pressed"]
[connection signal="pressed" from="VBoxContainer/QuitButton" to="." method="_on_quit_button_pressed"]
'''
        
        return scene
    
    def generate_game_over_scene(self) -> str:
        """Generate game over scene"""
        
        scene = '''[gd_scene load_steps=1 format=3]

[node name="GameOver" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.1, 0.1, 0.1, 0.9)

[node name="VBoxContainer" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -150.0
offset_top = -100.0
offset_right = 150.0
offset_bottom = 100.0

[node name="Label" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "GAME OVER"
theme_override_font_sizes/font_size = 48
horizontal_alignment = 1

[node name="ScoreLabel" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "Final Score: 0"
theme_override_font_sizes/font_size = 32
horizontal_alignment = 1

[node name="RestartButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "RESTART"
theme_override_font_sizes/font_size = 24

[node name="MenuButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "MAIN MENU"
theme_override_font_sizes/font_size = 24
'''
        
        return scene
    
    def generate_victory_scene(self) -> str:
        """Generate victory/win scene"""
        
        scene = '''[gd_scene load_steps=1 format=3]

[node name="Victory" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.1, 0.3, 0.1, 0.9)

[node name="VBoxContainer" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -150.0
offset_top = -100.0
offset_right = 150.0
offset_bottom = 100.0

[node name="Label" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "VICTORY!"
theme_override_font_sizes/font_size = 48
horizontal_alignment = 1
theme_override_colors/font_color = Color(0, 1, 0, 1)

[node name="ScoreLabel" type="Label" parent="VBoxContainer"]
layout_mode = 2
text = "Final Score: 0"
theme_override_font_sizes/font_size = 32
horizontal_alignment = 1

[node name="NextButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "NEXT LEVEL"
theme_override_font_sizes/font_size = 24

[node name="MenuButton" type="Button" parent="VBoxContainer"]
layout_mode = 2
text = "MAIN MENU"
theme_override_font_sizes/font_size = 24
'''
        
        return scene
    
    def generate_all_scenes(
        self,
        game_design: Dict[str, Any],
        level_design: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate all game scenes
        
        Returns:
            Dictionary mapping scene paths to scene content
        """
        
        scenes = {
            "scenes/main.tscn": self.generate_main_scene(game_design, level_design),
            "scenes/ui/main_menu.tscn": self.generate_menu_scene(game_design),
            "scenes/ui/game_over.tscn": self.generate_game_over_scene(),
            "scenes/ui/victory.tscn": self.generate_victory_scene()
        }
        
        # Generate level scenes
        levels = level_design.get('levels', [])
        for i, level in enumerate(levels, 1):
            scene_path = f"scenes/levels/level_{i}.tscn"
            scenes[scene_path] = self.generate_level_scene(i, level)
        
        logger.info(f"✅ Generated {len(scenes)} scene files")
        return scenes
