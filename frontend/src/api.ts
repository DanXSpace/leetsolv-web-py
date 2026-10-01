import type { AddInput, Delta, Problem, ReviewInput, Settings, Status } from './types';

export type Role = 'owner' | 'mentor' | 'anonymous';

let shareToken: string | null = null;

export function setShareToken(t: string | null) {
  shareToken = t;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === '') continue;
    parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  }
  return parts.length ? `?${parts.join('&')}` : '';
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let url = path;
  if (shareToken) {
    url += (url.includes('?') ? '&' : '?') + 'share=' + encodeURIComponent(shareToken);
  }
  const res = await fetch(url, {
    method,
    credentials: 'include',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const detail = (data as { detail?: unknown })?.detail;
    const message = typeof detail === 'string' ? detail : `Request failed (${res.status})`;
    throw new ApiError(res.status, message);
  }
  return data as T;
}

export const api = {
  me: () => request<{ role: Role; github_login: string | null }>('GET', '/api/auth/me'),
  loginUrl: () => request<{ authorize_url: string }>('GET', '/api/auth/login'),
  logout: () => request<null>('POST', '/api/auth/logout'),
  problems: () => request<Problem[]>('GET', '/api/problems'),
  problem: (id: number) => request<Problem>('GET', `/api/problems/${id}`),
  add: (b: AddInput) => request<Problem>('POST', '/api/problems', b),
  review: (b: ReviewInput) => request<Problem>('POST', '/api/review', b),
  editNote: (id: number, note: string) => request<Problem>('PATCH', `/api/problems/${id}/note`, { note }),
  remove: (id: number) => request<null>('DELETE', `/api/problems/${id}`),
  undo: () => request<null>('POST', '/api/undo'),
  history: () => request<Delta[]>('GET', '/api/history'),
  status: () => request<Status>('GET', '/api/status'),
  search: (params: Record<string, string | number | boolean | undefined>) =>
    request<Problem[]>('GET', '/api/search' + buildQuery(params)),
  settings: () => request<Settings>('GET', '/api/settings'),
  updateSettings: (b: Partial<Settings>) => request<Settings>('PUT', '/api/settings', b),
  share: () => request<{ token: string; url: string }>('GET', '/api/auth/share'),
  resetShare: () => request<{ token: string; url: string }>('POST', '/api/auth/share/reset'),
};
