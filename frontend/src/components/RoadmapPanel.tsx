import { useState } from "react";

import { api, type RoadmapResponse } from "../api/client";

export default function RoadmapPanel() {
  const [topic, setTopic] = useState("Machine Learning");
  const [level, setLevel] = useState("beginner");
  const [weeks, setWeeks] = useState(12);
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [error, setError] = useState("");

  const onGenerate = async () => {
    setError("");
    try {
      const data = await api.generateRoadmap(topic, level, weeks);
      setRoadmap(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Roadmap generation failed.");
    }
  };

  return (
    <section className="panel">
      <h2>Roadmap Builder</h2>
      <div className="form">
        <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Topic" />
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="beginner">beginner</option>
          <option value="intermediate">intermediate</option>
          <option value="advanced">advanced</option>
        </select>
        <input
          type="number"
          min={1}
          max={52}
          value={weeks}
          onChange={(e) => setWeeks(Number(e.target.value))}
          placeholder="Weeks"
        />
        <button onClick={onGenerate}>Generate Roadmap</button>
      </div>
      {roadmap ? (
        <div className="result-card">
          <div className="result-header">
            <strong>{roadmap.topic}</strong>
            <span className="chip">
              {roadmap.learner_level} · {roadmap.total_weeks} weeks
            </span>
          </div>
          <div className="source-list">
            {roadmap.steps.map((step) => (
              <article className="source-card" key={step.step}>
                <div className="source-meta">
                  <span>Step {step.step}</span>
                  <span>{step.estimated_hours}h</span>
                </div>
                <p>
                  <strong>{step.title}</strong>
                </p>
                <p>Outcomes: {step.outcomes.join(", ")}</p>
                <p>Resources: {step.resources.join(", ")}</p>
              </article>
            ))}
          </div>
        </div>
      ) : null}
      {error ? <div className="error">{error}</div> : null}
    </section>
  );
}
