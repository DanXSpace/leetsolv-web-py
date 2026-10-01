export interface Problem {
  id: number;
  url: string;
  slug: string;
  note: string;
  familiarity: number; // 0..4
  importance: number; // 0..3
  last_reviewed: string | null;
  next_review: string | null;
  review_count: number;
  ease_factor: number;
  title: string | null;
  difficulty: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface AddInput {
  url: string;
  note: string;
  familiarity: number;
  importance: number;
  memory: number;
}

export interface ReviewInput {
  target: string;
  familiarity: number;
  importance: number;
  memory: number;
}

export interface Delta {
  id: number;
  action: string; // add | update | delete
  question_id: number;
  old_state: Record<string, unknown> | null;
  new_state: Record<string, unknown> | null;
  created_at: string;
}

export interface Status {
  total: number;
  total_due: number;
  total_upcoming: number;
  due: Problem[];
  upcoming: Problem[];
}

export interface Settings {
  randomize_interval: boolean;
  overdue_penalty: boolean;
  overdue_limit: number;
  top_k_due: number;
  top_k_upcoming: number;
}

export const FAMILIARITY_LABELS = ['Very hard', 'Hard', 'Medium', 'Easy', 'Very easy'];
export const IMPORTANCE_LABELS = ['Low', 'Medium', 'High', 'Critical'];
export const MEMORY_LABELS = ['Reasoned', 'Partial', 'Full'];

export function familiarityLabel(n: number): string {
  return FAMILIARITY_LABELS[n] ?? String(n);
}

export function importanceLabel(n: number): string {
  return IMPORTANCE_LABELS[n] ?? String(n);
}

export function deltaSlug(d: Delta): string {
  const s = (d.new_state ?? d.old_state) as { slug?: string; url?: string } | null;
  return s?.slug ?? s?.url ?? `#${d.question_id}`;
}
