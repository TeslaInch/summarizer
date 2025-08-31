import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { supabase } from "@/supabaseClient";

const AuthGuard = ({ children }: { children: JSX.Element }) => {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    const getSession = async () => {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
      setLoading(false);
    };

    getSession();

    // Listen for auth state changes to update session
    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  if (loading) return <div>Loading...</div>;

  if (!session) return <Navigate to="/login" replace />;

  return children;
};

export default AuthGuard;
