import { useEffect, useMemo, useState } from "react";

import Badge from "./components/ui/Badge";
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import Input from "./components/ui/Input";
import Toast from "./components/ui/Toast";
import { isJobTerminal } from "./api/jobs";
import {
  createManuscript as apiCreateManuscript,
  createParagraph as apiCreateParagraph,
  extractDocumentFacts as apiExtractDocumentFacts,
  fetchDocumentFacts as apiFetchDocumentFacts,
  fetchJobStatus as apiFetchJobStatus,
  fetchParagraphRuns as apiFetchParagraphRuns,
  fetchParagraphView as apiFetchParagraphView,
  generateParagraph as apiGenerateParagraph,
  linkDocumentToManuscript as apiLinkDocumentToManuscript,
  loginUser as apiLoginUser,
  registerUser as apiRegisterUser,
  uploadDocument as apiUploadDocument,
  verifyParagraph as apiVerifyParagraph,
  updateSentence as apiUpdateSentence
} from "./api/ops";
import { API_BASE_URL } from "./config";

/** @typedef {import("./api/types").Fact} Fact */
/** @typedef {import("./api/types").ParagraphView} ParagraphView */
/** @typedef {import("./api/types").Job} Job */
/** @typedef {import("./api/types").Run} Run */

const defaultSpec = {
  section: "Introduction",
  intent: "Background Context",
  required_structure: {
    topic_sentence: true,
    evidence_sentences: 2,
    conclusion_sentence: true
  },
  allowed_fact_ids: [],
  style: {
    tense: "present",
    voice: "academic",
    target_length_words: [120, 150]
  },
  constraints: {
    forbidden_claims: ["novelty"],
    allowed_scope: "as stated in facts only"
  }
};

const tokenKey = "opusBlocksToken";
const manuscriptIdKey = "opusBlocksManuscriptId";
const manuscriptTitleKey = "opusBlocksManuscriptTitle";
const documentIdKey = "opusBlocksDocumentId";
const paragraphIdKey = "opusBlocksParagraphId";

function setRouteHash(route) {
  window.location.hash = route === "auth" ? "#/auth" : "#/canvas";
}

function getRouteFromHash() {
  const hash = window.location.hash;
  if (hash.includes("auth")) return "auth";
  return "canvas";
}

function requireId(payload, label) {
  if (!payload || !payload.id) {
    throw new Error(`${label} response missing id`);
  }
  return payload.id;
}

function isValidUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    value
  );
}

function App() {
  const [baseUrl, setBaseUrl] = useState(API_BASE_URL);
  const [token, setToken] = useState(localStorage.getItem(tokenKey) || "");
  const [route, setRoute] = useState(getRouteFromHash());
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [documentId, setDocumentId] = useState(
    localStorage.getItem(documentIdKey) || ""
  );
  const [documentFile, setDocumentFile] = useState(/** @type {File | null} */ (null));
  const [extractJobId, setExtractJobId] = useState("");
  const [facts, setFacts] = useState(/** @type {Fact[]} */ ([]));
  const [factSearch, setFactSearch] = useState("");
  const [factSourceFilter, setFactSourceFilter] = useState("ALL");
  const [factUncertainFilter, setFactUncertainFilter] = useState("ALL");
  const [selectedFactIds, setSelectedFactIds] = useState([]);
  const [factPageSize, setFactPageSize] = useState(5);
  const [manuscriptTitle, setManuscriptTitle] = useState(
    localStorage.getItem(manuscriptTitleKey) || "Test Manuscript"
  );
  const [manuscriptId, setManuscriptId] = useState(
    localStorage.getItem(manuscriptIdKey) || ""
  );
  const [paragraphSpec, setParagraphSpec] = useState(defaultSpec);
  const [paragraphId, setParagraphId] = useState(
    localStorage.getItem(paragraphIdKey) || ""
  );
  const [generateJobId, setGenerateJobId] = useState("");
  const [verifyJobId, setVerifyJobId] = useState("");
  const [paragraphView, setParagraphView] = useState(
    /** @type {ParagraphView | null} */ (null)
  );
  const [paragraphRuns, setParagraphRuns] = useState(/** @type {Run[]} */ ([]));
  const [jobLookupId, setJobLookupId] = useState("");
  const [jobStatus, setJobStatus] = useState(/** @type {Job | null} */ (null));
  const [autoPollJobId, setAutoPollJobId] = useState("");
  const [activeSentenceId, setActiveSentenceId] = useState("");
  const [hoveredSentenceId, setHoveredSentenceId] = useState("");
  const [editingSentenceId, setEditingSentenceId] = useState("");
  const [editingSentenceText, setEditingSentenceText] = useState("");

  const tokenPreview = useMemo(() => {
    if (!token) return "Not set";
    return `${token.slice(0, 16)}...${token.slice(-8)}`;
  }, [token]);

  const isAuthenticated = Boolean(token);
  const sections = ["Introduction", "Methods", "Results", "Discussion"];
  const intentOptions = {
    Introduction: ["Background Context", "Prior Work Summary", "Knowledge Gap", "Study Objective"],
    Methods: ["Study Design", "Participants / Data Sources", "Procedures / Protocol", "Analysis Methods"],
    Results: ["Primary Results", "Secondary Results", "Null / Negative Results"],
    Discussion: ["Result Interpretation", "Comparison to Prior Work", "Limitations", "Implications / Future Work"]
  };

  useEffect(() => {
    if (isAuthenticated) {
      setRoute("canvas");
      setRouteHash("canvas");
    } else {
      setRoute("auth");
      setRouteHash("auth");
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handler = () => {
      setRoute(getRouteFromHash());
    };
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  useEffect(() => {
    localStorage.setItem(manuscriptTitleKey, manuscriptTitle);
  }, [manuscriptTitle]);

  useEffect(() => {
    localStorage.setItem(manuscriptIdKey, manuscriptId);
  }, [manuscriptId]);

  useEffect(() => {
    localStorage.setItem(documentIdKey, documentId);
  }, [documentId]);

  useEffect(() => {
    localStorage.setItem(paragraphIdKey, paragraphId);
  }, [paragraphId]);

  const filteredFacts = useMemo(() => {
    return facts.filter((fact) => {
      if (
        factSourceFilter !== "ALL" &&
        fact.source_type.toUpperCase() !== factSourceFilter
      ) {
        return false;
      }
      if (factUncertainFilter === "UNCERTAIN" && !fact.is_uncertain) {
        return false;
      }
      if (factUncertainFilter === "CERTAIN" && fact.is_uncertain) {
        return false;
      }
      if (factSearch) {
        const term = factSearch.toLowerCase();
        if (!fact.content.toLowerCase().includes(term)) {
          return false;
        }
      }
      return true;
    });
  }, [facts, factSearch, factSourceFilter, factUncertainFilter]);

  const pagedFacts = useMemo(() => {
    return filteredFacts.slice(0, factPageSize);
  }, [filteredFacts, factPageSize]);

  const canUpload = Boolean(token);
  const canExtract = Boolean(documentId);
  const canCreateManuscript = Boolean(token);
  const canLinkDocument = Boolean(manuscriptId && documentId);
  const canSelectFacts = facts.length > 0;
  const canCreateParagraph = Boolean(manuscriptId && selectedFactIds.length);
  const canGenerate = Boolean(paragraphId);
  const canVerify = Boolean(paragraphId);
  const canViewParagraph = Boolean(paragraphId);

  function beginEditSentence(sentence) {
    setEditingSentenceId(sentence.id);
    setEditingSentenceText(sentence.text);
  }

  function cancelEditSentence() {
    setEditingSentenceId("");
    setEditingSentenceText("");
  }

  async function saveSentenceEdit(sentenceId) {
    if (!editingSentenceText.trim()) {
      setError("Sentence text cannot be empty.");
      return;
    }
    updateStatus("Saving sentence...");
    try {
      const payload = await apiUpdateSentence({
        baseUrl,
        token,
        sentenceId,
        text: editingSentenceText
      });
      const jobId = requireId(payload, "Update sentence");
      setJobLookupId(jobId);
      setAutoPollJobId(jobId);
      setEditingSentenceId("");
      setEditingSentenceText("");
      setToast({
        variant: "success",
        title: "Sentence updated",
        message: "Reverification started."
      });
      await fetchParagraphView(paragraphId);
    } catch (err) {
      handleError(err);
    }
  }

  function updateStatus(message) {
    setStatus(message);
    setError("");
  }

  function handleError(err) {
    const message = err instanceof Error ? err.message : String(err);
    setError(message);
    setStatus("Error");
    setToast({ variant: "danger", title: "Action failed", message });
  }

  async function register() {
    updateStatus("Registering...");
    try {
      await apiRegisterUser({ baseUrl, email, password });
      updateStatus("Registered.");
      setToast({ variant: "success", title: "Registered", message: "Account created." });
    } catch (err) {
      handleError(err);
    }
  }

  async function login() {
    updateStatus("Logging in...");
    try {
      const payload = await apiLoginUser({ baseUrl, email, password });
      const newToken = payload.access_token;
      setToken(newToken);
      localStorage.setItem(tokenKey, newToken);
      updateStatus("Logged in.");
      setToast({ variant: "success", title: "Welcome back", message: "Login successful." });
    } catch (err) {
      handleError(err);
    }
  }

  async function uploadDocument() {
    if (!documentFile) {
      setError("Pick a PDF first.");
      return;
    }
    updateStatus("Uploading document...");
    try {
      const payload = await apiUploadDocument({ baseUrl, token, file: documentFile });
      setDocumentId(requireId(payload, "Upload"));
      updateStatus("Document uploaded.");
      setToast({ variant: "success", title: "Upload complete", message: "Document stored." });
    } catch (err) {
      handleError(err);
    }
  }

  async function extractFacts() {
    if (!documentId) {
      setError("Document ID is required.");
      return;
    }
    updateStatus("Extracting facts...");
    try {
      setFacts([]);
      setSelectedFactIds([]);
      const payload = await apiExtractDocumentFacts({ baseUrl, token, documentId });
      setExtractJobId(requireId(payload, "Extract facts"));
      updateStatus("Extract job queued.");
      setToast({
        variant: "success",
        title: "Extraction queued",
        message: "Facts extraction has been enqueued."
      });
    } catch (err) {
      handleError(err);
    }
  }

  async function loadFacts() {
    if (!documentId) {
      setError("Document ID is required.");
      return;
    }
    updateStatus("Loading facts...");
    try {
      const payload = await apiFetchDocumentFacts({ baseUrl, token, documentId });
      setFacts(payload);
      updateStatus("Facts loaded.");
      setToast({ variant: "success", title: "Facts loaded", message: "Library refreshed." });
    } catch (err) {
      handleError(err);
    }
  }

  async function createManuscript() {
    updateStatus("Creating manuscript...");
    try {
      const payload = await apiCreateManuscript({
        baseUrl,
        token,
        title: manuscriptTitle
      });
      setManuscriptId(requireId(payload, "Create manuscript"));
      updateStatus("Manuscript created.");
      setToast({ variant: "success", title: "Manuscript ready", message: "Created successfully." });
    } catch (err) {
      handleError(err);
    }
  }

  async function attachDocument() {
    if (!manuscriptId || !documentId) {
      setError("Need manuscript ID and document ID.");
      return;
    }
    updateStatus("Linking document...");
    try {
      await apiLinkDocumentToManuscript({
        baseUrl,
        token,
        manuscriptId,
        documentId
      });
      updateStatus("Document linked.");
      setToast({ variant: "success", title: "Linked", message: "Document attached to manuscript." });
    } catch (err) {
      handleError(err);
    }
  }

  async function createParagraph() {
    if (!manuscriptId) {
      setError("Manuscript ID is required.");
      return;
    }
    updateStatus("Creating paragraph...");
    try {
      const specWithFacts = { ...paragraphSpec, allowed_fact_ids: selectedFactIds };
      const payload = await apiCreateParagraph({
        baseUrl,
        token,
        manuscriptId,
        spec: specWithFacts
      });
      const newParagraphId = requireId(payload, "Create paragraph");
      setParagraphId(newParagraphId);
      updateStatus("Paragraph created.");
      setToast({ variant: "success", title: "Paragraph created", message: "Ready to generate." });
      await fetchParagraphView(newParagraphId);
    } catch (err) {
      handleError(err);
    }
  }

  function toggleFactSelection(factId) {
    setSelectedFactIds((prev) => {
      if (prev.includes(factId)) {
        return prev.filter((id) => id !== factId);
      }
      return [...prev, factId];
    });
  }

  function setParagraphSpecForSection(section) {
    const nextIntent = intentOptions[section]?.[0] || paragraphSpec.intent;
    setParagraphSpec((prev) => ({
      ...prev,
      section,
      intent: nextIntent
    }));
  }

  async function generateParagraph() {
    if (!paragraphId) {
      setError("Paragraph ID is required.");
      return;
    }
    updateStatus("Generating paragraph...");
    try {
      const payload = await apiGenerateParagraph({ baseUrl, token, paragraphId });
      const jobId = requireId(payload, "Generate paragraph");
      setGenerateJobId(jobId);
      setJobLookupId(jobId);
      setAutoPollJobId(jobId);
      updateStatus("Generate job queued.");
      setToast({
        variant: "success",
        title: "Generate queued",
        message: "Writing job started."
      });
    } catch (err) {
      handleError(err);
    }
  }

  async function verifyParagraph() {
    if (!paragraphId) {
      setError("Paragraph ID is required.");
      return;
    }
    updateStatus("Verifying paragraph...");
    try {
      const payload = await apiVerifyParagraph({ baseUrl, token, paragraphId });
      const jobId = requireId(payload, "Verify paragraph");
      setVerifyJobId(jobId);
      setJobLookupId(jobId);
      setAutoPollJobId(jobId);
      updateStatus("Verify job queued.");
      setToast({
        variant: "success",
        title: "Verify queued",
        message: "Verification job started."
      });
    } catch (err) {
      handleError(err);
    }
  }

  async function fetchParagraphView(paragraphIdToLoad = paragraphId) {
    const trimmedId = String(paragraphIdToLoad ?? "").trim();
    if (!trimmedId) {
      setError("Paragraph ID is required.");
      return;
    }
    if (!isValidUuid(trimmedId)) {
      setError(`Paragraph ID must be a valid UUID (got "${trimmedId}").`);
      return;
    }
    updateStatus("Loading paragraph view...");
    try {
      const payload = await apiFetchParagraphView({
        baseUrl,
        token,
        paragraphId: trimmedId
      });
      setParagraphView(payload);
      if (!payload?.sentences?.length) {
        setStatus("Paragraph has no sentences yet.");
      }
      updateStatus("Paragraph view loaded.");
      setToast({ variant: "success", title: "Paragraph loaded", message: "View refreshed." });
    } catch (err) {
      handleError(err);
    }
  }

  async function fetchParagraphRuns(paragraphIdToLoad) {
    try {
      const payload = await apiFetchParagraphRuns({
        baseUrl,
        token,
        paragraphId: paragraphIdToLoad
      });
      setParagraphRuns(payload);
    } catch (err) {
      handleError(err);
    }
  }

  async function fetchJobStatus() {
    if (!jobLookupId) {
      setError("Job ID is required.");
      return;
    }
    updateStatus("Fetching job status...");
    try {
      const payload = await apiFetchJobStatus({ baseUrl, token, jobId: jobLookupId });
      setJobStatus(payload);
      if (payload?.status && isJobTerminal(payload.status)) {
        setAutoPollJobId("");
        if (payload.status === "FAILED") {
          setToast({
            variant: "danger",
            title: "Job failed",
            message: payload.error || "Job failed without error detail."
          });
        } else {
          setToast({
            variant: "success",
            title: "Job complete",
            message: `${payload.job_type} finished.`
          });
        }
      }
      updateStatus("Job status loaded.");
    } catch (err) {
      handleError(err);
    }
  }

  async function pollJobStatus(jobId) {
    try {
      const payload = await apiFetchJobStatus({ baseUrl, token, jobId });
      setJobStatus(payload);
      if (payload?.status && isJobTerminal(payload.status)) {
        setAutoPollJobId("");
        if (payload.status === "FAILED") {
          setToast({
            variant: "danger",
            title: "Job failed",
            message: payload.error || "Job failed without error detail."
          });
        } else {
          setToast({
            variant: "success",
            title: "Job complete",
            message: `${payload.job_type} finished.`
          });
        }
      }
    } catch (err) {
      handleError(err);
      setAutoPollJobId("");
    }
  }

  useEffect(() => {
    if (!paragraphView?.sentences?.length) {
      setActiveSentenceId("");
      return;
    }
    if (!activeSentenceId) {
      setActiveSentenceId(paragraphView.sentences[0].id);
    }
  }, [paragraphView, activeSentenceId]);

  useEffect(() => {
    if (!autoPollJobId) return undefined;
    const interval = setInterval(() => {
      pollJobStatus(autoPollJobId);
    }, 2000);
    return () => clearInterval(interval);
  }, [autoPollJobId, baseUrl, token]);

  useEffect(() => {
    if (!paragraphView?.paragraph?.id) {
      setParagraphRuns([]);
      return;
    }
    fetchParagraphRuns(paragraphView.paragraph.id);
  }, [paragraphView?.paragraph?.id, baseUrl, token]);

  const activeSentence = paragraphView?.sentences.find(
    (sentence) => sentence.id === activeSentenceId
  );
  const highlightedSentenceId = hoveredSentenceId || activeSentenceId;
  const paragraphJobStatus =
    jobStatus && paragraphView && jobStatus.target_id === paragraphView.paragraph.id
      ? jobStatus
      : null;
  const missingEvidence = paragraphView?.sentences?.some((sentence) =>
    sentence.verifier_failure_modes?.includes("UNCITED_CLAIM")
  );
  const paragraphStatus = paragraphView?.paragraph?.status || "UNKNOWN";
  const isJobActive = Boolean(autoPollJobId);
  const statusVariant =
    paragraphStatus === "VERIFIED"
      ? "success"
      : paragraphStatus === "PENDING_VERIFY" || paragraphStatus === "GENERATING"
        ? "warning"
        : "danger";

  if (!isAuthenticated || route === "auth") {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <div className="auth-header">
            <p className="eyebrow">OpusBlocks</p>
            <h1>Welcome back</h1>
            <p className="subtitle">
              Sign in to run extraction, generation, and verification workflows.
            </p>
          </div>
          <div className="grid">
            <Input
              label="API Base URL"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
            />
            <Input
              label="Email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password123!"
            />
          </div>
          <div className="actions auth-actions">
            <Button onClick={register}>Register</Button>
            <Button
              variant="primary"
              onClick={login}
            >
              Login
            </Button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {toast ? (
        <div className="toast-anchor">
          <Toast
            variant={toast.variant}
            title={toast.title}
            message={toast.message}
            onClose={() => setToast(null)}
          />
        </div>
      ) : null}
      <div className="mobile-warning">
        <p>
          This experience is optimized for larger screens. For best results, use a desktop
          view.
        </p>
      </div>
      <header className="app-header">
        <div>
          <p className="eyebrow">OpusBlocks</p>
          <h1>Ops Console</h1>
          <p className="subtitle">
            Run the extraction → generation → verification loop from one canvas.
          </p>
        </div>
        <div className="status-card">
          <div>
            <span>Status</span>
            <strong>{status}</strong>
          </div>
          <div>
            <span>Token</span>
            <strong>{tokenPreview}</strong>
          </div>
          <div className="header-actions">
            <nav className="header-nav">
              <Button
                size="sm"
                variant="muted"
                onClick={() => document.getElementById("library-section")?.scrollIntoView({ behavior: "smooth" })}
              >
                Library
              </Button>
              <Button
                size="sm"
                variant="muted"
                onClick={() => document.getElementById("canvas-section")?.scrollIntoView({ behavior: "smooth" })}
              >
                Canvas
              </Button>
              <Button
                size="sm"
                variant="muted"
                onClick={() => document.getElementById("inspector-section")?.scrollIntoView({ behavior: "smooth" })}
              >
                Inspector
              </Button>
            </nav>
            <Button
              size="sm"
              variant="muted"
              onClick={() => {
                setToken("");
                localStorage.removeItem(tokenKey);
                setRouteHash("auth");
              }}
            >
              Sign out
            </Button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </header>

      <div className="app-grid">
        <aside className="app-sidebar">
          <section className="panel" id="library-section">
            <h2>Documents + Facts</h2>
            <p className="muted">Upload a PDF, extract facts, then curate evidence.</p>
            <ol className="step-list">
              <li>Upload PDF</li>
              <li>Extract Facts</li>
              <li>Select Facts</li>
              <li>Create Paragraph</li>
            </ol>
            <div className="grid">
              <Input
                label="Document ID"
                value={documentId}
                onChange={(event) => setDocumentId(event.target.value)}
                placeholder="UUID"
              />
              <label className="ui-field">
                <span className="ui-field__label">Upload PDF</span>
                <input
                  className="ui-input"
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
                />
              </label>
              <Input
                label="Extract Job ID"
                value={extractJobId}
                onChange={(event) => setExtractJobId(event.target.value)}
                placeholder="UUID"
              />
            </div>
            <div className="actions">
              <Button onClick={uploadDocument} disabled={!canUpload}>
                Upload
              </Button>
              <Button onClick={extractFacts} disabled={!canExtract}>
                Extract Facts
              </Button>
              <Button onClick={loadFacts} disabled={!canExtract}>
                Load Facts
              </Button>
            </div>
            <div className="fact-filters">
              <Input
                label="Search facts"
                value={factSearch}
                onChange={(event) => setFactSearch(event.target.value)}
                placeholder="Search text..."
              />
              <div className="filter-row">
                <label className="ui-field">
                  <span className="ui-field__label">Source</span>
                  <select
                    className="ui-select"
                    value={factSourceFilter}
                    onChange={(event) => setFactSourceFilter(event.target.value)}
                  >
                    <option value="ALL">All</option>
                    <option value="PDF">PDF</option>
                    <option value="MANUAL">Manual</option>
                  </select>
                </label>
                <label className="ui-field">
                  <span className="ui-field__label">Uncertainty</span>
                  <select
                    className="ui-select"
                    value={factUncertainFilter}
                    onChange={(event) => setFactUncertainFilter(event.target.value)}
                  >
                    <option value="ALL">All</option>
                    <option value="UNCERTAIN">Uncertain</option>
                    <option value="CERTAIN">Certain</option>
                  </select>
                </label>
              </div>
            </div>
            <div className="list">
              {facts.length === 0 ? (
                <div className="empty-card">
                  <p className="muted">No facts yet.</p>
                  <p className="muted">
                    Upload a document and click Extract Facts to populate the library.
                  </p>
                </div>
              ) : filteredFacts.length === 0 ? (
                <div className="empty-card">
                  <p className="muted">No facts match your filters.</p>
                  <p className="muted">Try clearing search or adjusting filters.</p>
                </div>
              ) : (
                pagedFacts.map((fact) => (
                  <Card
                    key={fact.id}
                    className={selectedFactIds.includes(fact.id) ? "fact-card fact-card--selected" : "fact-card"}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        toggleFactSelection(fact.id);
                      }
                    }}
                  >
                    <div className="fact-card__header">
                      <Badge>{fact.source_type}</Badge>
                      {fact.is_uncertain ? <Badge variant="warning">Uncertain</Badge> : null}
                      <Button
                        size="sm"
                        variant={selectedFactIds.includes(fact.id) ? "primary" : "muted"}
                        onClick={() => toggleFactSelection(fact.id)}
                      >
                        {selectedFactIds.includes(fact.id) ? "Selected" : "Select"}
                      </Button>
                    </div>
                    <p>
                      {factSearch
                        ? fact.content.split(new RegExp(`(${factSearch})`, "gi")).map((part, index) => (
                            part.toLowerCase() === factSearch.toLowerCase() ? (
                              <mark key={`${fact.id}-match-${index}`}>{part}</mark>
                            ) : (
                              <span key={`${fact.id}-part-${index}`}>{part}</span>
                            )
                          ))
                        : fact.content}
                    </p>
                    <small>Fact ID: {fact.id}</small>
                  </Card>
                ))
              )}
            </div>
            {filteredFacts.length > factPageSize ? (
              <div className="actions">
                <Button variant="muted" onClick={() => setFactPageSize((size) => size + 5)}>
                  Show more facts
                </Button>
              </div>
            ) : null}
          </section>
        </aside>

        <main className="app-canvas">
          <section className="panel" id="canvas-section">
            <h2>Manuscript Canvas</h2>
            <p className="muted">
              Create a manuscript, link documents, and scaffold paragraphs by section.
            </p>
            <ol className="step-list">
              <li>Create Manuscript</li>
              <li>Link Document</li>
              <li>Create Paragraph</li>
              <li>Generate → Verify</li>
            </ol>
            <div className="grid">
              <Input
                label="Manuscript Title"
                value={manuscriptTitle}
                onChange={(event) => setManuscriptTitle(event.target.value)}
              />
              <Input
                label="Manuscript ID"
                value={manuscriptId}
                onChange={(event) => setManuscriptId(event.target.value)}
                placeholder="UUID"
              />
              <Input
                label="Paragraph ID"
                value={paragraphId}
                onChange={(event) => setParagraphId(event.target.value)}
                placeholder="UUID"
              />
            </div>
            <div className="actions">
              <Button onClick={createManuscript} disabled={!canCreateManuscript}>
                Create Manuscript
              </Button>
              <Button onClick={attachDocument} disabled={!canLinkDocument}>
                Link Document
              </Button>
              <Button
                variant="muted"
                onClick={() => {
                  setDocumentId("");
                  setManuscriptId("");
                  setParagraphId("");
                  setSelectedFactIds([]);
                  setFacts([]);
                  setParagraphView(null);
                  localStorage.removeItem(documentIdKey);
                  localStorage.removeItem(manuscriptIdKey);
                  localStorage.removeItem(paragraphIdKey);
                  setToast({ variant: "success", title: "Reset", message: "IDs cleared." });
                }}
              >
                Reset IDs
              </Button>
            </div>
            <div className="actions">
              <Button onClick={createParagraph} disabled={!canCreateParagraph}>
                Create Paragraph
              </Button>
              <Button
                onClick={generateParagraph}
                variant={selectedFactIds.length ? "primary" : "muted"}
                disabled={!canGenerate || isJobActive}
              >
                Generate
              </Button>
              <Button onClick={verifyParagraph} disabled={!canVerify || isJobActive}>
                Verify
              </Button>
            </div>
            <div className="actions">
              <Badge variant={statusVariant}>
                {paragraphStatus.replace("_", " ")}
              </Badge>
              {isJobActive ? <span className="muted">Job running…</span> : null}
              {paragraphJobStatus?.status === "FAILED" ? (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => {
                    if (paragraphJobStatus.job_type === "GENERATE_PARAGRAPH") {
                      generateParagraph();
                    } else if (paragraphJobStatus.job_type === "VERIFY_PARAGRAPH") {
                      verifyParagraph();
                    }
                  }}
                >
                  Retry last job
                </Button>
              ) : null}
            </div>
            <div className="builder-grid">
              <div className="builder-card">
                <h3>Section</h3>
                <div className="chip-row">
                  {sections.map((section) => (
                    <Button
                      key={section}
                      size="sm"
                      variant={paragraphSpec.section === section ? "primary" : "muted"}
                      onClick={() => setParagraphSpecForSection(section)}
                    >
                      {section}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="builder-card">
                <h3>Intent</h3>
                <div className="chip-row">
                  {intentOptions[paragraphSpec.section]?.map((intent) => (
                    <Button
                      key={intent}
                      size="sm"
                      variant={paragraphSpec.intent === intent ? "primary" : "muted"}
                      onClick={() =>
                        setParagraphSpec((prev) => ({
                          ...prev,
                          intent
                        }))
                      }
                    >
                      {intent}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="builder-card">
                <h3>Structure</h3>
                <div className="grid">
                  <Input
                    label="Evidence sentences"
                    type="number"
                    min="1"
                    value={paragraphSpec.required_structure.evidence_sentences}
                    onChange={(event) =>
                      setParagraphSpec((prev) => ({
                        ...prev,
                        required_structure: {
                          ...prev.required_structure,
                          evidence_sentences: Number(event.target.value)
                        }
                      }))
                    }
                  />
                  <Input
                    label="Min words"
                    type="number"
                    min="1"
                    value={paragraphSpec.style.target_length_words[0]}
                    onChange={(event) =>
                      setParagraphSpec((prev) => ({
                        ...prev,
                        style: {
                          ...prev.style,
                          target_length_words: [
                            Number(event.target.value),
                            prev.style.target_length_words[1]
                          ]
                        }
                      }))
                    }
                  />
                  <Input
                    label="Max words"
                    type="number"
                    min="1"
                    value={paragraphSpec.style.target_length_words[1]}
                    onChange={(event) =>
                      setParagraphSpec((prev) => ({
                        ...prev,
                        style: {
                          ...prev.style,
                          target_length_words: [
                            prev.style.target_length_words[0],
                            Number(event.target.value)
                          ]
                        }
                      }))
                    }
                  />
                </div>
              </div>
              <div className="builder-card">
                <h3>Constraints</h3>
                <Input
                  label="Allowed scope"
                  value={paragraphSpec.constraints.allowed_scope}
                  onChange={(event) =>
                    setParagraphSpec((prev) => ({
                      ...prev,
                      constraints: {
                        ...prev.constraints,
                        allowed_scope: event.target.value
                      }
                    }))
                  }
                />
              </div>
            </div>
            <div className="selection-summary">
              <Badge variant="success">{selectedFactIds.length} facts selected</Badge>
              {selectedFactIds.length === 0 ? (
                <span className="muted">Select facts from the Library to constrain generation.</span>
              ) : null}
            </div>
          </section>

          <section className="panel">
            <h2>Paragraph View</h2>
            <div className="actions">
              <Button onClick={() => fetchParagraphView()} disabled={!canViewParagraph}>
                Load Paragraph View
              </Button>
            </div>
            {paragraphView ? (
              <div className="view">
                <h3>Paragraph</h3>
                {paragraphView.sentences.length === 0 ? (
                  <div className="empty-card">
                    <p className="muted">No sentences yet.</p>
                    <p className="muted">Run Generate or Verify to populate this paragraph.</p>
                  </div>
                ) : (
                  <div className="sentences">
                    {paragraphView.sentences.map((sentence) => (
                      <Card
                        key={sentence.id}
                        className={
                          sentence.id === activeSentenceId
                            ? "sentence sentence--active"
                            : "sentence"
                        }
                        onClick={() => setActiveSentenceId(sentence.id)}
                        onMouseEnter={() => setHoveredSentenceId(sentence.id)}
                        onMouseLeave={() => setHoveredSentenceId("")}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            beginEditSentence(sentence);
                          }
                        }}
                      >
                        {editingSentenceId === sentence.id ? (
                          <div className="sentence-edit">
                            <textarea
                              className="ui-textarea"
                              rows={3}
                              value={editingSentenceText}
                              onChange={(event) => setEditingSentenceText(event.target.value)}
                            />
                            <div className="actions">
                              <Button size="sm" variant="primary" onClick={() => saveSentenceEdit(sentence.id)}>
                                Save
                              </Button>
                              <Button size="sm" variant="muted" onClick={cancelEditSentence}>
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <p>{sentence.text}</p>
                            <div className="sentence-actions">
                              <Button size="sm" variant="muted" onClick={() => beginEditSentence(sentence)}>
                                Edit
                              </Button>
                            </div>
                          </>
                        )}
                        <small>
                          {sentence.supported ? "Verified" : "Needs review"} · {sentence.sentence_type}
                        </small>
                        {!sentence.supported && sentence.verifier_failure_modes.length ? (
                          <div className="failure-modes">
                            {sentence.verifier_failure_modes.map((mode) => (
                              <Badge key={mode} variant="danger">
                                {mode}
                              </Badge>
                            ))}
                          </div>
                        ) : null}
                        <div className="citations">
                          {paragraphView.links
                            .filter((link) => link.sentence_id === sentence.id)
                            .map((link, index) => (
                              <Badge
                                key={`${link.sentence_id}-${link.fact_id}-${index}`}
                                className={
                                  hoveredSentenceId === sentence.id
                                    ? "chip chip--highlight"
                                    : "chip"
                                }
                              >
                                {link.fact_id}
                              </Badge>
                            ))}
                          {paragraphView.links.filter((link) => link.sentence_id === sentence.id).length === 0 ? (
                            <Badge key={`${sentence.id}-uncited`} variant="danger">Uncited</Badge>
                          ) : null}
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
                {missingEvidence ? (
                  <div className="empty-card">
                    <p className="muted">Missing evidence detected.</p>
                    <p className="muted">Review uncited sentences or add more facts.</p>
                  </div>
                ) : null}
                <h3>Facts</h3>
                {paragraphView.facts.length === 0 ? (
                  <div className="empty-card">
                    <p className="muted">No facts attached to this manuscript.</p>
                    <p className="muted">Link a document or add manual facts.</p>
                  </div>
                ) : (
                  <div className="facts">
                    {paragraphView.facts.map((fact) => (
                      <Card
                        key={fact.id}
                        className={
                          paragraphView.links.some(
                            (link) =>
                              link.fact_id === fact.id &&
                              link.sentence_id === highlightedSentenceId
                          )
                            ? "compact-card fact-card--selected"
                            : "compact-card"
                        }
                      >
                        <Badge>{fact.source_type}</Badge>
                        <p>{fact.content}</p>
                        <small>{fact.id}</small>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </section>
        </main>

        <aside className="app-inspector" id="inspector-section">
          <section className="panel">
            <h2>Jobs</h2>
            <div className="grid">
              <Input
                label="Job ID Lookup"
                value={jobLookupId}
                onChange={(event) => setJobLookupId(event.target.value)}
                placeholder="UUID"
              />
              <Input label="Generate Job ID" value={generateJobId} readOnly />
              <Input label="Verify Job ID" value={verifyJobId} readOnly />
            </div>
            <div className="actions">
              <Button onClick={fetchJobStatus}>Check Job Status</Button>
              {jobStatus?.status === "FAILED" ? (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => {
                    if (jobStatus.job_type === "GENERATE_PARAGRAPH") {
                      generateParagraph();
                    } else if (jobStatus.job_type === "VERIFY_PARAGRAPH") {
                      verifyParagraph();
                    }
                  }}
                >
                  Retry Job
                </Button>
              ) : null}
            </div>
            {jobStatus ? (
              <Card className="job">
                <strong>{jobStatus.job_type}</strong>
                <span>Status: {jobStatus.status}</span>
                {jobStatus.error ? <p className="error">{jobStatus.error}</p> : null}
              </Card>
            ) : null}
          </section>
          <section className="panel">
            <h2>Inspector</h2>
            {paragraphView ? (
              <div className="inspector">
                <div>
                  <span className="inspector__label">Paragraph</span>
                  <p className="inspector__value">{paragraphView.paragraph.id}</p>
                  <p className="muted">
                    {paragraphView.paragraph.section} · {paragraphView.paragraph.intent}
                  </p>
                  <p className="muted">Status: {paragraphView.paragraph.status}</p>
                </div>
                <div>
                  <span className="inspector__label">Allowed Facts</span>
                  <p className="inspector__value">
                    {paragraphView.paragraph.allowed_fact_ids.length}
                  </p>
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
                <div>
                  <span className="inspector__label">Active Sentence</span>
                  {activeSentence ? (
                    <>
                      <p className="inspector__value">{activeSentence.text}</p>
                      <p className="muted">
                        {activeSentence.supported ? "Verified" : "Needs review"} ·{" "}
                        {activeSentence.sentence_type}
                      </p>
                      {activeSentence.verifier_explanation ? (
                        <p className="muted">{activeSentence.verifier_explanation}</p>
                      ) : null}
                    </>
                  ) : (
                    <p className="muted">Select a sentence to inspect.</p>
                  )}
                </div>
                <div>
                  <span className="inspector__label">Run History</span>
                  {paragraphRuns.length ? (
                    <div className="run-list">
                      {paragraphRuns.map((run) => (
                        <Card key={run.id} className="run-card">
                          <strong>{run.run_type}</strong>
                          <span className="muted">{run.model}</span>
                          <span className="muted">
                            {new Date(run.created_at).toLocaleString()}
                          </span>
                          {run.trace_id ? (
                            <span className="muted">Trace: {run.trace_id}</span>
                          ) : null}
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <p className="muted">No runs recorded yet.</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="muted">Load a paragraph to inspect details.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

export default App;
