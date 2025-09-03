import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, File, X, CheckCircle, AlertCircle, Clock } from "lucide-react";

interface UploadFile {
  id: string;
  file: File;
  status: "uploading" | "completed" | "error";
  error?: string;
  result?: any;
}

interface PDFUploadProps {
  onUploadComplete?: (result: any) => void;
}

const BACKEND_URL = "http://localhost:8000/upload-pdf";

const PDFUpload = ({ onUploadComplete }: PDFUploadProps) => {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const showToast = (title: string, description: string, variant: "default" | "destructive" = "default") => {
    console.log(`Toast: ${title} - ${description} (${variant})`);
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || isProcessing) return;

    // Only allow one file at a time
    const file = files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.includes("pdf")) {
      showToast("Invalid file type", "Please upload only PDF files.", "destructive");
      return;
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      showToast("File too large", "Please upload files smaller than 50MB.", "destructive");
      return;
    }

    const newFile: UploadFile = {
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: "uploading",
    };

    setUploadFiles([newFile]);
    handleUpload(newFile);
  }, [isProcessing]);

  const handleUpload = async (uploadFile: UploadFile) => {
    try {
      setIsProcessing(true);

      const formData = new FormData();
      formData.append("file", uploadFile.file);

      console.log("Starting PDF upload and processing...");

      const response = await fetch(BACKEND_URL, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to process PDF");
      }

      // Mark as completed
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id 
            ? { ...file, status: "completed", result: data } 
            : file
        )
      );

      // Notify parent component with complete results
      onUploadComplete?.(data);

      showToast(
        "PDF processed successfully!",
        `${uploadFile.file.name} has been analyzed and summarized.`
      );

    } catch (error: any) {
      console.error("Upload/processing error:", error);
      
      setUploadFiles((prev) =>
        prev.map((file) =>
          file.id === uploadFile.id
            ? { 
                ...file, 
                status: "error", 
                error: error.message || "Processing failed. Please try again." 
              }
            : file
        )
      );

      showToast("Processing failed", error.message || "Please try again.", "destructive");
    } finally {
      setIsProcessing(false);
    }
  };

  const removeFile = (fileId: string) => {
    if (isProcessing) return; // Don't allow removal while processing
    setUploadFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isProcessing) setIsDragging(true);
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

  const hasActiveUpload = uploadFiles.some(f => f.status === "uploading");

  return (
    <div className="space-y-6">
      <Card
        className={`border-2 border-dashed transition-all duration-200 ${
          isDragging 
            ? "border-blue-400 bg-blue-50" 
            : isProcessing 
            ? "border-gray-200 bg-gray-50" 
            : "border-gray-300 hover:border-gray-400"
        } ${isProcessing ? "pointer-events-none opacity-60" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8 text-center">
          <div className={`p-4 rounded-full w-fit mx-auto mb-4 ${
            isProcessing ? "bg-orange-100" : "bg-blue-100"
          }`}>
            {isProcessing ? (
              <Clock className="h-8 w-8 text-orange-600 animate-pulse" />
            ) : (
              <Upload className="h-8 w-8 text-blue-600" />
            )}
          </div>

          {isProcessing ? (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Processing Your PDF...</h3>
              <p className="text-gray-600 mb-6">
                AI is extracting text, generating summary, and finding related videos. 
                The processing time varies based on size.
              </p>
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Please wait...</span>
              </div>
            </>
          ) : (
            <>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Drop your PDF here or click to browse
              </h3>
              <p className="text-gray-600 mb-6">
                Supports PDF files up to 50MB • One file at a time
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                  onClick={() => document.getElementById("file-input")?.click()}
                  disabled={isProcessing}
                >
                  <File className="mr-2 h-4 w-4" /> Choose PDF File
                </Button>
                <div className="flex items-center text-gray-500 text-sm">
                  <AlertCircle className="mr-1 h-4 w-4" />
                  Complete processing takes 30-60 seconds
                </div>
              </div>
            </>
          )}

          <input
            id="file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
            disabled={isProcessing}
          />
        </CardContent>
      </Card>

      {uploadFiles.length > 0 && (
        <div className="space-y-4">
          {uploadFiles.map((uploadFile) => (
            <Card key={uploadFile.id} className="border shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      uploadFile.status === "completed"
                        ? "bg-green-100"
                        : uploadFile.status === "error"
                        ? "bg-red-100"
                        : "bg-blue-100"
                    }`}>
                      {uploadFile.status === "completed" ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : uploadFile.status === "error" ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Clock className="h-5 w-5 text-blue-600 animate-pulse" />
                        </div>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{uploadFile.file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(uploadFile.file.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {uploadFile.status === "uploading" && (
                      <span className="text-sm text-blue-600 font-medium">Processing...</span>
                    )}
                    {uploadFile.status === "completed" && (
                      <span className="text-sm text-green-600 font-medium">✅ Complete</span>
                    )}
                    {uploadFile.status === "error" && (
                      <span className="text-sm text-red-600 font-medium">❌ Failed</span>
                    )}

                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => removeFile(uploadFile.id)} 
                      className="text-gray-400 hover:text-gray-600"
                      disabled={uploadFile.status === "uploading"}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {uploadFile.status === "uploading" && (
                  <div className="mt-3">
                    <Progress value={50} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1">
                      Extracting text, generating summary, and finding related videos...
                    </p>
                  </div>
                )}

                {uploadFile.error && (
                  <p className="text-sm text-red-600 mt-2 bg-red-50 p-2 rounded">
                    {uploadFile.error}
                  </p>
                )}

                {uploadFile.status === "completed" && uploadFile.result && (
                  <div className="mt-3 p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-700 font-medium mb-1">Processing Complete!</p>
                    <p className="text-xs text-green-600">
                      Summary generated • {uploadFile.result.videos?.length || 0} videos found
                    </p>
                  </div>
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