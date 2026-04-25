import type { BatchRunResponse, DemoFlowResponse, ProspectRunResponse, ScenarioListResponse } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8000");

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let detail = `Request failed with status ${response.status}`;
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      detail = payload.detail;
    }
  } catch {
    const text = await response.text();
    if (text) {
      detail = text;
    }
  }

  throw new Error(detail);
}

export async function fetchHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseResponse(response);
}

export async function fetchScenarios(): Promise<ScenarioListResponse> {
  const response = await fetch(`${API_BASE_URL}/run-prospect/scenarios`);
  return parseResponse(response);
}

export async function fetchBatchSummary(): Promise<BatchRunResponse> {
  const response = await fetch(`${API_BASE_URL}/run-prospect/batch`);
  return parseResponse(response);
}

export async function runProspect(payload?: {
  company_name?: string;
  scenario_name?: string;
  reply_text?: string;
}): Promise<ProspectRunResponse> {
  const response = await fetch(`${API_BASE_URL}/run-prospect`, {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  return parseResponse(response);
}

export async function runDemoFlow(payload?: {
  company_name?: string;
  scenario_name?: string;
  reply_text?: string;
}): Promise<DemoFlowResponse> {
  const response = await fetch(`${API_BASE_URL}/run-prospect/demo-flow`, {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  return parseResponse(response);
}

export { API_BASE_URL };
