import { useState } from "react";

import { api, type RAGQueryResponse } from "../api/client";
import TaskPoller from "./TaskPoller";

export default function RagPanel() {
  const [documentId, setDocumentId] = useState("doc-001");
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(4);
  const [file, setFile] = useState<File | null>(null);
  const [ingestTaskId, setIngestTaskId] = useState("");
  const [answer, setAnswer] = useState<RAGQueryResponse | null>(null);
  const [error, setError] = useState("");

  const submitTextIngest = async () => {
    setError("");
    setAnswer(null);
    try {
      const task = await api.submitRagTextIngest(documentId, text);
      setIngestTaskId(task.task_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to enqueue text ingestion.");
    }
  };

  const submitFileIngest = async () => {
    if (!file) return;
    setError("");
    setAnswer(null);
    try {
      const task = await api.submitRagFileIngest(documentId, file);
      setIngestTaskId(task.task_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to enqueue file ingestion.");
    }
  };

  const submitQuery = async () => {
    setError("");
    try {
      const data = await api.queryRag(query, documentId, topK);
      setAnswer(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "RAG query failed.");
    }
  };

  return (
    <section className="panel">
      <h2>RAG Chatbot</h2>
      <div className="form">
        <input value={documentId} onChange={(e) => setDocumentId(e.target.value)} placeholder="Document ID" />
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste source text..." rows={5} />
        <button onClick={submitTextIngest} disabled={!text.trim()}>
          Enqueue Text Ingestion
        </button>
      </div>
      <div className="form">
        <input type="file" accept=".txt,.pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button onClick={submitFileIngest} disabled={!file}>
          Enqueue File Ingestion
        </button>
      </div>
      {ingestTaskId ? <TaskPoller taskId={ingestTaskId} onPoll={api.pollRagTask} title="RAG Ingestion Status" /> : null}
      <div className="form">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask a question..." />
        <input
          type="number"
          min={1}
          max={20}
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          placeholder="Top K"
        />
        <button onClick={submitQuery} disabled={!query.trim()}>
          Query RAG
        </button>
      </div>
      {answer ? (
        <div className="result-card">
          <div className="result-header">
            <strong>Answer</strong>
            <span className="chip">{answer.cache_hit ? "cache hit" : "live"}</span>
          </div>
          <p className="result-text">{answer.answer}</p>

          <div className="result-header">
            <strong>Sources</strong>
            <span className="chip">{answer.sources.length}</span>
          </div>
          <div className="source-list">
            {answer.sources.map((source, index) => (
              <article key={`${index}-${source.score}`} className="source-card">
                <div className="source-meta">
                  <span>#{index + 1}</span>
                  <span>score {source.score.toFixed(3)}</span>
                </div>
                <p>{source.text}</p>
                {source.metadata.filename ? (
                  <div className="source-file">File: {String(source.metadata.filename)}</div>
                ) : null}
              </article>
            ))}
          </div>
        </div>
      ) : null}
      {error ? <div className="error">{error}</div> : null}
    </section>
  );
}
