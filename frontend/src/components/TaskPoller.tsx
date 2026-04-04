import { useEffect, useState } from "react";

import type { TaskStatus } from "../api/client";

type TaskPollerProps = {
  taskId: string;
  onPoll: (taskId: string) => Promise<TaskStatus>;
  title: string;
};

export default function TaskPoller({ taskId, onPoll, title }: TaskPollerProps) {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let active = true;
    const interval = setInterval(async () => {
      try {
        const next = await onPoll(taskId);
        if (!active) return;
        setStatus(next);
        if (next.status === "SUCCESS" || next.status === "FAILURE") {
          clearInterval(interval);
        }
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : "Polling failed");
      }
    }, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [onPoll, taskId]);

  return (
    <div className="task-box">
      <div className="task-title">{title}</div>
      <div>Task ID: {taskId}</div>
      <div>Status: {status?.status ?? "PENDING"}</div>
      {status?.error ? <div className="error">{status.error}</div> : null}
      {status?.result ? (
        <div className="result-card compact">
          {"summary" in status.result && typeof status.result.summary === "string" ? (
            <>
              <div className="result-header">
                <strong>Summary</strong>
              </div>
              <p className="result-text">{status.result.summary}</p>
            </>
          ) : null}
          {"transcript" in status.result && typeof status.result.transcript === "string" ? (
            <>
              <div className="result-header">
                <strong>Transcript</strong>
              </div>
              <p className="result-text">{status.result.transcript.slice(0, 1200)}</p>
            </>
          ) : null}
          {!("summary" in status.result) && !("transcript" in status.result) ? (
            <pre>{JSON.stringify(status.result, null, 2)}</pre>
          ) : null}
        </div>
      ) : null}
      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}
