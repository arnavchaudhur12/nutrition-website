import { API_BASE_URL } from "../config/api";

type VisitorSessionResponse = {
  session_id: string;
  active_visitors: number;
};

type VisitorCountResponse = {
  active_visitors: number;
};

async function parseError(response: Response, fallback: string): Promise<Error> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return new Error(body?.detail ?? fallback);
}

export async function connectVisitor(): Promise<VisitorSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/visitors/connect`, {
    method: "POST"
  });

  if (!response.ok) {
    throw await parseError(response, "Unable to start visitor tracking.");
  }

  return (await response.json()) as VisitorSessionResponse;
}

export async function sendVisitorHeartbeat(sessionId: string): Promise<VisitorSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/visitors/heartbeat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: sessionId })
  });

  if (!response.ok) {
    throw await parseError(response, "Unable to refresh visitor count.");
  }

  return (await response.json()) as VisitorSessionResponse;
}

export async function fetchActiveVisitors(): Promise<VisitorCountResponse> {
  const response = await fetch(`${API_BASE_URL}/visitors`);

  if (!response.ok) {
    throw await parseError(response, "Unable to load visitor count.");
  }

  return (await response.json()) as VisitorCountResponse;
}

export async function disconnectVisitor(sessionId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/visitors/disconnect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: sessionId }),
    keepalive: true
  }).catch(() => undefined);
}
