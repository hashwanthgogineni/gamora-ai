import { useState } from "react";
import Header from "@/components/Header";
import ChatInterface from "@/components/ChatInterface";
import CodePreview from "@/components/CodePreview";
import { SignInModal } from "@/components/SignInModal";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";

interface User {
  name: string;
  profession: string;
  email: string;
}

const Index = () => {
  // Keep the state if later you want to enable preview again
  const [showPreview] = useState(false);
  const [user, setUser] = useState<User | undefined>();
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);

  const handleSignIn = (userData: User) => {
    setUser(userData);
  };

  const handleSignOut = () => {
    setUser(undefined);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header
        user={user}
        onSignOut={handleSignOut}
        onSignInClick={() => setIsSignInModalOpen(true)}
      />

      <main className="flex-1 overflow-hidden">
        {showPreview ? (
          <ResizablePanelGroup direction="horizontal" className="h-full">
            <ResizablePanel defaultSize={50} minSize={30}>
              <ChatInterface />
            </ResizablePanel>
            <ResizableHandle className="w-1 bg-border hover:bg-primary/20 transition-colors" />
            <ResizablePanel defaultSize={50} minSize={30}>
              <CodePreview />
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          <div className="h-full max-w-4xl mx-auto">
            <ChatInterface />
          </div>
        )}
      </main>

      {/* Removed the toggle preview button */}

      <SignInModal
        isOpen={isSignInModalOpen}
        onClose={() => setIsSignInModalOpen(false)}
        onSignIn={handleSignIn}
      />
    </div>
  );
};

export default Index;
