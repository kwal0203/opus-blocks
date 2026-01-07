import { API_BASE_URL } from "../config";

function buildHeaders(token) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseResponse(response) {
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function resolveErrorPayload(payload) {
  if (!payload) {
    return null;
  }
  if (typeof payload === "string") {
    return payload;
  }
  if (typeof payload.detail === "string") {
    return payload.detail;
  }
  if (Array.isArray(payload.detail)) {
    const messages = payload.detail
      .map((item) => {
        if (!item) return null;
        if (typeof item === "string") return item;
        if (typeof item.msg === "string") return item.msg;
        return null;
      })
      .filter(Boolean);
    if (messages.length) {
      return messages.join("; ");
    }
  }
  if (typeof payload.message === "string") {
    return payload.message;
  }
  return null;
}

export async function apiJson(
  path,
  { method = "GET", token, body, baseUrl = API_BASE_URL } = {}
) {
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: buildHeaders(token),
    body: body ? JSON.stringify(body) : undefined
  });

  const payload = await parseResponse(response);
  if (!response.ok) {
    const detail = resolveErrorPayload(payload);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}

export async function apiForm(
  path,
  { method = "POST", token, formData, baseUrl = API_BASE_URL } = {}
) {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: formData
  });

  const payload = await parseResponse(response);
  if (!response.ok) {
    const detail = resolveErrorPayload(payload);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}
