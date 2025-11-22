import React, { useEffect, useRef, useState } from 'react';
import GameCanvas from './components/GameCanvas';
import gameConfig from './config/gameConfig';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <GameCanvas config={gameConfig} />
    </div>
  );
}

export default App;

