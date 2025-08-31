import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  Clock,
  FileText,
  LogOut,
  Menu,
  Play,
  Search,
  Settings,
  User,
  X,
} from "lucide-react";
import PDFUpload from "./PDFUpload";
import SummaryCard from "./SummaryCard";
import VideoCard from "./VideoCard";

const Dashboard = () => {
  const [selectedTab, setSelectedTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [summaries, setSummaries] = useState<any[]>([]);
  const [videos, setVideos] = useState<any[]>([]);

  const handleLogout = () => {
    console.log("Logout clicked");
  };

  const handleTabChange = (tab: string) => {
    setSelectedTab(tab);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>

              <div className="p-2 rounded-lg">
                <img
                  src="/pdepthlogo.png"
                  alt="PDepth Logo"
                  className="h-6 w-6 object-contain"
                />
              </div>
              <span className="text-xl font-bold text-foreground">PDepth</span>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" className="hidden sm:flex">
                <Search className="h-4 w-4 mr-2" />
                Search PDFs, summaries...
              </Button>
              <Button variant="ghost" size="sm" className="hidden sm:flex">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" className="hidden sm:flex">
                <User className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8 relative">
          {/* Sidebar Overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar Navigation */}
          <div
            className={`
              w-64 space-y-2 
              lg:relative lg:translate-x-0 
              fixed left-0 top-16 h-[calc(100vh-4rem)] z-50 bg-background
              transform transition-transform duration-200 ease-in-out
              ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
            `}
          >
            <div className="p-4 bg-card rounded-lg border shadow-sm m-4 lg:m-0">
              <nav className="space-y-1">
                <button
                  onClick={() => handleTabChange("dashboard")}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    selectedTab === "dashboard"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  <BookOpen className="mr-3 h-4 w-4" />
                  Dashboard
                </button>
                <button
                  onClick={() => handleTabChange("my-pdfs")}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    selectedTab === "my-pdfs"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  <FileText className="mr-3 h-4 w-4" />
                  My PDFs
                </button>
                <button
                  onClick={() => handleTabChange("summaries")}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    selectedTab === "summaries"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  <Clock className="mr-3 h-4 w-4" />
                  Summaries
                </button>
                <button
                  onClick={() => handleTabChange("videos")}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    selectedTab === "videos"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  <Play className="mr-3 h-4 w-4" />
                  Videos
                </button>
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 lg:ml-0">
            {selectedTab === "dashboard" && (
              <div className="space-y-8">
                {/* Upload Section */}
                <div className="bg-hero-gradient rounded-2xl p-8 text-white">
                  <div className="max-w-2xl">
                    <h1 className="text-3xl font-bold mb-2">Upload Your PDF</h1>
                    <p className="text-white/90 mb-6">
                      Drag and drop your PDF files or click to browse. Get instant AI-powered summaries
                      and related video content—all in one smart app.
                    </p>
                    <PDFUpload
                      onUploadComplete={(summariesFromBackend, recommendedVideos) => {
                        setSummaries(summariesFromBackend);
                        setVideos(recommendedVideos);
                      }}
                    />
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
                  {/* Summary Results */}
                  <Card className="shadow-card">
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <FileText className="mr-2 h-5 w-5" />
                        Summary Result
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {summaries.slice(0, 1).map((summary, idx) => (
                        <SummaryCard key={idx} pdf={summary} />
                      ))}
                    </CardContent>
                  </Card>

                  {/* Related Videos */}
                  <Card className="shadow-card">
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Play className="mr-2 h-5 w-5" />
                        Related Videos
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {videos.slice(0, 3).map((video, idx) => (
                        <VideoCard key={idx} video={video} />
                      ))}
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {selectedTab === "my-pdfs" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">My PDFs</h2>
                  <Badge variant="secondary">{summaries.length} documents</Badge>
                </div>
                <div className="grid gap-6">
                  {summaries.map((summary, idx) => (
                    <SummaryCard key={idx} pdf={summary} expanded />
                  ))}
                </div>
              </div>
            )}

            {selectedTab === "summaries" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">All Summaries</h2>
                  <Badge variant="secondary">
                    {summaries.filter((p) => p.processingStatus === "completed").length} completed
                  </Badge>
                </div>
                <div className="grid gap-6">
                  {summaries
                    .filter((summary) => summary.processingStatus === "completed")
                    .map((summary, idx) => (
                      <SummaryCard key={idx} pdf={summary} expanded />
                    ))}
                </div>
              </div>
            )}

            {selectedTab === "videos" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">Related Videos</h2>
                  <Badge variant="secondary">{videos.length} videos</Badge>
                </div>
                <div className="grid gap-4">
                  {videos.map((video, idx) => (
                    <VideoCard key={idx} video={video} expanded />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
