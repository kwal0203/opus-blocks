import { useCallback, useEffect, useState } from "react";

import { fetchJobStatus as apiFetchJobStatus } from "../api/ops";
import { isJobTerminal } from "../api/jobs";

function getErrorMessage(err) {
  return err instanceof Error ? err.message : String(err);
}

export function useJobStatus({ baseUrl, token, onTerminal, onError }) {
  const [jobStatus, setJobStatus] = useState(null);
  const [pollingJobId, setPollingJobId] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const fetchJobStatus = useCallback(
    async (jobId) => {
      const trimmedId = String(jobId ?? "").trim();
      if (!trimmedId) {
        const err = new Error("Job ID is required.");
        setError(err.message);
        if (onError) {
          onError(err);
        }
        return null;
      }
      setIsLoading(true);
      try {
        const payload = await apiFetchJobStatus({
          baseUrl,
          token,
          jobId: trimmedId
        });
        setJobStatus(payload);
        setError("");
        if (payload?.status && isJobTerminal(payload.status)) {
          setPollingJobId("");
          if (onTerminal) {
            onTerminal(payload);
          }
        }
        return payload;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        if (onError) {
          onError(err);
        }
        setPollingJobId("");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [baseUrl, token, onTerminal, onError]
  );

  useEffect(() => {
    if (!pollingJobId) return undefined;
    const interval = setInterval(() => {
      fetchJobStatus(pollingJobId);
    }, 2000);
    return () => clearInterval(interval);
  }, [pollingJobId, fetchJobStatus]);

  const startPolling = useCallback((jobId) => {
    const trimmedId = String(jobId ?? "").trim();
    if (!trimmedId) return;
    setPollingJobId(trimmedId);
  }, []);

  const stopPolling = useCallback(() => {
    setPollingJobId("");
  }, []);

  const clearStatus = useCallback(() => {
    setJobStatus(null);
    setError("");
    setIsLoading(false);
  }, []);

  return {
    jobStatus,
    error,
    fetchJobStatus,
    startPolling,
    stopPolling,
    clearStatus,
    isPolling: Boolean(pollingJobId),
    isLoading
  };
}
