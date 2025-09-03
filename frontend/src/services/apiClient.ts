import { supabase } from "@/supabaseClient";

class SecureApiClient {
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || "http://localhost:8000";
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      throw new Error("No authentication token available");
    }

    return {
      "Authorization": `Bearer ${session.access_token}`,
      "Content-Type": "application/json"
    };
  }

  private async handleResponse(response: Response) {
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid - redirect to login
        await supabase.auth.signOut();
        window.location.href = '/login';
        throw new Error("Authentication failed");
      }
      
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }

  async uploadPDF(file: File): Promise<any> {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
      throw new Error("No authentication token available");
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseURL}/upload-pdf`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${session.access_token}`,
        // Don't set Content-Type for FormData - let browser handle it
      },
      body: formData,
    });

    return this.handleResponse(response);
  }

  async getSummaries(pdfName?: string): Promise<any> {
    const headers = await this.getAuthHeaders();
    const url = pdfName 
      ? `${this.baseURL}/summaries?pdf=${encodeURIComponent(pdfName)}`
      : `${this.baseURL}/summaries`;

    const response = await fetch(url, {
      method: "GET",
      headers: headers,
    });

    return this.handleResponse(response);
  }

  async summarizeText(text: string, maxWords?: number): Promise<any> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/summarize`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        text: text,
        max_words: maxWords || 400
      }),
    });

    return this.handleResponse(response);
  }

  async getHealth(): Promise<any> {
    // Health endpoint doesn't require auth
    const response = await fetch(`${this.baseURL}/health`);
    return this.handleResponse(response);
  }
}

export const apiClient = new SecureApiClient();