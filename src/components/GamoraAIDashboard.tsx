import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Send, Download, Paperclip, Gamepad2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { apiClient, ProgressUpdate } from '@/lib/api';
import Header from '@/components/Header';

interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp?: Date;
}

export default function GamoraAIDashboard() {
  const location = useLocation();
  const locationState = location.state as { 
    initialMessage?: string;
    projectId?: string;
    websocketUrl?: string;
  } || {};
  
  const initialMessage = locationState.initialMessage || '';
  const projectId = locationState.projectId;
  const websocketUrl = locationState.websocketUrl;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(projectId || null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [gameHtmlContent, setGameHtmlContent] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const completionMessageAddedRef = useRef<boolean>(false);

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const addBotMessage = useCallback((text: string) => {
    setMessages((prev) => [...prev, { 
      text, 
      sender: 'bot', 
      timestamp: new Date() 
    }]);
  }, []);

  const handleWebSocketUpdate = useCallback((update: ProgressUpdate) => {
    console.log('WebSocket update:', update);
    
    switch (update.type) {
      case 'connected':
        setCurrentStatus('Game Generation In Progress...');
        // Don't add message to chat - keep static message
        break;
        
      case 'progress':
        const { status, message, step, progress } = update.data;
        // Update status for right panel only
        const displayText = message || status || 'Processing...';
        if (displayText) {
          setCurrentStatus(displayText);
        }
        // Don't add to chat - keep static message
        if (step) {
          setIsLoading(true);
        }
        break;
        
      case 'complete':
        setIsLoading(false);
        setCurrentStatus('Completed');
        const { project_id } = update.data;
        const previewUrlFromUpdate = (update.data as any).preview_url || update.data.web_preview_url;
        if (project_id) {
          setCurrentProjectId(project_id);
          // Fetch preview URL if not in update
          if (previewUrlFromUpdate) {
            setPreviewUrl(previewUrlFromUpdate);
            // Load HTML content directly for better rendering
            loadGameHtml(previewUrlFromUpdate);
          } else {
            // Fetch preview URL from API
            fetchPreviewUrl(project_id);
          }
        }
        // Update chat with completion message (only once)
        if (!completionMessageAddedRef.current) {
          addBotMessage('Enjoy the Game and let me know if you need any changes on it?');
          completionMessageAddedRef.current = true;
        }
        break;
        
      case 'error':
        setIsLoading(false);
        setCurrentStatus('Failed');
        addBotMessage(`❌ Error: ${update.data.error || 'Generation failed'}`);
        break;
    }
  }, [addBotMessage]);

  // Initialize with user message and connect to WebSocket
  useEffect(() => {
    if (initialMessage && messages.length === 0) {
      setMessages([
        { text: initialMessage, sender: 'user', timestamp: new Date() },
        { text: 'Cooking the game! please wait a bit...', sender: 'bot', timestamp: new Date() }
      ]);
    }

    // Connect to WebSocket if projectId is available
    if (projectId) {
      setIsLoading(true);
      setCurrentStatus('Connecting...');
      completionMessageAddedRef.current = false; // Reset completion message flag
      
      apiClient.createWebSocketConnection(projectId, handleWebSocketUpdate).then((ws) => {
        wsRef.current = ws;
      }).catch((error) => {
        console.error('Failed to connect WebSocket:', error);
        addBotMessage('❌ Failed to connect to real-time updates');
        setIsLoading(false);
      });

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      };
    }
  }, [projectId, initialMessage, addBotMessage, handleWebSocketUpdate]);

  const handleSend = async () => {
    if (input.trim() === '' || isLoading) return;
    
    const newMsg: Message = { text: input, sender: 'user', timestamp: new Date() };
    setMessages((prev) => [...prev, newMsg]);
    const userPrompt = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      // Reset completion message flag for new generation
      completionMessageAddedRef.current = false;
      
      // Add initial bot message
      setMessages((prev) => [
        ...prev,
        { text: 'Cooking the game! please wait a bit...', sender: 'bot', timestamp: new Date() }
      ]);
      
      // Call backend API to generate new game
      const response = await apiClient.generateGame({
        prompt: userPrompt,
      });

      // Connect to WebSocket for this new project
      if (wsRef.current) {
        wsRef.current.close();
      }

      // Update project ID
      setCurrentProjectId(response.project_id);
      setPreviewUrl(null); // Reset preview URL for new game
      setGameHtmlContent(null); // Reset HTML content

      apiClient.createWebSocketConnection(response.project_id, (update: ProgressUpdate) => {
        handleWebSocketUpdate(update);
      }).then((ws) => {
        wsRef.current = ws;
        setCurrentStatus('Starting generation...');
      }).catch((error) => {
        console.error('Failed to connect WebSocket:', error);
        addBotMessage('❌ Failed to connect to real-time updates');
        setIsLoading(false);
      });
    } catch (error: any) {
      console.error('Failed to generate game:', error);
      addBotMessage(`❌ Error: ${error.message || 'Failed to start generation'}`);
      setIsLoading(false);
    }
  };

  const handleDownloadGame = async () => {
    if (!currentProjectId) {
      console.error('No project ID available');
      addBotMessage('❌ No game available to download. Please generate a game first.');
      return;
    }

    try {
      addBotMessage('Preparing game files for download...');

      // Get auth token for download endpoint
      const { createClient } = await import('@supabase/supabase-js');
      const supabase = createClient(
        import.meta.env.VITE_SUPABASE_URL || '',
        import.meta.env.VITE_SUPABASE_ANON_KEY || ''
      );
      
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
        addBotMessage('❌ Please sign in to download games.');
        return;
      }

      // Call backend download endpoint for HTML5 games (ZIP)
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const downloadUrl = `${API_BASE_URL}/api/v1/generate/download-web/${currentProjectId}`;
      
      // Download with proper error handling and progress
      addBotMessage('Downloading game files...');
      
      const response = await fetch(downloadUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `Download failed: ${response.statusText}`;
        
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          // Use default error message
        }
        
        throw new Error(errorMessage);
      }

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `game_${currentProjectId}.zip`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download as blob and create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      addBotMessage('Game downloaded successfully! Extract the ZIP file and open index.html in your browser.');
    } catch (error) {
      console.error('Download error:', error);
      addBotMessage(`❌ Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDownload = async () => {
    if (!currentProjectId) {
      console.error('No project ID available');
      addBotMessage('❌ No game available to download. Please generate a game first.');
      return;
    }

    try {
      // PROTOTYPE MODE: Always use Windows build
      const platform = 'windows';
      addBotMessage('📥 Starting download... (Windows EXE)');

      // Get auth token for download endpoint
      const { createClient } = await import('@supabase/supabase-js');
      const supabase = createClient(
        import.meta.env.VITE_SUPABASE_URL || '',
        import.meta.env.VITE_SUPABASE_ANON_KEY || ''
      );
      
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
        addBotMessage('❌ Please sign in to download games.');
        return;
      }

      // Call backend download endpoint
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const downloadUrl = `${API_BASE_URL}/api/v1/generate/download/${currentProjectId}?platform=${platform}`;
      
      // Download with proper error handling and progress
      addBotMessage('⏳ Downloading game file...');
      
      const response = await fetch(downloadUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `Download failed: ${response.statusText}`;
        
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          // Use default error message
        }
        
        throw new Error(errorMessage);
      }

      // Check if response has content
      const contentLength = response.headers.get('content-length');
      if (contentLength && parseInt(contentLength) === 0) {
        throw new Error('Downloaded file is empty. The build may not be ready yet.');
      }

      // Get blob with progress tracking
      const blob = await response.blob();
      
      if (!blob || blob.size === 0) {
        throw new Error('Downloaded file is empty. Please try again.');
      }

      // Create download link
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${currentProjectId}_windows.exe`;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
      }, 100);

      const fileSizeMB = (blob.size / 1024 / 1024).toFixed(2);
      addBotMessage(`✅ Download complete! File size: ${fileSizeMB} MB`);
    } catch (error: any) {
      console.error('Download failed:', error);
      const errorMessage = error.message || 'Unknown error occurred';
      addBotMessage(`❌ Download failed: ${errorMessage}. Please try again or contact support.`);
    }
  };

  const fetchPreviewUrl = async (projectId: string) => {
    try {
      const project = await apiClient.getProject(projectId);
      if (project.web_preview_url) {
        setPreviewUrl(project.web_preview_url);
        // Also try to load HTML content directly for better rendering
        await loadGameHtml(project.web_preview_url);
      } else {
        // Fallback: construct preview URL from project ID
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const previewUrl = `${API_BASE_URL}/api/v1/generate/preview/${projectId}`;
        setPreviewUrl(previewUrl);
        await loadGameHtml(previewUrl);
      }
    } catch (error) {
      console.error('Failed to fetch preview URL:', error);
      // Fallback: construct preview URL from project ID
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const previewUrl = `${API_BASE_URL}/api/v1/generate/preview/${projectId}`;
      setPreviewUrl(previewUrl);
      await loadGameHtml(previewUrl);
    }
  };

  const loadGameHtml = async (url: string) => {
    try {
      const response = await fetch(url);
      if (response.ok) {
        const html = await response.text();
        setGameHtmlContent(html);
        console.log('✅ Loaded game HTML content');
      } else {
        console.error('Failed to load game HTML:', response.status);
      }
    } catch (error) {
      console.error('Error loading game HTML:', error);
    }
  };

  const copyProjectId = async () => {
    if (currentProjectId) {
      try {
        await navigator.clipboard.writeText(currentProjectId);
        // You could show a toast here
        console.log('Project ID copied to clipboard');
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-black text-white font-sans">
      {/* Header */}
      <Header />
      
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden bg-black">
      {/* Left Chat Panel */}
      <div className="w-[35%] flex flex-col border-r border-border/50 p-6 bg-black">
        <div
          className={`flex-1 mb-4 custom-scrollbar ${
            messages.length > 0 ? 'overflow-y-auto space-y-4' : 'overflow-hidden'
          }`}
        >
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col justify-center items-center h-full text-white text-center">
              <p className="text-lg mb-2 font-light">Start building your next game</p>
              <p className="text-sm font-light">Describe your idea and Gamora will generate code for you.</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className={`p-4 rounded-2xl max-w-[85%] leading-relaxed shadow-sm border border-border/50 bg-black text-white text-sm font-light tracking-wide ${
                msg.sender === 'user' ? 'ml-auto' : ''
              }`}
            >
              {msg.text}
            </motion.div>
          ))}
          <div ref={chatEndRef} />
        </div>

        <div className="flex items-center gap-3 mt-4 bg-black border border-border/50 rounded-3xl shadow-lg p-4 backdrop-blur-sm">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
          />
          <Paperclip
            size={18}
            className={`transition ${
              isLoading 
                ? 'text-gray-500 cursor-not-allowed opacity-50' 
                : 'text-[#25D366] cursor-pointer hover:text-[#128C7E]'
            }`}
            onClick={isLoading ? undefined : handleAttachClick}
          />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            disabled={isLoading}
            className="flex-1 bg-black text-white placeholder-gray-400 text-[16px] focus:outline-none font-light border-none outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="Describe your idea..."
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className={`p-3 rounded-sm shadow-md transition-all border-none outline-none ${
              isLoading
                ? 'bg-gray-600 cursor-not-allowed opacity-50'
                : 'bg-[#25D366] active:scale-95 cursor-pointer hover:scale-105 hover:shadow-lg'
            }`}
          >
            <Send size={18} className="text-black" />
          </button>
        </div>
      </div>

      {/* Right Preview Panel */}
      <div className="w-[65%] flex flex-col items-center justify-center bg-black relative">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full w-full">
            <div className="flex flex-col items-center mb-4">
              <p className="text-white text-xl font-light">{currentStatus || 'Cooking your Game...'}</p>
              <p className="text-gray-400 text-sm font-light mt-1">(Might take 3-4 minutes)</p>
            </div>
            <div className="border border-[#25D366] rounded-sm p-[3px] w-[260px]">
              <div className="flex gap-[3px] bg-black p-[2px]">
                {Array.from({ length: 15 }).map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0.2 }}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.1 }}
                    className="w-[14px] h-[14px] bg-[#25D366]"
                  />
                ))}
              </div>
            </div>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center w-full h-full py-6"
          >
            {currentProjectId && previewUrl ? (
              <>
                <div className="flex items-center justify-end w-full px-6 pt-6 pb-6">
                  <button
                    onClick={handleDownloadGame}
                    className="
                      bg-black text-green-500 border border-green-500 
                      px-6 py-3 rounded-sm font-light
                      transition-colors duration-300
                      hover:bg-green-500 hover:text-black
                      flex items-center gap-2
                    "
                  >
                    <Download size={18} />
                    Download Game
                  </button>
                </div>
                <div className="flex-1 w-full px-6 pt-6 pb-6 relative flex items-center justify-center">
                  {gameHtmlContent ? (
                    // Render HTML directly in a sandboxed iframe using srcdoc
                    <iframe
                      key={previewUrl}
                      srcDoc={gameHtmlContent}
                      className="w-full h-full max-w-full max-h-full border-0 rounded-lg bg-black"
                      title="Game Preview"
                      allow="gamepad; fullscreen; autoplay; microphone; camera"
                      sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads allow-presentation"
                      style={{ 
                        border: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%',
                        minHeight: '500px'
                      }}
                      onLoad={() => {
                        console.log('✅ Game rendered successfully');
                      }}
                      onError={(e) => {
                        console.error('❌ Game render error:', e);
                      }}
                    />
                  ) : (
                    // Fallback to URL-based iframe if HTML content not loaded
                    <iframe
                      key={previewUrl}
                      src={previewUrl}
                      className="w-full h-full max-w-full max-h-full border-0 rounded-lg bg-black"
                      title="Game Preview"
                      allow="gamepad; fullscreen; autoplay; microphone; camera"
                      sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads allow-presentation"
                      style={{ 
                        border: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%',
                        minHeight: '500px'
                      }}
                      onLoad={() => {
                        console.log('✅ Iframe loaded successfully:', previewUrl);
                      }}
                      onError={(e) => {
                        console.error('❌ Iframe load error:', e);
                      }}
                    />
                  )}
                </div>
              </>
            ) : currentProjectId ? (
              <div className="flex flex-col items-center justify-center h-full">
                <Gamepad2 size={64} className="text-gray-600 mb-4" />
                <h2 className="text-xl mb-2 text-gray-400 font-light">
                  Game is Generating...
                </h2>
                <p className="text-gray-500 text-sm font-light">
                  Preview will appear here when ready
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full">
                <Gamepad2 size={64} className="text-gray-600 mb-4" />
                <h2 className="text-xl mb-2 text-gray-400 font-light">
                  No Game Generated Yet
                </h2>
                <p className="text-gray-500 text-sm font-light">
                  Generate a game to preview it here
                </p>
              </div>
            )}
          </motion.div>
        )}
      </div>
      </div>

      <style>{`
        .custom-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: rgba(107, 107, 107, 0.2) transparent;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 3px;
          height: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: rgba(107, 107, 107, 0.2);
          border-radius: 3px;
          transition: background-color 0.2s ease;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: rgba(107, 107, 107, 0.35);
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
      `}</style>
    </div>
  );
}

