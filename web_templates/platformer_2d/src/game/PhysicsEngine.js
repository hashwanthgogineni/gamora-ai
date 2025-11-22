import Matter from 'matter-js';

class PhysicsEngine {
  constructor() {
    // Create Matter.js engine
    this.engine = Matter.Engine.create();
    this.world = this.engine.world;
    
    // Set gravity
    this.engine.world.gravity.y = 0.8;
    
    // Run engine
    Matter.Runner.run(this.engine);
  }

  createPlayer(x, y, width, height) {
    const body = Matter.Bodies.rectangle(x, y, width, height, {
      frictionAir: 0.1,
      restitution: 0,
      density: 0.001
    });
    
    Matter.World.add(this.world, body);
    return body;
  }

  createPlatform(x, y, width, height) {
    const body = Matter.Bodies.rectangle(x, y, width, height, {
      isStatic: true,
      friction: 0.3
    });
    
    Matter.World.add(this.world, body);
    return body;
  }

  createEnemy(x, y, width, height) {
    const body = Matter.Bodies.rectangle(x, y, width, height, {
      isStatic: false,
      frictionAir: 0.1
    });
    
    // Simple AI: move back and forth
    body.enemyAI = {
      direction: 1,
      speed: 1,
      startX: x
    };
    
    Matter.World.add(this.world, body);
    return body;
  }

  createCollectible(x, y, width, height) {
    const body = Matter.Bodies.circle(x, y, width / 2, {
      isStatic: false,
      isSensor: true, // Allow player to pass through
      frictionAir: 0
    });
    
    Matter.World.add(this.world, body);
    return body;
  }

  update(deltaTime) {
    // Update enemy AI
    Matter.Composite.allBodies(this.world).forEach(body => {
      if (body.enemyAI) {
        // Move enemy back and forth
        const distance = body.position.x - body.enemyAI.startX;
        if (Math.abs(distance) > 100) {
          body.enemyAI.direction *= -1;
        }
        
        Matter.Body.setVelocity(body, {
          x: body.enemyAI.direction * body.enemyAI.speed,
          y: body.velocity.y
        });
      }
    });
    
    // Engine update is handled by Matter.Runner
  }
}

export default PhysicsEngine;

