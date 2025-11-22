// Game configuration - will be customized by AI
const gameConfig = {
  title: '{{GAME_TITLE}}',
  player: {
    speed: {{PLAYER_SPEED}},
    jumpHeight: {{JUMP_HEIGHT}},
    width: 64,
    height: 64
  },
  gravity: 0.8,
  world: {
    width: 1920,
    height: 1080
  }
};

export default gameConfig;

