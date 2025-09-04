import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen, User, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/supabaseClient";

const Login = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast({
        title: "Error",
        description: "Please fill in all fields.",
        variant: "destructive",
      });
      return;
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: formData.email,
      password: formData.password,
    });

    if (error) {
      toast({
        title: "Login Failed",
        description: error.message,
        variant: "destructive",
      });
      return;
    }

    // Save token for API calls
    const session = data.session;
    localStorage.setItem("access_token", session.access_token);

    toast({
      title: "Welcome back!",
      description: "Successfully logged in to your account.",
    });

    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="p-2 bg-study-gradient rounded-lg">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
            </div>
            <p className="text-muted-foreground">Learn smarter, not harder</p>
          </div>

          {/* Welcome Back Header */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-foreground">Welcome Back to PDepth</h1>
            <p className="text-muted-foreground">
              Start summarizing PDFs and watching related videos instantly
            </p>
          </div>

          {/* Login Form */}
          <Card className="shadow-card">
            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    Email Address
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="pl-10 h-12"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      className="pl-10 pr-10 h-12"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 bg-study-gradient hover:shadow-glow text-lg font-medium"
                >
                  Log In
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Sign Up Link */}
          <div className="text-center">
            <p className="text-muted-foreground">
              I do not have an account?{" "}
              <button
                onClick={() => navigate("/signup")}
                className="text-primary hover:text-primary/80 font-medium underline-offset-4 hover:underline"
              >
                Sign Up
              </button>
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Hero Section */}
      <div className="hidden lg:block flex-1 bg-hero-gradient relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/10 to-transparent"></div>
        
        {/* Floating Icons */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className="relative">
            {/* Main Icons */}
            <div className="flex space-x-8 mb-8">
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in">
                <BookOpen className="h-12 w-12 text-white" />
              </div>
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in" style={{animationDelay: '0.2s'}}>
                <User className="h-12 w-12 text-white" />
              </div>
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in" style={{animationDelay: '0.4s'}}>
                <BookOpen className="h-12 w-12 text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="absolute bottom-16 left-8 right-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">Transform Your Learning</h2>
          <p className="text-xl text-white/90 mb-8 max-w-md mx-auto">
            Upload any PDF, get instant AI-powered summaries, and discover related educational videos to deepen your understanding.
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 text-center">
        
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;