import { useState } from "react";

import { api } from "../api/client";
import TaskPoller from "./TaskPoller";

export default function VideoPanel() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [language, setLanguage] = useState("en");
  const [taskId, setTaskId] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const task = await api.submitVideo(youtubeUrl, language, 350);
      setTaskId(task.task_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit video task.");
    }
  };

  return (
    <section className="panel">
      <h2>Video Summarizer</h2>
      <form onSubmit={onSubmit} className="form">
        <input
          placeholder="YouTube URL"
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          required
        />
        <input placeholder="Language (en)" value={language} onChange={(e) => setLanguage(e.target.value)} />
        <button type="submit">Start Background Job</button>
      </form>
      {error ? <div className="error">{error}</div> : null}
      {taskId ? <TaskPoller taskId={taskId} onPoll={api.pollVideoTask} title="Video Task Status" /> : null}
    </section>
  );
}
