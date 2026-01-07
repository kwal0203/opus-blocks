const TERMINAL_STATUSES = new Set(["SUCCEEDED", "FAILED", "CANCELLED"]);

export function isJobTerminal(status) {
  return TERMINAL_STATUSES.has(status);
}

export function shouldPollJob(status) {
  return !isJobTerminal(status);
}
