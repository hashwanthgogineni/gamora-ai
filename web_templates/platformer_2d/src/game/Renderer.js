class Renderer {
  constructor(ctx, assets) {
    this.ctx = ctx;
    this.assets = assets;
  }

  renderBackground(img, width, height) {
    if (img) {
      this.ctx.drawImage(img, 0, 0, width, height);
    } else {
      // Fallback: gradient background
      const gradient = this.ctx.createLinearGradient(0, 0, 0, height);
      gradient.addColorStop(0, '#1a1a2e');
      gradient.addColorStop(1, '#16213e');
      this.ctx.fillStyle = gradient;
      this.ctx.fillRect(0, 0, width, height);
    }
  }

  renderPlayer(body, img) {
    if (img) {
      this.ctx.save();
      this.ctx.translate(body.position.x, body.position.y);
      this.ctx.rotate(body.angle);
      this.ctx.drawImage(img, -body.bounds.max.x + body.bounds.min.x, -body.bounds.max.y + body.bounds.min.y);
      this.ctx.restore();
    } else {
      // Fallback: colored rectangle
      this.ctx.fillStyle = '#4A90E2';
      this.ctx.fillRect(
        body.position.x - (body.bounds.max.x - body.bounds.min.x) / 2,
        body.position.y - (body.bounds.max.y - body.bounds.min.y) / 2,
        body.bounds.max.x - body.bounds.min.x,
        body.bounds.max.y - body.bounds.min.y
      );
    }
  }

  renderPlatform(body, img) {
    if (img) {
      this.ctx.save();
      this.ctx.translate(body.position.x, body.position.y);
      this.ctx.rotate(body.angle);
      this.ctx.drawImage(img, -body.bounds.max.x + body.bounds.min.x, -body.bounds.max.y + body.bounds.min.y);
      this.ctx.restore();
    } else {
      // Fallback: brown rectangle
      this.ctx.fillStyle = '#8B4513';
      this.ctx.fillRect(
        body.position.x - (body.bounds.max.x - body.bounds.min.x) / 2,
        body.position.y - (body.bounds.max.y - body.bounds.min.y) / 2,
        body.bounds.max.x - body.bounds.min.x,
        body.bounds.max.y - body.bounds.min.y
      );
    }
  }

  renderEnemy(body, img) {
    if (img) {
      this.ctx.save();
      this.ctx.translate(body.position.x, body.position.y);
      this.ctx.rotate(body.angle);
      this.ctx.drawImage(img, -body.bounds.max.x + body.bounds.min.x, -body.bounds.max.y + body.bounds.min.y);
      this.ctx.restore();
    } else {
      // Fallback: red rectangle
      this.ctx.fillStyle = '#FF6464';
      this.ctx.fillRect(
        body.position.x - (body.bounds.max.x - body.bounds.min.x) / 2,
        body.position.y - (body.bounds.max.y - body.bounds.min.y) / 2,
        body.bounds.max.x - body.bounds.min.x,
        body.bounds.max.y - body.bounds.min.y
      );
    }
  }

  renderCollectible(body, img) {
    if (img) {
      this.ctx.save();
      this.ctx.translate(body.position.x, body.position.y);
      this.ctx.drawImage(img, -body.bounds.max.x + body.bounds.min.x, -body.bounds.max.y + body.bounds.min.y);
      this.ctx.restore();
    } else {
      // Fallback: yellow circle
      this.ctx.fillStyle = '#FFD700';
      this.ctx.beginPath();
      this.ctx.arc(body.position.x, body.position.y, body.bounds.max.x - body.bounds.min.x, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  renderUI(collectiblesRemaining) {
    // Score/UI overlay
    this.ctx.fillStyle = '#fff';
    this.ctx.font = '20px Arial';
    this.ctx.fillText(`Collectibles: ${collectiblesRemaining}`, 10, 30);
    this.ctx.fillText('WASD or Arrow Keys to move', 10, 60);
  }
}

export default Renderer;

