import { useState, useRef, useEffect } from 'react';
import { Send, Plus } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/lib/supabase';
import { apiClient } from '@/lib/api';
import Header from '@/components/Header';

export default function GamoraAIMain() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const handleSend = async () => {
    if (input.trim() && !isLoading) {
      setIsLoading(true);
      
      try {
        // Check if user is authenticated
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          toast({
            title: "Authentication Required",
            description: "Please sign in to generate games",
            variant: "destructive",
          });
          navigate('/signin');
          setIsLoading(false);
          return;
        }

        // Call backend API to generate game
        const response = await apiClient.generateGame({
          prompt: input.trim(),
        });

        // Navigate to dashboard with project ID
        navigate('/chat-dashboard', { 
          state: { 
            initialMessage: input.trim(),
            projectId: response.project_id,
            websocketUrl: response.websocket_url,
          } 
        });
      } catch (error: any) {
        console.error('Failed to generate game:', error);
        toast({
          title: "Generation Failed",
          description: error.message || "Failed to start game generation. Please try again.",
          variant: "destructive",
        });
        setIsLoading(false);
      }
    }
  };

  // Check if user just signed in via Google OAuth and show toast
  useEffect(() => {
    const checkGoogleSignIn = async () => {
      // Check if URL has OAuth callback parameters
      const urlParams = new URLSearchParams(window.location.search);
      const hasOAuthParams = urlParams.has('code') || urlParams.has('access_token');
      
      // Also check session storage for Google sign-in flag
      const googleSignIn = sessionStorage.getItem('google_sign_in');
      
      if (hasOAuthParams || googleSignIn) {
        // Wait a bit for auth state to update
        setTimeout(async () => {
          const { data: { session } } = await supabase.auth.getSession();
          if (session) {
            toast({
              title: "Welcome!",
              description: "Successfully signed in with Google",
            });
            // Clear the flag
            sessionStorage.removeItem('google_sign_in');
            // Clean up URL params
            if (hasOAuthParams) {
              window.history.replaceState({}, '', location.pathname);
            }
          }
        }, 500);
      }
    };
    
    checkGoogleSignIn();
  }, [toast, location.pathname]);

  // Green netted grid background effect
  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      body {
        background-color: #000;
        background-image:
          linear-gradient(to right, rgba(37, 211, 102, 0.15) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(37, 211, 102, 0.15) 1px, transparent 1px);
        background-size: 40px 40px;
        background-repeat: repeat;
      }
    `;
    document.head.appendChild(style);
    return () => {
      if (document.head.contains(style)) {
        document.head.removeChild(style);
      }
    };
  }, []);

  return (
    <div className="flex flex-col min-h-screen w-full text-white font-sans overflow-visible relative">
      {/* Header */}
      <Header />
      
      {/* Main Content */}
      <div className="flex flex-col items-center justify-center flex-1">
        {/* Header Section */}
        <div className="text-center mb-12 z-10">
        <h1 className="text-5xl font-bold mb-2 font-light">
          Build something <span className="text-[#25D366]">Epic</span>
        </h1>
        <p className="text-gray-300 text-lg font-light">Create immersive games by chatting with AI</p>
      </div>

      {/* Chat Input Section */}
      <div className="flex flex-col items-center w-full max-w-4xl px-6 z-10">
        <div className="relative w-full">
          {/* Large Input Box */}
          <div className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl shadow-xl p-6 min-h-[200px] flex flex-col backdrop-blur-sm">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
            />
            
            {/* Top: Placeholder/Input Area */}
            <div className="flex-1 flex items-start">
              <textarea
                placeholder="Ask Gamora to build the game you want!"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                disabled={isLoading}
                className="flex-1 bg-transparent text-white placeholder-gray-400 text-lg focus:outline-none font-light border-none outline-none resize-none min-h-[120px] disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ lineHeight: '1.6' }}
              />
            </div>
            
            {/* Bottom: Actions */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#2a2a2a]">
              {/* Left: Add button */}
              <button
                onClick={handleAttachClick}
                disabled={isLoading}
                className="flex items-center gap-2 text-gray-400 hover:text-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-light text-sm border-none outline-none"
              >
                <Plus size={16} />
                <span>Add files, images etc</span>
              </button>
              
              {/* Right: Send button */}
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="w-10 h-10 flex items-center justify-center bg-[#25D366] rounded-sm transition-all duration-200 cursor-pointer border-none outline-none hover:bg-[#20BA5A] active:scale-[0.96] disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-[#25D366]"
              >
                <Send size={18} className="text-black" />
              </button>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}

