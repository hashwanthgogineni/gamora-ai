import Matter from 'matter-js';
import PhysicsEngine from './PhysicsEngine';
import Renderer from './Renderer';

class GameEngine {
  constructor(canvas, assets, config) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.assets = assets;
    this.config = config;
    
    // Initialize physics
    this.physics = new PhysicsEngine();
    
    // Initialize renderer
    this.renderer = new Renderer(this.ctx, assets);
    
    // Game state
    this.running = false;
    this.lastTime = 0;
    
    // Game entities
    this.player = null;
    this.platforms = [];
    this.enemies = [];
    this.collectibles = [];
    
    // Input handling
    this.keys = {};
    this.setupInput();
    
    // Initialize game world
    this.init();
  }

  init() {
    // Create player
    const playerX = 100;
    const playerY = 300;
    this.player = this.physics.createPlayer(
      playerX,
      playerY,
      this.config.player.width,
      this.config.player.height
    );
    
    // Create platforms
    this.createPlatforms();
    
    // Create enemies
    this.createEnemies();
    
    // Create collectibles
    this.createCollectibles();
  }

  createPlatforms() {
    // Ground platform
    const ground = this.physics.createPlatform(
      this.canvas.width / 2,
      this.canvas.height - 50,
      this.canvas.width,
      100
    );
    this.platforms.push(ground);
    
    // Additional platforms
    const platformPositions = [
      { x: 400, y: 500, width: 200, height: 20 },
      { x: 700, y: 400, width: 200, height: 20 },
      { x: 1000, y: 300, width: 200, height: 20 }
    ];
    
    platformPositions.forEach(pos => {
      const platform = this.physics.createPlatform(
        pos.x,
        pos.y,
        pos.width,
        pos.height
      );
      this.platforms.push(platform);
    });
  }

  createEnemies() {
    // Create some enemies
    for (let i = 0; i < 3; i++) {
      const enemy = this.physics.createEnemy(
        500 + i * 300,
        200,
        64,
        64
      );
      this.enemies.push(enemy);
    }
  }

  createCollectibles() {
    // Create collectibles
    for (let i = 0; i < 5; i++) {
      const collectible = this.physics.createCollectible(
        300 + i * 200,
        250,
        32,
        32
      );
      this.collectibles.push(collectible);
    }
  }

  setupInput() {
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
    });
    
    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });
  }

  update(deltaTime) {
    // Update physics
    this.physics.update(deltaTime);
    
    // Handle player input
    if (this.player) {
      const speed = this.config.player.speed;
      
      // Horizontal movement
      if (this.keys['a'] || this.keys['arrowleft']) {
        Matter.Body.setVelocity(this.player, {
          x: -speed,
          y: this.player.velocity.y
        });
      } else if (this.keys['d'] || this.keys['arrowright']) {
        Matter.Body.setVelocity(this.player, {
          x: speed,
          y: this.player.velocity.y
        });
      } else {
        // Apply friction
        Matter.Body.setVelocity(this.player, {
          x: this.player.velocity.x * 0.9,
          y: this.player.velocity.y
        });
      }
      
      // Jump
      if ((this.keys['w'] || this.keys[' '] || this.keys['arrowup']) && this.isOnGround()) {
        Matter.Body.setVelocity(this.player, {
          x: this.player.velocity.x,
          y: -this.config.player.jumpHeight
        });
      }
    }
    
    // Check collisions
    this.checkCollisions();
  }

  isOnGround() {
    if (!this.player) return false;
    
    // Check if player is touching any platform
    const playerBottom = this.player.position.y + this.config.player.height / 2;
    const tolerance = 5;
    
    for (const platform of this.platforms) {
      const platformTop = platform.position.y - platform.bounds.max.y + platform.bounds.min.y;
      if (Math.abs(playerBottom - platformTop) < tolerance) {
        return true;
      }
    }
    
    return false;
  }

  checkCollisions() {
    // Check player-enemy collisions
    this.enemies.forEach((enemy, index) => {
      if (this.player && Matter.Collision.collides(this.player, enemy)) {
        // Reset player position
        Matter.Body.setPosition(this.player, { x: 100, y: 300 });
      }
    });
    
    // Check player-collectible collisions
    this.collectibles.forEach((collectible, index) => {
      if (this.player && Matter.Collision.collides(this.player, collectible)) {
        // Remove collectible
        Matter.World.remove(this.physics.world, collectible);
        this.collectibles.splice(index, 1);
      }
    });
  }

  render() {
    // Clear canvas
    this.ctx.fillStyle = '#1a1a2e';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Render background if available
    if (this.assets.background) {
      this.renderer.renderBackground(this.assets.background, this.canvas.width, this.canvas.height);
    }
    
    // Render platforms
    this.platforms.forEach(platform => {
      this.renderer.renderPlatform(platform, this.assets.platform);
    });
    
    // Render collectibles
    this.collectibles.forEach(collectible => {
      this.renderer.renderCollectible(collectible, this.assets.collectible);
    });
    
    // Render enemies
    this.enemies.forEach(enemy => {
      this.renderer.renderEnemy(enemy, this.assets.enemy);
    });
    
    // Render player
    if (this.player) {
      this.renderer.renderPlayer(this.player, this.assets.player);
    }
    
    // Render UI
    this.renderer.renderUI(this.collectibles.length);
  }

  gameLoop(currentTime) {
    if (!this.running) return;
    
    const deltaTime = (currentTime - this.lastTime) / 1000;
    this.lastTime = currentTime;
    
    // Cap deltaTime to prevent large jumps
    const cappedDelta = Math.min(deltaTime, 0.1);
    
    this.update(cappedDelta);
    this.render();
    
    requestAnimationFrame((time) => this.gameLoop(time));
  }

  start() {
    this.running = true;
    this.lastTime = performance.now();
    this.gameLoop(this.lastTime);
  }

  stop() {
    this.running = false;
  }
}

export default GameEngine;

