import Card from "../../components/ui/Card";

function RunHistory({ paragraphRuns, isLoading, errorMessage }) {
  return (
    <div>
      <span className="inspector__label">Run History</span>
      {errorMessage ? <p className="error">{errorMessage}</p> : null}
      {isLoading ? (
        <p className="muted">Loading run history…</p>
      ) : paragraphRuns.length ? (
        <div className="run-list">
          {paragraphRuns.map((run) => (
            <Card key={run.id} className="run-card">
              <strong>{run.run_type}</strong>
              <span className="muted">{run.model}</span>
              <span className="muted">{new Date(run.created_at).toLocaleString()}</span>
              {run.trace_id ? <span className="muted">Trace: {run.trace_id}</span> : null}
            </Card>
          ))}
        </div>
      ) : (
        <p className="muted">No runs recorded yet.</p>
      )}
    </div>
  );
}

export default RunHistory;
