import { useEffect, useMemo, useState } from "react";

import Badge from "./components/ui/Badge";
import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import Input from "./components/ui/Input";
import Textarea from "./components/ui/Textarea";
import { isJobTerminal } from "./api/jobs";
import {
  createManuscript as apiCreateManuscript,
  createParagraph as apiCreateParagraph,
  extractDocumentFacts as apiExtractDocumentFacts,
  fetchDocumentFacts as apiFetchDocumentFacts,
  fetchJobStatus as apiFetchJobStatus,
  fetchParagraphView as apiFetchParagraphView,
  generateParagraph as apiGenerateParagraph,
  linkDocumentToManuscript as apiLinkDocumentToManuscript,
  loginUser as apiLoginUser,
  registerUser as apiRegisterUser,
  uploadDocument as apiUploadDocument,
  verifyParagraph as apiVerifyParagraph
} from "./api/ops";
import { API_BASE_URL } from "./config";

/** @typedef {import("./api/types").Fact} Fact */
/** @typedef {import("./api/types").ParagraphView} ParagraphView */
/** @typedef {import("./api/types").Job} Job */

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

function requireId(payload, label) {
  if (!payload || !payload.id) {
    throw new Error(`${label} response missing id`);
  }
  return payload.id;
}

function App() {
  const [baseUrl, setBaseUrl] = useState(API_BASE_URL);
  const [token, setToken] = useState(localStorage.getItem(tokenKey) || "");
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [documentFile, setDocumentFile] = useState(/** @type {File | null} */ (null));
  const [extractJobId, setExtractJobId] = useState("");
  const [facts, setFacts] = useState(/** @type {Fact[]} */ ([]));
  const [factSearch, setFactSearch] = useState("");
  const [factSourceFilter, setFactSourceFilter] = useState("ALL");
  const [factUncertainFilter, setFactUncertainFilter] = useState("ALL");
  const [selectedFactIds, setSelectedFactIds] = useState([]);
  const [manuscriptTitle, setManuscriptTitle] = useState("Test Manuscript");
  const [manuscriptId, setManuscriptId] = useState("");
  const [paragraphSpec, setParagraphSpec] = useState(
    JSON.stringify(defaultSpec, null, 2)
  );
  const [paragraphId, setParagraphId] = useState("");
  const [generateJobId, setGenerateJobId] = useState("");
  const [verifyJobId, setVerifyJobId] = useState("");
  const [paragraphView, setParagraphView] = useState(
    /** @type {ParagraphView | null} */ (null)
  );
  const [jobLookupId, setJobLookupId] = useState("");
  const [jobStatus, setJobStatus] = useState(/** @type {Job | null} */ (null));
  const [autoPollJobId, setAutoPollJobId] = useState("");
  const [activeSentenceId, setActiveSentenceId] = useState("");

  const tokenPreview = useMemo(() => {
    if (!token) return "Not set";
    return `${token.slice(0, 16)}...${token.slice(-8)}`;
  }, [token]);

  const isAuthenticated = Boolean(token);
  const sections = ["Introduction", "Methods", "Results", "Discussion"];

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

  function updateStatus(message) {
    setStatus(message);
    setError("");
  }

  function handleError(err) {
    const message = err instanceof Error ? err.message : String(err);
    setError(message);
    setStatus("Error");
  }

  async function register() {
    updateStatus("Registering...");
    try {
      await apiRegisterUser({ baseUrl, email, password });
      updateStatus("Registered.");
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
      const payload = await apiExtractDocumentFacts({ baseUrl, token, documentId });
      setExtractJobId(requireId(payload, "Extract facts"));
      updateStatus("Extract job queued.");
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
    } catch (err) {
      handleError(err);
    }
  }

  async function createParagraph() {
    if (!manuscriptId) {
      setError("Manuscript ID is required.");
      return;
    }
    let spec;
    try {
      spec = JSON.parse(paragraphSpec);
    } catch (err) {
      setError("Paragraph spec must be valid JSON.");
      return;
    }
    updateStatus("Creating paragraph...");
    try {
      const specWithFacts = { ...spec, allowed_fact_ids: selectedFactIds };
      const payload = await apiCreateParagraph({
        baseUrl,
        token,
        manuscriptId,
        spec: specWithFacts
      });
      setParagraphId(requireId(payload, "Create paragraph"));
      updateStatus("Paragraph created.");
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
    try {
      const spec = JSON.parse(paragraphSpec);
      const intentDefaults = {
        Introduction: "Background Context",
        Methods: "Study Design",
        Results: "Primary Results",
        Discussion: "Result Interpretation"
      };
      const nextSpec = {
        ...spec,
        section,
        intent: intentDefaults[section] || spec.intent
      };
      setParagraphSpec(JSON.stringify(nextSpec, null, 2));
    } catch (err) {
      setError("Paragraph spec must be valid JSON.");
    }
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
    } catch (err) {
      handleError(err);
    }
  }

  async function fetchParagraphView() {
    if (!paragraphId) {
      setError("Paragraph ID is required.");
      return;
    }
    updateStatus("Loading paragraph view...");
    try {
      const payload = await apiFetchParagraphView({ baseUrl, token, paragraphId });
      setParagraphView(payload);
      updateStatus("Paragraph view loaded.");
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

  const activeSentence = paragraphView?.sentences.find(
    (sentence) => sentence.id === activeSentenceId
  );

  if (!isAuthenticated) {
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
            <Button variant="primary" onClick={login}>Login</Button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
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
          <div className="actions">
            <Button size="sm" variant="muted" onClick={() => {
              setToken("");
              localStorage.removeItem(tokenKey);
            }}>
              Sign out
            </Button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </header>

      <div className="app-grid">
        <aside className="app-sidebar">
          <section className="panel">
            <h2>Connection</h2>
            <div className="grid">
              <Input
                label="Base URL"
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
            <div className="actions">
              <Button onClick={register}>Register</Button>
              <Button variant="primary" onClick={login}>Login</Button>
            </div>
          </section>

          <section className="panel">
            <h2>Documents + Facts</h2>
            <p className="muted">Upload a PDF, extract facts, then curate evidence.</p>
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
              <Button onClick={uploadDocument}>Upload</Button>
              <Button onClick={extractFacts}>Extract Facts</Button>
              <Button onClick={loadFacts}>Load Facts</Button>
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
              {filteredFacts.length === 0 ? (
                <p className="muted">No facts loaded yet.</p>
              ) : (
                filteredFacts.map((fact) => (
                  <Card
                    key={fact.id}
                    className={selectedFactIds.includes(fact.id) ? "fact-card fact-card--selected" : "fact-card"}
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
                    <p>{fact.content}</p>
                    <small>Fact ID: {fact.id}</small>
                  </Card>
                ))
              )}
            </div>
          </section>
        </aside>

        <main className="app-canvas">
          <section className="panel">
            <h2>Manuscript Canvas</h2>
            <p className="muted">
              Create a manuscript, link documents, and scaffold paragraphs by section.
            </p>
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
              <Button onClick={createManuscript}>Create Manuscript</Button>
              <Button onClick={attachDocument}>Link Document</Button>
            </div>
            <div className="section-grid">
              {sections.map((section) => (
                <Card key={section} className="section-card">
                  <div>
                    <h3>{section}</h3>
                    <p className="muted">Add a paragraph scaffold for this section.</p>
                  </div>
                  <Button
                    size="sm"
                    variant="muted"
                    onClick={() => setParagraphSpecForSection(section)}
                  >
                    Set Spec
                  </Button>
                </Card>
              ))}
            </div>
            <Textarea
              className="textarea"
              label="Paragraph Spec (JSON)"
              value={paragraphSpec}
              onChange={(event) => setParagraphSpec(event.target.value)}
              rows={12}
            />
            <div className="actions">
              <Button onClick={createParagraph}>Create Paragraph</Button>
              <Button onClick={generateParagraph}>Generate</Button>
              <Button onClick={verifyParagraph}>Verify</Button>
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
              <Button onClick={fetchParagraphView}>Load Paragraph View</Button>
            </div>
            {paragraphView ? (
              <div className="view">
                <h3>Paragraph</h3>
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
                    >
                      <p>{sentence.text}</p>
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
                          .map((link) => (
                            <Badge key={link.id} className="chip">
                              {link.fact_id}
                            </Badge>
                          ))}
                      </div>
                    </Card>
                  ))}
                </div>
                <h3>Facts</h3>
                <div className="facts">
                  {paragraphView.facts.map((fact) => (
                    <Card key={fact.id}>
                      <Badge>{fact.source_type}</Badge>
                      <p>{fact.content}</p>
                      <small>{fact.id}</small>
                    </Card>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        </main>

        <aside className="app-inspector">
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
