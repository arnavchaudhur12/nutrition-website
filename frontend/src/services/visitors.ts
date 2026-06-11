import { API_BASE_URL } from "../config/api";

type VisitorCountResponse = {
  total_visitors: number;
};

async function parseError(response: Response, fallback: string): Promise<Error> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return new Error(body?.detail ?? fallback);
}

export async function fetchTotalVisitors(): Promise<VisitorCountResponse> {
  const response = await fetch(`${API_BASE_URL}/visitors`);

  if (!response.ok) {
    throw await parseError(response, "Unable to load visitor count.");
  }

  return (await response.json()) as VisitorCountResponse;
}

export async function trackVisitor(): Promise<VisitorCountResponse> {
  const response = await fetch(`${API_BASE_URL}/visitors/track`, {
    method: "POST"
  });

  if (!response.ok) {
    throw await parseError(response, "Unable to track visitor count.");
  }

  return (await response.json()) as VisitorCountResponse;
}
