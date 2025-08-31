import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./components/Landing";
import Login from "./components/Auth/Login";
import Signup from "./components/Auth/Signup";
import Dashboard from "./components/Dashboard/Dashboard";
import NotFound from "./pages/NotFound";
import { supabase } from "@/supabaseClient";
import AuthGuard from "./components/Auth/AuthGuard"; // <-- Added

const queryClient = new QueryClient();

const App = () => {
  useEffect(() => {
    const initSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session) {
        localStorage.setItem("access_token", session.access_token);
      }

      // Listen for auth changes and keep token updated
      const { data: listener } = supabase.auth.onAuthStateChange(
        async (_event, session) => {
          if (session) {
            localStorage.setItem("access_token", session.access_token);
          } else {
            localStorage.removeItem("access_token");
          }
        }
      );

      return () => {
        listener.subscription.unsubscribe();
      };
    };

    initSession();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/dashboard"
              element={
                <AuthGuard>
                  <Dashboard />
                </AuthGuard>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;

