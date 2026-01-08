import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";

function JobStatusPanel({
  jobLookupId,
  onJobLookupIdChange,
  generateJobId,
  verifyJobId,
  onFetchJobStatus,
  jobStatus,
  onRetryJob,
  isLoading,
  isPolling,
  errorMessage
}) {
  return (
    <section className="panel">
      <h2>Jobs</h2>
      <div className="grid">
        <Input
          label="Job ID Lookup"
          value={jobLookupId}
          onChange={(event) => onJobLookupIdChange(event.target.value)}
          placeholder="UUID"
        />
        <Input label="Generate Job ID" value={generateJobId} readOnly />
        <Input label="Verify Job ID" value={verifyJobId} readOnly />
      </div>
      <div className="actions">
        <Button onClick={onFetchJobStatus} disabled={isLoading}>
          {isLoading ? "Checking..." : "Check Job Status"}
        </Button>
        {isPolling ? <span className="muted">Polling…</span> : null}
        {jobStatus?.status === "FAILED" ? (
          <Button variant="danger" size="sm" onClick={onRetryJob}>
            Retry Job
          </Button>
        ) : null}
      </div>
      {errorMessage ? <p className="error">{errorMessage}</p> : null}
      {jobStatus ? (
        <Card className="job">
          <strong>{jobStatus.job_type}</strong>
          <span>Status: {jobStatus.status}</span>
          {jobStatus.error ? <p className="error">{jobStatus.error}</p> : null}
        </Card>
      ) : null}
    </section>
  );
}

export default JobStatusPanel;
