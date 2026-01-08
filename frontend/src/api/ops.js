import { apiForm, apiJson } from "./client";

export function registerUser({ baseUrl, email, password }) {
  return apiJson("/auth/register", {
    method: "POST",
    baseUrl,
    body: { email, password }
  });
}

export function loginUser({ baseUrl, email, password }) {
  return apiJson("/auth/login", {
    method: "POST",
    baseUrl,
    body: { email, password }
  });
}

export function uploadDocument({ baseUrl, token, file }) {
  const formData = new FormData();
  formData.append("file", file);
  return apiForm("/documents/upload", {
    baseUrl,
    token,
    formData
  });
}

export function extractDocumentFacts({ baseUrl, token, documentId }) {
  return apiJson(`/documents/${documentId}/extract_facts`, {
    method: "POST",
    baseUrl,
    token
  });
}

export function fetchDocumentFacts({ baseUrl, token, documentId }) {
  return apiJson(`/documents/${documentId}/facts`, {
    baseUrl,
    token
  });
}

export function createManuscript({ baseUrl, token, title }) {
  return apiJson("/manuscripts", {
    method: "POST",
    baseUrl,
    token,
    body: { title }
  });
}

export function linkDocumentToManuscript({ baseUrl, token, manuscriptId, documentId }) {
  return apiJson(`/manuscripts/${manuscriptId}/documents/${documentId}`, {
    method: "POST",
    baseUrl,
    token
  });
}

export function createParagraph({ baseUrl, token, manuscriptId, spec }) {
  return apiJson("/paragraphs", {
    method: "POST",
    baseUrl,
    token,
    body: { manuscript_id: manuscriptId, spec }
  });
}

export function generateParagraph({ baseUrl, token, paragraphId }) {
  return apiJson(`/paragraphs/${paragraphId}/generate`, {
    method: "POST",
    baseUrl,
    token
  });
}

export function verifyParagraph({ baseUrl, token, paragraphId }) {
  return apiJson(`/paragraphs/${paragraphId}/verify`, {
    method: "POST",
    baseUrl,
    token
  });
}

export function fetchParagraphView({ baseUrl, token, paragraphId }) {
  return apiJson(`/paragraphs/${paragraphId}/view`, {
    baseUrl,
    token
  });
}

export function fetchParagraphRuns({ baseUrl, token, paragraphId }) {
  const params = new URLSearchParams({ paragraph_id: paragraphId });
  return apiJson(`/runs?${params.toString()}`, {
    baseUrl,
    token
  });
}

export function fetchJobStatus({ baseUrl, token, jobId }) {
  return apiJson(`/jobs/${jobId}`, {
    baseUrl,
    token
  });
}

export function updateSentence({ baseUrl, token, sentenceId, text }) {
  return apiJson(`/sentences/${sentenceId}`, {
    method: "PATCH",
    baseUrl,
    token,
    body: { text }
  });
}
