import { useState, useEffect } from "react";
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

const DASHBOARD_URL = "http://localhost:8000"; // your backend base URL

const Dashboard = () => {
  const [selectedTab, setSelectedTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [summaries, setSummaries] = useState<any[]>([]);
  const [videos, setVideos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleLogout = () => console.log("Logout clicked");

  const handleTabChange = (tab: string) => {
    setSelectedTab(tab);
    setSidebarOpen(false);
  };

  // Poll for updates when PDFs are processing
  const pollForUpdates = async (filenames: string[]) => {
    const pollInterval = setInterval(async () => {
      try {
        let allCompleted = true;
        const updatedSummaries = [];
        const updatedVideos = [];

        for (const filename of filenames) {
          const res = await fetch(`${DASHBOARD_URL}/summaries?pdf=${encodeURIComponent(filename)}`);
          if (!res.ok) continue;

          const data = await res.json();
          
          // Create summary object
          const summaryObj = {
            id: Date.now() + Math.random(), // Generate unique ID
            title: filename.replace('.pdf', ''),
            summary: data.summary || "Processing...",
            uploadDate: data.upload_date || new Date().toISOString(),
            processingStatus: data.status || "processing",
            author: "Unknown", // You can extract this from PDF metadata if needed
          };

          updatedSummaries.push(summaryObj);

          // Add videos if available
          if (data.videos && Array.isArray(data.videos)) {
            const formattedVideos = data.videos.map((video, index) => ({
              id: Date.now() + index + Math.random(),
              title: video.title || "Video Title",
              channel: video.channel || "Unknown Channel",
              duration: video.duration || "0:00",
              thumbnail: video.thumbnail || "",
              url: video.url || "#"
            }));
            updatedVideos.push(...formattedVideos);
          }

          if (data.status !== "completed") {
            allCompleted = false;
          }
        }

        // Update state
        setSummaries(prev => {
          // Remove old entries for these files and add new ones
          const filtered = prev.filter(s => !filenames.some(f => s.title === f.replace('.pdf', '')));
          return [...filtered, ...updatedSummaries];
        });

        setVideos(prev => {
          // For videos, we'll replace all videos (you might want to be more sophisticated)
          return updatedVideos;
        });

        // Stop polling when all are completed
        if (allCompleted) {
          clearInterval(pollInterval);
          setLoading(false);
        }

      } catch (err) {
        console.error("Error polling for updates:", err);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 5 minutes max
    setTimeout(() => {
      clearInterval(pollInterval);
      setLoading(false);
    }, 300000);
  };

  const handleUploadComplete = async (uploadedFileNames: string[]) => {
    console.log("Upload completed for:", uploadedFileNames);
    setLoading(true);
    
    // Start polling for updates
    pollForUpdates(uploadedFileNames);
    
    // Immediately try to get any available data
    try {
      for (const filename of uploadedFileNames) {
        const res = await fetch(`${DASHBOARD_URL}/summaries?pdf=${encodeURIComponent(filename)}`);
        if (res.ok) {
          const data = await res.json();
          
          const summaryObj = {
            id: Date.now() + Math.random(),
            title: filename.replace('.pdf', ''),
            summary: data.summary || "Processing...",
            uploadDate: data.upload_date || new Date().toISOString(),
            processingStatus: data.status || "processing",
            author: "Unknown",
          };

          setSummaries(prev => [...prev, summaryObj]);
        }
      }
    } catch (err) {
      console.error("Error fetching initial data:", err);
    }
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
                <img src="/pdepthlogo.png" alt="PDepth Logo" className="h-6 w-6 object-contain" />
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
          {sidebarOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}
          
          {/* Sidebar Navigation */}
          <div
            className={`w-64 space-y-2 lg:relative lg:translate-x-0 fixed left-0 top-16 h-[calc(100vh-4rem)] z-50 bg-background transform transition-transform duration-200 ease-in-out ${
              sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            }`}
          >
            <div className="p-4 bg-card rounded-lg border shadow-sm m-4 lg:m-0">
              <nav className="space-y-1">
              {["dashboard","my-pdfs","summaries","videos"].map((tab) => {
                const icons: any = { dashboard: BookOpen, "my-pdfs": FileText, summaries: Clock, videos: Play };
                const IconComponent = icons[tab];
                return (
                  <button
                    key={tab}
                    onClick={() => handleTabChange(tab)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      selectedTab === tab
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <IconComponent className="mr-3 h-4 w-4" />
                    {tab.charAt(0).toUpperCase() + tab.slice(1).replace("-", " ")}
                  </button>
                );
              })}

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
                      Drag and drop your PDF files or click to browse. Get instant AI-powered summaries and related video content—all in one smart app.
                    </p>
                    <PDFUpload onUploadComplete={handleUploadComplete} />
                  </div>
                </div>

                {/* Show loading state */}
                {loading && (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Processing your PDF... This may take a moment.</p>
                  </div>
                )}

                {/* Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
                  {summaries.length > 0 && (
                    <Card className="shadow-card">
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <FileText className="mr-2 h-5 w-5" />
                          Recent Summary
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <SummaryCard pdf={summaries[summaries.length - 1]} />
                      </CardContent>
                    </Card>
                  )}

                  {videos.length > 0 && (
                    <Card className="shadow-card">
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Play className="mr-2 h-5 w-5" />
                          Related Videos
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {videos.slice(0, 3).map((video, idx) => (
                          <VideoCard key={video.id || idx} video={video} />
                        ))}
                      </CardContent>
                    </Card>
                  )}
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
                  {summaries.map((summary) => (
                    <SummaryCard key={summary.id} pdf={summary} expanded />
                  ))}
                  {summaries.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No PDFs uploaded yet. Upload your first PDF to get started!</p>
                    </div>
                  )}
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
                    .map((summary) => (
                      <SummaryCard key={summary.id} pdf={summary} expanded />
                    ))}
                  {summaries.filter(s => s.processingStatus === "completed").length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No completed summaries yet. Upload and process PDFs to see summaries here!</p>
                    </div>
                  )}
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
                  {videos.map((video) => (
                    <VideoCard key={video.id} video={video} expanded />
                  ))}
                  {videos.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No video recommendations yet. Upload and process PDFs to get related videos!</p>
                    </div>
                  )}
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