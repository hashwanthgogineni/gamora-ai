// src/components/ProfileModal.tsx
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/hooks/useAuth";
import { Card } from "@/components/ui/card";
import { User as UserIcon, Briefcase, FileText } from "lucide-react";

interface ProfileModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ProfileModal({ open, onClose }: ProfileModalProps) {
  const { user } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [profession, setProfession] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && user) {
      (async () => {
        const { data } = await supabase
          .from("profiles")
          .select("*")
          .eq("id", user.id)
          .single();
        if (data) {
          setFirstName(data.first_name || "");
          setLastName(data.last_name || "");
          setProfession(data.profession || "");
          setBio(data.bio || "");
        }
      })();
    }
  }, [open, user]);

  const handleSave = async () => {
    if (!user) return;
    setLoading(true);
    const { error } = await supabase.from("profiles").upsert({
      id: user.id,
      first_name: firstName,
      last_name: lastName,
      profession,
      bio,
      updated_at: new Date().toISOString(),
    });
    setLoading(false);
    if (!error) onClose();
    else alert(error.message);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/90 z-40 flex items-center justify-center">
      <Card className="sm:max-w-[450px] w-full mx-auto p-6 border border-card-border bg-background text-foreground font-sans font-light rounded-xl">
        <h2 className="text-2xl font-light text-center mb-6">
          Complete Your Profile
        </h2>

        {/* Name fields */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="space-y-1">
            <label className="flex items-center gap-2 text-sm font-light">
              <UserIcon className="h-4 w-4 text-green-500" />
              First Name
            </label>
            <input
              type="text"
              placeholder="First Name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
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
            />
          </div>

          <div className="space-y-1">
            <label className="flex items-center gap-2 text-sm font-light">
              <UserIcon className="h-4 w-4 text-green-500" />
              Last Name
            </label>
            <input
              type="text"
              placeholder="Last Name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
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
            />
          </div>
        </div>

        {/* Profession */}
        <div className="space-y-1 mb-4">
          <label className="flex items-center gap-2 text-sm font-light">
            <Briefcase className="h-4 w-4 text-green-500" />
            Profession
          </label>
          <input
            type="text"
            placeholder="Your role"
            value={profession}
            onChange={(e) => setProfession(e.target.value)}
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
          />
        </div>

        {/* Bio */}
        <div className="space-y-1 mb-6">
          <label className="flex items-center gap-2 text-sm font-light">
            <FileText className="h-4 w-4 text-green-500" />
            Short Bio
          </label>
          <textarea
            placeholder="Tell us a little about yourself..."
            rows={3}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="
              w-full px-3 py-2 text-sm 
              border border-card-border 
              bg-card text-foreground
              rounded-md resize-none
              focus:outline-none 
              focus:border-card-border 
              focus:ring-0
              font-sans font-light
            "
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="w-full bg-card text-foreground hover:bg-card/80 border border-card-border rounded-md transition-all duration-300 font-sans font-light py-2"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full bg-white text-black hover:bg-gray-100 border border-card-border rounded-md transition-all duration-300 font-sans font-light py-2"
          >
            {loading ? "Saving…" : "Save Profile"}
          </button>
        </div>
      </Card>
    </div>
  );
}
