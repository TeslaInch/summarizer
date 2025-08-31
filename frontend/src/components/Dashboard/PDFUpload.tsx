import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, File, X, CheckCircle, AlertCircle } from "lucide-react";

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: "uploading" | "processing" | "completed" | "error";
  error?: string;
}

interface PDFUploadProps {
  // summaries: array of summary objects
  // videos: array of video objects
  onUploadComplete?: (summaries: any[], videos: any[]) => void;
}

const BACKEND_URL = "http://localhost:8000/upload-pdf";

const PDFUpload = ({ onUploadComplete }: PDFUploadProps) => {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const showToast = (title: string, description: string, variant: "default" | "destructive" = "default") => {
    console.log(`Toast: ${title} - ${description} (${variant})`);
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;

    const newFiles: UploadFile[] = Array.from(files).map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: "uploading",
    }));

    const invalidFiles = newFiles.filter((f) => !f.file.type.includes("pdf"));
    if (invalidFiles.length > 0) {
      showToast("Invalid file type", "Please upload only PDF files.", "destructive");
      return;
    }

    const oversizedFiles = newFiles.filter((f) => f.file.size > 50 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      showToast("File too large", "Please upload files smaller than 50MB.", "destructive");
      return;
    }

    setUploadFiles((prev) => [...prev, ...newFiles]);
    newFiles.forEach((uploadFile) => handleUpload(uploadFile));
  }, []);

  const handleUpload = async (uploadFile: UploadFile) => {
    try {
      // Step 1: mark as uploading
      setUploadFiles((prev) =>
        prev.map((file) => (file.id === uploadFile.id ? { ...file, progress: 50 } : file))
      );

      const formData = new FormData();
      formData.append("file", uploadFile.file);

      const response = await fetch(BACKEND_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to upload PDF");

      // Step 2: mark as processing
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id ? { ...file, progress: 80, status: "processing" } : file
        )
      );

      const data = await response.json();

      // Ensure we have arrays even if backend returns nothing
      const summaries = Array.isArray(data.summaries) ? data.summaries : [];
      const videos = Array.isArray(data.videos) ? data.videos : [];

      // Step 3: mark as completed
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id
            ? { ...file, progress: 100, status: "completed" }
            : file
        )
      );

      // Notify dashboard to update its state
      onUploadComplete?.(summaries, videos);

      showToast(
        "PDF processed successfully!",
        `${uploadFile.file.name} has been summarized and related videos found.`
      );
    } catch (error) {
      console.error(error);
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id
            ? {
                ...file,
                progress: 100,
                status: "error",
                error: "Failed to process PDF. Please try again.",
              }
            : file
        )
      );
      showToast("Upload failed", uploadFile.file.name, "destructive");
    }
  };

  const removeFile = (fileId: string) => {
    setUploadFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <Card
        className={`border-2 border-dashed transition-all duration-200 ${
          isDragging
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8">
          <div className="text-center">
            <div className="p-4 bg-blue-100 rounded-full w-fit mx-auto mb-4">
              <Upload className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Drop your PDF here or click to browse
            </h3>
            <p className="text-gray-600 mb-6">Supports PDF files up to 50MB</p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white"
                size="lg"
                onClick={() => document.getElementById("file-input")?.click()}
              >
                <File className="mr-2 h-4 w-4" />
                Choose File
              </Button>
              <div className="flex items-center text-gray-500 text-sm">
                <AlertCircle className="mr-1 h-4 w-4" />
                Processing takes 30-60 seconds
              </div>
            </div>

            <input
              id="file-input"
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileInput}
              className="hidden"
            />
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {uploadFiles.length > 0 && (
        <div className="space-y-4">
          {uploadFiles.map((uploadFile) => (
            <Card key={uploadFile.id} className="border shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`p-2 rounded-lg ${
                        uploadFile.status === "completed"
                          ? "bg-green-100"
                          : uploadFile.status === "error"
                          ? "bg-red-100"
                          : "bg-blue-100"
                      }`}
                    >
                      {uploadFile.status === "completed" ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : uploadFile.status === "error" ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : (
                        <File className="h-5 w-5 text-blue-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {uploadFile.file.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {(uploadFile.file.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {uploadFile.status === "uploading" && (
                      <span className="text-sm text-gray-600">
                        {Math.round(uploadFile.progress)}%
                      </span>
                    )}
                    {uploadFile.status === "processing" && (
                      <span className="text-sm text-blue-600 font-medium">
                        Processing...
                      </span>
                    )}
                    {uploadFile.status === "completed" && (
                      <span className="text-sm text-green-600 font-medium">
                        Completed
                      </span>
                    )}
                    {uploadFile.status === "error" && (
                      <span className="text-sm text-red-600 font-medium">
                        Error
                      </span>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(uploadFile.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {uploadFile.status === "uploading" && (
                  <Progress value={uploadFile.progress} className="h-2" />
                )}

                {uploadFile.status === "processing" && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full animate-pulse"
                      style={{ width: "60%" }}
                    ></div>
                  </div>
                )}

                {uploadFile.error && (
                  <p className="text-sm text-red-600 mt-2">
                    {uploadFile.error}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default PDFUpload;
