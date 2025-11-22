"""
Comprehensive Game Genre Registry
All game genres that exist in the world, with metadata and characteristics
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GenreRegistry:
    """
    Registry of all game genres with their characteristics, mechanics, and requirements
    """
    
    # Comprehensive list of all game genres
    ALL_GENRES = {
        # Action Genres
        "action": {
            "name": "Action",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["combat", "movement", "reflexes"],
            "common_features": ["enemies", "weapons", "health", "power-ups"],
            "examples": ["Devil May Cry", "Bayonetta", "God of War"]
        },
        "platformer": {
            "name": "Platformer",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["jump", "run", "collect", "avoid"],
            "common_features": ["platforms", "collectibles", "enemies", "power-ups"],
            "examples": ["Super Mario", "Sonic", "Celeste", "Hollow Knight"]
        },
        "endless_runner": {
            "name": "Endless Runner",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["run", "jump", "slide", "dodge", "collect"],
            "common_features": ["obstacles", "collectibles", "power-ups", "score"],
            "examples": ["Subway Surfers", "Temple Run", "Canabalt", "Jetpack Joyride"]
        },
        "beat_em_up": {
            "name": "Beat 'em Up",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["combat", "combo", "special_moves"],
            "common_features": ["enemies", "health", "combos", "bosses"],
            "examples": ["Streets of Rage", "Double Dragon", "Final Fight"]
        },
        "hack_and_slash": {
            "name": "Hack and Slash",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["combat", "combo", "loot"],
            "common_features": ["weapons", "enemies", "loot", "upgrades"],
            "examples": ["Diablo", "Path of Exile", "Torchlight"]
        },
        "fighting": {
            "name": "Fighting",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["combat", "special_moves", "block"],
            "common_features": ["characters", "health", "rounds", "combos"],
            "examples": ["Street Fighter", "Tekken", "Mortal Kombat", "Super Smash Bros"]
        },
        
        # Shooter Genres
        "shooter": {
            "name": "Shooter",
            "category": "shooter",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["aim", "shoot", "reload", "cover"],
            "common_features": ["weapons", "ammo", "enemies", "health"],
            "examples": ["Call of Duty", "Counter-Strike", "Doom"]
        },
        "fps": {
            "name": "First-Person Shooter",
            "category": "shooter",
            "dimensions": ["3D"],
            "core_mechanics": ["aim", "shoot", "reload", "cover", "movement"],
            "common_features": ["weapons", "ammo", "enemies", "health", "crosshair"],
            "examples": ["Call of Duty", "Doom", "Half-Life", "Halo"]
        },
        "tps": {
            "name": "Third-Person Shooter",
            "category": "shooter",
            "dimensions": ["3D"],
            "core_mechanics": ["aim", "shoot", "cover", "movement"],
            "common_features": ["weapons", "ammo", "enemies", "health", "camera"],
            "examples": ["Gears of War", "The Division", "Tomb Raider"]
        },
        "bullet_hell": {
            "name": "Bullet Hell",
            "category": "shooter",
            "dimensions": ["2D"],
            "core_mechanics": ["dodge", "shoot", "pattern_recognition"],
            "common_features": ["bullets", "power-ups", "bosses", "score"],
            "examples": ["Touhou", "Ikaruga", "Enter the Gungeon"]
        },
        "twin_stick_shooter": {
            "name": "Twin-Stick Shooter",
            "category": "shooter",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["move", "shoot", "dodge"],
            "common_features": ["enemies", "power-ups", "score", "waves"],
            "examples": ["Geometry Wars", "Binding of Isaac", "Enter the Gungeon"]
        },
        
        # Puzzle Genres
        "puzzle": {
            "name": "Puzzle",
            "category": "puzzle",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["solve", "think", "pattern"],
            "common_features": ["puzzles", "levels", "hints", "score"],
            "examples": ["Tetris", "Portal", "The Witness", "Baba Is You"]
        },
        "match_3": {
            "name": "Match-3",
            "category": "puzzle",
            "dimensions": ["2D"],
            "core_mechanics": ["match", "swap", "combo", "clear"],
            "common_features": ["grid", "pieces", "power-ups", "levels"],
            "examples": ["Candy Crush", "Bejeweled", "Puzzle Quest"]
        },
        "tetris_like": {
            "name": "Tetris-like",
            "category": "puzzle",
            "dimensions": ["2D"],
            "core_mechanics": ["rotate", "place", "clear_lines"],
            "common_features": ["falling_blocks", "grid", "score", "speed"],
            "examples": ["Tetris", "Puyo Puyo", "Dr. Mario"]
        },
        "physics_puzzle": {
            "name": "Physics Puzzle",
            "category": "puzzle",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["physics", "solve", "manipulate"],
            "common_features": ["objects", "gravity", "constraints", "goals"],
            "examples": ["Angry Birds", "Cut the Rope", "World of Goo"]
        },
        "logic_puzzle": {
            "name": "Logic Puzzle",
            "category": "puzzle",
            "dimensions": ["2D"],
            "core_mechanics": ["deduce", "solve", "pattern"],
            "common_features": ["rules", "constraints", "solution", "hints"],
            "examples": ["Sudoku", "Picross", "The Witness"]
        },
        "escape_room": {
            "name": "Escape Room",
            "category": "puzzle",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["explore", "solve", "collect", "escape"],
            "common_features": ["clues", "items", "puzzles", "time"],
            "examples": ["The Room", "Myst", "Escape Simulator"]
        },
        
        # Strategy Genres
        "strategy": {
            "name": "Strategy",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["plan", "manage", "execute"],
            "common_features": ["resources", "units", "buildings", "objectives"],
            "examples": ["Civilization", "Age of Empires", "StarCraft"]
        },
        "rts": {
            "name": "Real-Time Strategy",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["build", "manage", "command", "expand"],
            "common_features": ["resources", "units", "buildings", "map"],
            "examples": ["StarCraft", "Age of Empires", "Command & Conquer"]
        },
        "tbs": {
            "name": "Turn-Based Strategy",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["plan", "execute", "wait"],
            "common_features": ["turns", "units", "resources", "map"],
            "examples": ["Civilization", "XCOM", "Fire Emblem"]
        },
        "tower_defense": {
            "name": "Tower Defense",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["place", "upgrade", "defend"],
            "common_features": ["towers", "waves", "enemies", "resources"],
            "examples": ["Plants vs Zombies", "Kingdom Rush", "Bloons TD"]
        },
        "city_builder": {
            "name": "City Builder",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["build", "manage", "expand", "optimize"],
            "common_features": ["buildings", "resources", "population", "zones"],
            "examples": ["SimCity", "Cities: Skylines", "Anno"]
        },
        
        # RPG Genres
        "rpg": {
            "name": "RPG",
            "category": "rpg",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["level", "equip", "quest", "explore"],
            "common_features": ["stats", "inventory", "quests", "npcs"],
            "examples": ["Final Fantasy", "The Elder Scrolls", "The Witcher"]
        },
        "jrpg": {
            "name": "JRPG",
            "category": "rpg",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["turn_based_combat", "level", "story", "explore"],
            "common_features": ["party", "stats", "quests", "story"],
            "examples": ["Final Fantasy", "Persona", "Dragon Quest"]
        },
        "action_rpg": {
            "name": "Action RPG",
            "category": "rpg",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["combat", "level", "loot", "explore"],
            "common_features": ["stats", "inventory", "skills", "enemies"],
            "examples": ["Diablo", "Dark Souls", "The Witcher"]
        },
        "roguelike": {
            "name": "Roguelike",
            "category": "rpg",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["permadeath", "procedural", "explore", "loot"],
            "common_features": ["dungeons", "items", "enemies", "random"],
            "examples": ["The Binding of Isaac", "Spelunky", "Hades"]
        },
        "roguelite": {
            "name": "Roguelite",
            "category": "rpg",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["permadeath", "meta_progression", "explore"],
            "common_features": ["runs", "upgrades", "random", "unlocks"],
            "examples": ["Hades", "Dead Cells", "Risk of Rain"]
        },
        
        # Adventure Genres
        "adventure": {
            "name": "Adventure",
            "category": "adventure",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["explore", "solve", "story", "interact"],
            "common_features": ["npcs", "items", "puzzles", "story"],
            "examples": ["The Legend of Zelda", "Tomb Raider", "Uncharted"]
        },
        "point_and_click": {
            "name": "Point and Click",
            "category": "adventure",
            "dimensions": ["2D"],
            "core_mechanics": ["click", "explore", "solve", "collect"],
            "common_features": ["items", "npcs", "puzzles", "inventory"],
            "examples": ["Monkey Island", "Grim Fandango", "Broken Age"]
        },
        "visual_novel": {
            "name": "Visual Novel",
            "category": "adventure",
            "dimensions": ["2D"],
            "core_mechanics": ["read", "choose", "story"],
            "common_features": ["text", "choices", "characters", "routes"],
            "examples": ["Doki Doki Literature Club", "Phoenix Wright", "Steins;Gate"]
        },
        "metroidvania": {
            "name": "Metroidvania",
            "category": "adventure",
            "dimensions": ["2D"],
            "core_mechanics": ["explore", "backtrack", "unlock", "upgrade"],
            "common_features": ["map", "abilities", "secrets", "bosses"],
            "examples": ["Metroid", "Castlevania", "Hollow Knight", "Ori"]
        },
        
        # Simulation Genres
        "simulation": {
            "name": "Simulation",
            "category": "simulation",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["simulate", "manage", "control"],
            "common_features": ["systems", "resources", "time", "realism"],
            "examples": ["The Sims", "Flight Simulator", "Euro Truck Simulator"]
        },
        "life_sim": {
            "name": "Life Simulation",
            "category": "simulation",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["manage", "interact", "customize", "live"],
            "common_features": ["characters", "needs", "relationships", "customization"],
            "examples": ["The Sims", "Animal Crossing", "Stardew Valley"]
        },
        "farming_sim": {
            "name": "Farming Simulation",
            "category": "simulation",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["plant", "harvest", "manage", "expand"],
            "common_features": ["crops", "animals", "tools", "seasons"],
            "examples": ["Stardew Valley", "Harvest Moon", "Farm Together"]
        },
        "racing": {
            "name": "Racing",
            "category": "simulation",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["drive", "race", "compete", "upgrade"],
            "common_features": ["vehicles", "tracks", "lap", "time"],
            "examples": ["Mario Kart", "Forza", "Gran Turismo", "Need for Speed"]
        },
        "sports": {
            "name": "Sports",
            "category": "simulation",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["play", "compete", "control", "strategy"],
            "common_features": ["teams", "rules", "field", "score"],
            "examples": ["FIFA", "NBA 2K", "Rocket League", "Mario Tennis"]
        },
        "flight_sim": {
            "name": "Flight Simulator",
            "category": "simulation",
            "dimensions": ["3D"],
            "core_mechanics": ["fly", "navigate", "land", "manage"],
            "common_features": ["aircraft", "weather", "instruments", "missions"],
            "examples": ["Microsoft Flight Simulator", "X-Plane", "Ace Combat"]
        },
        
        # Arcade Genres
        "arcade": {
            "name": "Arcade",
            "category": "arcade",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["score", "survive", "quick_reflexes"],
            "common_features": ["high_score", "lives", "power-ups", "waves"],
            "examples": ["Pac-Man", "Space Invaders", "Galaga"]
        },
        "pinball": {
            "name": "Pinball",
            "category": "arcade",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["flip", "bounce", "score", "multiplier"],
            "common_features": ["ball", "flippers", "bumpers", "score"],
            "examples": ["Pinball FX", "The Pinball Arcade"]
        },
        
        # Horror Genres
        "horror": {
            "name": "Horror",
            "category": "horror",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["survive", "hide", "explore", "fear"],
            "common_features": ["enemies", "atmosphere", "resources", "scares"],
            "examples": ["Resident Evil", "Silent Hill", "Amnesia", "Outlast"]
        },
        "survival_horror": {
            "name": "Survival Horror",
            "category": "horror",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["survive", "manage_resources", "hide", "solve"],
            "common_features": ["limited_ammo", "enemies", "puzzles", "atmosphere"],
            "examples": ["Resident Evil", "Silent Hill", "The Last of Us"]
        },
        
        # Other Genres
        "idle": {
            "name": "Idle/Incremental",
            "category": "casual",
            "dimensions": ["2D"],
            "core_mechanics": ["wait", "upgrade", "progress", "automate"],
            "common_features": ["currency", "upgrades", "prestige", "time"],
            "examples": ["Cookie Clicker", "Adventure Capitalist", "Idle Miner"]
        },
        "rhythm": {
            "name": "Rhythm",
            "category": "music",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["tap", "timing", "rhythm", "combo"],
            "common_features": ["music", "notes", "score", "combo"],
            "examples": ["Guitar Hero", "Dance Dance Revolution", "Beat Saber"]
        },
        "music": {
            "name": "Music",
            "category": "music",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["play", "create", "rhythm"],
            "common_features": ["instruments", "notes", "tracks", "recording"],
            "examples": ["Guitar Hero", "Rock Band", "Beat Saber"]
        },
        "card_game": {
            "name": "Card Game",
            "category": "strategy",
            "dimensions": ["2D"],
            "core_mechanics": ["draw", "play", "strategy", "deck"],
            "common_features": ["cards", "deck", "hand", "mana"],
            "examples": ["Hearthstone", "Magic: The Gathering", "Slay the Spire"]
        },
        "board_game": {
            "name": "Board Game",
            "category": "strategy",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["turn", "strategy", "luck", "rules"],
            "common_features": ["pieces", "board", "turns", "rules"],
            "examples": ["Chess", "Monopoly", "Catan", "Ticket to Ride"]
        },
        "maze": {
            "name": "Maze",
            "category": "puzzle",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["navigate", "explore", "solve", "find"],
            "common_features": ["walls", "path", "goal", "collectibles"],
            "examples": ["Pac-Man", "Labyrinth", "Maze Runner"]
        },
        "stealth": {
            "name": "Stealth",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["hide", "sneak", "avoid", "assassinate"],
            "common_features": ["visibility", "noise", "enemies", "tools"],
            "examples": ["Metal Gear Solid", "Dishonored", "Hitman", "Thief"]
        },
        "survival": {
            "name": "Survival",
            "category": "action",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["survive", "craft", "gather", "build"],
            "common_features": ["health", "hunger", "thirst", "crafting"],
            "examples": ["Minecraft", "Don't Starve", "The Forest", "Rust"]
        },
        "sandbox": {
            "name": "Sandbox",
            "category": "creative",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["create", "build", "explore", "experiment"],
            "common_features": ["tools", "materials", "world", "creativity"],
            "examples": ["Minecraft", "Terraria", "Garry's Mod", "Dreams"]
        },
        "educational": {
            "name": "Educational",
            "category": "educational",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["learn", "practice", "quiz", "progress"],
            "common_features": ["lessons", "challenges", "feedback", "progress"],
            "examples": ["Math Blaster", "Typing Tutor", "CodeCombat"]
        },
        "party": {
            "name": "Party",
            "category": "casual",
            "dimensions": ["2D", "3D"],
            "core_mechanics": ["compete", "minigames", "social", "fun"],
            "common_features": ["minigames", "multiplayer", "rounds", "score"],
            "examples": ["Mario Party", "Jackbox Games", "Overcooked"]
        },
        "casual": {
            "name": "Casual",
            "category": "casual",
            "dimensions": ["2D"],
            "core_mechanics": ["simple", "quick", "relaxing"],
            "common_features": ["easy", "short", "accessible", "fun"],
            "examples": ["Angry Birds", "Candy Crush", "Flappy Bird"]
        }
    }
    
    @classmethod
    def get_genre(cls, genre_key: str) -> Optional[Dict[str, Any]]:
        """Get genre information by key"""
        return cls.ALL_GENRES.get(genre_key.lower())
    
    @classmethod
    def normalize_genre(cls, genre_input: str) -> str:
        """
        Normalize genre input to a standard genre key
        Handles variations and synonyms
        """
        genre_lower = genre_input.lower().strip()
        
        # Direct match
        if genre_lower in cls.ALL_GENRES:
            return genre_lower
        
        # Synonym mapping
        synonyms = {
            "platform": "platformer",
            "platforming": "platformer",
            "jump and run": "platformer",
            "runner": "endless_runner",
            "endless run": "endless_runner",
            "infinite runner": "endless_runner",
            "first person shooter": "fps",
            "third person shooter": "tps",
            "shmup": "bullet_hell",
            "shoot em up": "bullet_hell",
            "match three": "match_3",
            "match-3": "match_3",
            "match 3": "match_3",
            "real time strategy": "rts",
            "turn based strategy": "tbs",
            "role playing game": "rpg",
            "action role playing": "action_rpg",
            "action rpg": "action_rpg",
            "rogue like": "roguelike",
            "rogue-lite": "roguelite",
            "point and click adventure": "point_and_click",
            "visual novel": "visual_novel",
            "life simulation": "life_sim",
            "farming": "farming_sim",
            "farming simulation": "farming_sim",
            "flight simulator": "flight_sim",
            "survival horror": "survival_horror",
            "card": "card_game",
            "board": "board_game",
            "stealth game": "stealth",
            "survival game": "survival",
            "party game": "party",
            "casual game": "casual"
        }
        
        if genre_lower in synonyms:
            return synonyms[genre_lower]
        
        # Enhanced partial/fuzzy matching
        # Score each genre by how well it matches
        best_match = None
        best_score = 0
        
        for key, info in cls.ALL_GENRES.items():
            score = 0
            
            # Exact key match (highest priority)
            if key in genre_lower or genre_lower in key:
                score += 10
            
            # Genre name match
            genre_name = info["name"].lower()
            if genre_name in genre_lower:
                score += 8
            elif any(word in genre_lower for word in genre_name.split()):
                score += 5
            
            # Check examples (e.g., "subway" matches "Subway Surfers" -> endless_runner)
            examples = [ex.lower() for ex in info.get("examples", [])]
            for example in examples:
                # Check if any word from example is in input
                example_words = example.split()
                for word in example_words:
                    if len(word) > 3 and word in genre_lower:  # Only meaningful words
                        score += 3
                        break
            
            # Check core mechanics keywords
            mechanics = [m.lower() for m in info.get("core_mechanics", [])]
            for mechanic in mechanics:
                if mechanic in genre_lower:
                    score += 2
            
            # Check common features
            features = [f.lower() for f in info.get("common_features", [])]
            for feature in features:
                if feature in genre_lower:
                    score += 1
            
            # Update best match
            if score > best_score:
                best_score = score
                best_match = key
        
        # If we found a good match (score > 0), use it
        if best_match and best_score > 0:
            logger.info(f"🎯 Partial genre match: '{genre_input}' -> '{best_match}' (score: {best_score})")
            return best_match
        
        # Default fallback
        logger.warning(f"⚠️  No genre match found for '{genre_input}', using default 'platformer'")
        return "platformer"
    
    @classmethod
    def get_all_genres(cls) -> List[str]:
        """Get list of all genre keys"""
        return list(cls.ALL_GENRES.keys())
    
    @classmethod
    def get_genres_by_category(cls, category: str) -> List[str]:
        """Get all genres in a category"""
        return [
            key for key, info in cls.ALL_GENRES.items()
            if info.get("category") == category.lower()
        ]
    
    @classmethod
    def get_genre_info(cls, genre_key: str) -> Dict[str, Any]:
        """Get full genre information"""
        genre = cls.get_genre(genre_key)
        if not genre:
            # Return default platformer info
            genre = cls.ALL_GENRES.get("platformer", {})
        return genre.copy()

