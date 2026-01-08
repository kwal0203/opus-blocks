function ParagraphInspector({ paragraph, paragraphJobStatus }) {
  return (
    <div>
      <span className="inspector__label">Paragraph</span>
      <p className="inspector__value">{paragraph.id}</p>
      <p className="muted">
        {paragraph.section} · {paragraph.intent}
      </p>
      <p className="muted">Status: {paragraph.status}</p>
      {paragraph.latest_run_id ? (
        <p className="muted">Latest run: {paragraph.latest_run_id}</p>
      ) : null}
      <div>
        <span className="inspector__label">Allowed Facts</span>
        <p className="inspector__value">{paragraph.allowed_fact_ids.length}</p>
      </div>
      <div>
        <span className="inspector__label">Latest Job Status</span>
        {paragraphJobStatus ? (
          <p className="inspector__value">
            {paragraphJobStatus.job_type} · {paragraphJobStatus.status}
          </p>
        ) : (
          <p className="muted">Run a job to see status here.</p>
        )}
      </div>
    </div>
  );
}

export default ParagraphInspector;
