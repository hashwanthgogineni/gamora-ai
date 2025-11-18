// src/components/SignInModal.tsx
import { useState } from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Mail, Lock } from "lucide-react";
import { supabase } from "@/lib/supabase";

interface SignInModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSignInSuccess: () => void; // notify parent of successful sign-in/up
}

export function SignInModal({
  isOpen,
  onClose,
  onSignInSuccess,
}: SignInModalProps) {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle sign in or sign up
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email.trim() || !formData.password.trim()) return;

    if (isSignUp && formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (isSignUp) {
        // create user + auto login (because email confirm disabled)
        const { error } = await supabase.auth.signUp({
          email: formData.email,
          password: formData.password,
        });
        if (error) throw error;

        // Immediately signed in because confirmation disabled
        onSignInSuccess();
        onClose();
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: formData.email,
          password: formData.password,
        });
        if (error) throw error;

        onSignInSuccess();
        onClose();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Google OAuth with redirect to /chat-main
  const handleGoogleSignIn = async () => {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/chat-main`, // 👈 forces redirect to chat-main page after login
      },
    });
    setLoading(false);
    if (error) {
      setError(error.message);
    }
    // Supabase will handle redirect automatically
  };

  const handleInputChange =
    (field: keyof typeof formData) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={onClose}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 bg-black/90 z-40" />
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <Card className="sm:max-w-[400px] w-full mx-auto p-6 border border-card-border bg-background text-foreground font-sans font-light">
            <h2 className="text-2xl font-light text-center mb-6">
              {isSignUp ? "Create an Account" : "Sign In"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div className="space-y-2">
                <Label
                  htmlFor="email"
                  className="flex items-center gap-2 text-sm font-light"
                >
                  <Mail className="h-4 w-4 text-primary" />
                  Email
                </Label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange("email")}
                  placeholder="your.email@example.com"
                  className="
                    w-full h-10 px-3 py-2 text-sm 
                    border border-card-border 
                    bg-card text-foreground
                    rounded-md
                    focus:outline-none 
                    focus:border-card-border 
                    focus:ring-0
                    font-sans font-light
                  "
                  required
                />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <Label
                  htmlFor="password"
                  className="flex items-center gap-2 text-sm font-light"
                >
                  <Lock className="h-4 w-4 text-primary" />
                  Password
                </Label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange("password")}
                  placeholder="Enter your password"
                  className="
                    w-full h-10 px-3 py-2 text-sm 
                    border border-card-border 
                    bg-card text-foreground
                    rounded-md
                    focus:outline-none 
                    focus:border-card-border 
                    focus:ring-0
                    font-sans font-light
                  "
                  required
                />
              </div>

              {/* Confirm Password only for SignUp */}
              {isSignUp && (
                <div className="space-y-2">
                  <Label
                    htmlFor="confirmPassword"
                    className="flex items-center gap-2 text-sm font-light"
                  >
                    <Lock className="h-4 w-4 text-primary" />
                    Confirm Password
                  </Label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange("confirmPassword")}
                    placeholder="Re-enter your password"
                    className="
                      w-full h-10 px-3 py-2 text-sm 
                      border border-card-border 
                      bg-card text-foreground
                      rounded-md
                      focus:outline-none 
                      focus:border-card-border 
                      focus:ring-0
                      font-sans font-light
                    "
                    required
                  />
                </div>
              )}

              {error && (
                <p className="text-sm text-red-500 text-center">{error}</p>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="
                  w-full 
                  bg-card 
                  text-white 
                  hover:bg-card/80 
                  border border-card-border
                  rounded-md
                  transition-all duration-300 mt-6
                  font-sans font-light
                "
              >
                {loading
                  ? isSignUp
                    ? "Signing up…"
                    : "Signing in…"
                  : isSignUp
                  ? "Sign Up"
                  : "Sign In"}
              </Button>

              <Button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={loading}
                className="
                  w-full 
                  mt-2 
                  bg-white 
                  text-black 
                  hover:bg-gray-100 
                  border border-card-border
                  rounded-md
                  transition-all duration-300
                  font-sans font-light
                "
              >
                Continue with Google
              </Button>

              <p className="text-xs text-center text-muted-foreground mt-4 font-sans font-light">
                {isSignUp ? (
                  <>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setIsSignUp(false)}
                      className="underline text-primary bg-transparent border-none outline-none font-sans font-light"
                      style={{ padding: 0 }}
                    >
                      Sign In
                    </button>
                  </>
                ) : (
                  <>
                    Don’t have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setIsSignUp(true)}
                      className="underline text-primary bg-transparent border-none outline-none font-sans font-light"
                      style={{ padding: 0 }}
                    >
                      Sign Up
                    </button>
                  </>
                )}
              </p>
            </form>
          </Card>
        </div>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
