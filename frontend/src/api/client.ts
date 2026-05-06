const getBaseUrl = () => {
  // If explicitly provided via Env Var, use that
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  
  // SSR fallback
  if (typeof window === 'undefined') return "http://localhost:8000/api/v1";

  const { hostname, origin } = window.location;
  
  // If we are on Render/Railway/Custom Domain, use the relative origin
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `${origin}/api/v1`;
  }
  
  // Local development fallback
  return "http://localhost:8000/api/v1";
};

const API_BASE_URL = getBaseUrl();

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
    if (!response.ok) {
      const body = await response.text();
      console.error(`API Error [${response.status}] ${url}:`, body);
      throw new Error(`${response.status} ${response.statusText}: ${body}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    console.error(`Fetch error at ${url}:`, error);
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new Error(`Failed to connect to backend at ${API_BASE_URL}. Ensure the backend is running.`);
    }
    throw error;
  }
}

export type TaskAccepted = { task_id: string; status: "queued"; message: string };
export type TaskStatus = { task_id: string; status: string; result?: Record<string, unknown>; error?: string | null };

export type RAGSource = { text: string; score: number; metadata: Record<string, unknown> };
export type RAGQueryResponse = { answer: string; sources: RAGSource[]; cache_hit: boolean };

export type RoadmapStep = {
  step: number;
  title: string;
  outcomes: string[];
  resources: string[];
  estimated_hours: number;
};
export type RoadmapResponse = {
  topic: string;
  learner_level: string;
  total_weeks: number;
  steps: RoadmapStep[];
};

export const api = {
  submitVideo(url: string, targetLanguage: string, maxSummaryTokens: number): Promise<TaskAccepted> {
    return http("/video/summarize", {
      method: "POST",
      body: JSON.stringify({
        youtube_url: url,
        target_language: targetLanguage,
        max_summary_tokens: maxSummaryTokens,
      }),
    });
  },
  pollVideoTask(taskId: string): Promise<TaskStatus> {
    return http(`/video/tasks/${taskId}`);
  },
  submitRagTextIngest(documentId: string, text: string): Promise<TaskAccepted> {
    return http("/rag/ingest/text/async", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, text, metadata: {} }),
    });
  },
  submitRagFileIngest(documentId: string, file: File): Promise<TaskAccepted> {
    const formData = new FormData();
    formData.append("document_id", documentId);
    formData.append("file", file);
    return fetch(`${API_BASE_URL}/rag/ingest/file/async`, { method: "POST", body: formData }).then(async (res) => {
      if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
      }
      return (await res.json()) as TaskAccepted;
    });
  },
  submitRagYoutubeIngest(documentId: string, youtubeUrl: string, targetLanguage: string = "en"): Promise<TaskAccepted> {
    return http("/rag/ingest/youtube", {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
        youtube_url: youtubeUrl,
        target_language: targetLanguage,
        metadata: {}
      }),
    });
  },
  pollRagTask(taskId: string): Promise<TaskStatus> {
    return http(`/rag/tasks/${taskId}`);
  },
  queryRag(query: string, documentId?: string, topK: number = 4): Promise<RAGQueryResponse> {
    return http("/rag/query", { 
      method: "POST", 
      body: JSON.stringify({ query, document_id: documentId, top_k: topK }) 
    });
  },
  generateRoadmap(topic: string, learnerLevel: string, targetDurationWeeks: number): Promise<RoadmapResponse> {
    return http("/roadmap/generate", {
      method: "POST",
      body: JSON.stringify({
        topic,
        learner_level: learnerLevel,
        target_duration_weeks: targetDurationWeeks,
      }),
    });
  },
};
