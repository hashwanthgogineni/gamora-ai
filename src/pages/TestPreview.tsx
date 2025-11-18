import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Gamepad2 } from 'lucide-react';

/**
 * TEMPORARY TEST PAGE - DELETE AFTER TESTING
 * 
 * This page tests if we can render a game from Supabase Storage
 * without running the full generation workflow.
 * 
 * Usage:
 * 1. Go to http://localhost:8080/test-preview
 * 2. Enter a project ID from your Supabase Storage (games/ folder)
 * 3. Click "Load Game" to test
 * 4. Delete this file after testing
 */

export default function TestPreview() {
  const [searchParams] = useSearchParams();
  const [projectId, setProjectId] = useState(searchParams.get('projectId') || '');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Get API base URL from environment
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Auto-load if projectId is in URL
  useEffect(() => {
    const urlProjectId = searchParams.get('projectId');
    if (urlProjectId) {
      setProjectId(urlProjectId);
      const url = `${apiBaseUrl}/api/v1/generate/preview/${urlProjectId}`;
      setPreviewUrl(url);
    }
  }, [searchParams, apiBaseUrl]);

  const handleLoad = (id?: string) => {
    const testId = id || projectId.trim();
    if (!testId) {
      setError('Please enter a project ID');
      return;
    }

    setLoading(true);
    setError(null);
    
    // Use the proxy endpoint
    const url = `${apiBaseUrl}/api/v1/generate/preview/${testId}`;
    setPreviewUrl(url);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-neutral-950 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl text-green-500 font-light mb-4">
            🧪 Test Game Preview (TEMPORARY - DELETE AFTER TESTING)
          </h1>
          
          <div className="flex gap-4 items-center mb-4">
            <input
              type="text"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              placeholder="Enter project ID (e.g., c2d3de5c-3131-47ea-9780-9521eb8bb052)"
              className="px-4 py-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded text-white flex-1"
            />
            <button
              onClick={() => handleLoad()}
              disabled={loading}
              className="px-6 py-2 bg-green-500 text-black rounded hover:bg-green-600 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load Game'}
            </button>
          </div>

          {error && (
            <div className="text-red-500 mb-4">{error}</div>
          )}

          <p className="text-gray-400 text-sm mb-4">
            💡 Tip: Check your Supabase Storage bucket for a project ID in the <code>games/</code> folder
          </p>
        </div>

        <div className="border border-[#6b6b6b]/50 rounded-xl bg-black/60 p-4">
          <h2 className="flex items-center gap-1 text-xl mb-4 text-green-500 font-light">
            <Gamepad2 size={15} className="text-green-500 relative top-[1.5px]" /> Game Preview
          </h2>

          {previewUrl ? (
            <div className="border border-[#6b6b6b]/50 rounded-xl bg-black/60 overflow-hidden">
              <iframe
                key={previewUrl}
                src={previewUrl}
                className="w-full h-[720px] border-none"
                title="Game Preview Test"
                allow="gamepad; fullscreen; autoplay; encrypted-media; microphone; camera"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads"
                style={{ border: 'none' }}
                referrerPolicy="no-referrer"
                onError={(e) => {
                  console.error('Iframe load error:', e);
                  setError('Failed to load game preview');
                }}
                onLoad={() => {
                  console.log('Iframe loaded successfully:', previewUrl);
                  setError(null);
                }}
              />
            </div>
          ) : (
            <div className="border border-[#6b6b6b]/50 rounded-xl w-full h-[720px] bg-black/60 flex items-center justify-center">
              <p className="text-gray-400 text-sm font-light">
                Enter a project ID and click "Load Game" to test
              </p>
            </div>
          )}

          {previewUrl && (
            <div className="mt-4 p-4 bg-[#1a1a1a] rounded text-sm">
              <p className="text-gray-400 mb-2">Preview URL:</p>
              <code className="text-green-400 break-all">{previewUrl}</code>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

