import React, { useEffect, useRef, useState } from 'react';
import Matter from 'matter-js';
import GameEngine from '../game/GameEngine';
import assetsManifest from '../assets/manifest.json';

function GameCanvas({ config }) {
  const canvasRef = useRef(null);
  const gameEngineRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Load assets
    const loadAssets = async () => {
      try {
        const assets = {};
        
        // Load each asset from manifest
        for (const [key, path] of Object.entries(assetsManifest)) {
          if (path && key !== 'ui') {
            const img = new Image();
            // Handle different path formats:
            // - Absolute paths: use as-is
            // - Relative paths starting with ./: remove ./ and use /assets/
            // - Paths without /: prepend /assets/
            let assetPath = path;
            if (path.startsWith('./')) {
              assetPath = `/assets/${path.substring(2)}`;
            } else if (!path.startsWith('/')) {
              assetPath = `/assets/${path}`;
            }
            img.src = assetPath;
            await new Promise((resolve, reject) => {
              img.onload = resolve;
              img.onerror = () => {
                console.warn(`Failed to load asset: ${key} from ${assetPath}`);
                resolve(); // Continue even if asset fails
              };
            });
            assets[key] = img;
          }
        }

        // Initialize game engine
        const engine = new GameEngine(canvas, assets, config);
        gameEngineRef.current = engine;
        
        // Start game loop
        engine.start();
        setLoading(false);
      } catch (err) {
        console.error('Failed to initialize game:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    loadAssets();

    // Handle window resize
    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (gameEngineRef.current) {
        gameEngineRef.current.stop();
      }
    };
  }, [config]);

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#fff',
        background: '#000'
      }}>
        <div>
          <h2>Error loading game</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#fff',
        background: '#000'
      }}>
        <div>Loading game...</div>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: 'block',
        width: '100%',
        height: '100%',
        background: '#1a1a2e'
      }}
    />
  );
}

export default GameCanvas;

