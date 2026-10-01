import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import type { Problem } from '../types';
import { FAMILIARITY_LABELS, IMPORTANCE_LABELS } from '../types';
import ProblemBadges from '../components/ProblemBadges';

export default function Problems() {
  const { role } = useAuth();
  const isOwner = role === 'owner';
  const [list, setList] = useState<Problem[]>([]);
  const [q, setQ] = useState('');
  const [fam, setFam] = useState('');
  const [imp, setImp] = useState('');
  const [dueOnly, setDueOnly] = useState(false);
  const [err, setErr] = useState('');
  const [selected, setSelected] = useState<Problem | null>(null);

  const load = useCallback(async () => {
    try {
      setList(
        await api.search({
          query: q || undefined,
          familiarity: fam === '' ? undefined : Number(fam),
          importance: imp === '' ? undefined : Number(imp),
          due_only: dueOnly || undefined,
        }),
      );
      setErr('');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to load');
    }
  }, [q, fam, imp, dueOnly]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <h1>Problems</h1>
      <div className="filters">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search slug or note…" />
        <select value={fam} onChange={(e) => setFam(e.target.value)}>
          <option value="">Any familiarity</option>
          {FAMILIARITY_LABELS.map((l, i) => (
            <option key={l} value={i}>
              {l}
            </option>
          ))}
        </select>
        <select value={imp} onChange={(e) => setImp(e.target.value)}>
          <option value="">Any importance</option>
          {IMPORTANCE_LABELS.map((l, i) => (
            <option key={l} value={i}>
              {l}
            </option>
          ))}
        </select>
        <label className="checkbox">
          <input type="checkbox" checked={dueOnly} onChange={(e) => setDueOnly(e.target.checked)} /> Due only
        </label>
      </div>
      {err && <p className="error">{err}</p>}
      <p className="sub">
        {list.length} result{list.length === 1 ? '' : 's'}
      </p>
      <ul className="cards">
        {list.map((p) => (
          <li
            className="card"
            key={p.id}
            onClick={() => setSelected(p.id === selected?.id ? null : p)}
          >
            <div className="card-head">
              <div>
                <a
                  className="title"
                  href={p.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(e) => e.stopPropagation()}
                >
                  {p.title || p.slug}
                </a>
                {p.title && <div className="slug">{p.slug}</div>}
                <div className="meta">
                  <ProblemBadges p={p} />
                  <span className="due">next {p.next_review}</span>
                </div>
              </div>
              {p.difficulty && (
                <span className={`diff diff-${p.difficulty.toLowerCase()}`}>{p.difficulty}</span>
              )}
            </div>
            {selected?.id === p.id && <Detail p={p} isOwner={isOwner} onChanged={load} />}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Detail({ p, isOwner, onChanged }: { p: Problem; isOwner: boolean; onChanged: () => void }) {
  const [note, setNote] = useState(p.note);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function saveNote() {
    setBusy(true);
    setErr('');
    try {
      await api.editNote(p.id, note);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to save');
    } finally {
      setBusy(false);
    }
  }

  async function del() {
    if (!window.confirm(`Delete “${p.title || p.slug}”?`)) return;
    try {
      await api.remove(p.id);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to delete');
    }
  }

  return (
    <div className="detail" onClick={(e) => e.stopPropagation()}>
      {p.tags && p.tags.length > 0 && (
        <div className="tags">
          {p.tags.map((t) => (
            <span key={t} className="tag">
              {t}
            </span>
          ))}
        </div>
      )}
      <div className="detail-row">
        <span>Last reviewed</span>
        <span>{p.last_reviewed ?? '—'}</span>
        <span>Next review</span>
        <span>{p.next_review ?? '—'}</span>
        <span>Reviews</span>
        <span>{p.review_count}</span>
        <span>Ease factor</span>
        <span>{p.ease_factor.toFixed(3)}</span>
      </div>
      {isOwner ? (
        <div className="field">
          <label>Note</label>
          <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
          <div className="row">
            <button className="primary" onClick={saveNote} disabled={busy}>
              Save note
            </button>
            <button className="danger" onClick={del}>
              Delete
            </button>
          </div>
          {err && <p className="error">{err}</p>}
        </div>
      ) : (
        p.note && <p className="note">{p.note}</p>
      )}
    </div>
  );
}
