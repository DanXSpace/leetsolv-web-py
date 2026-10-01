import { useState } from 'react';
import { api } from '../api';
import type { Problem } from '../types';
import { FAMILIARITY_LABELS, IMPORTANCE_LABELS, MEMORY_LABELS } from '../types';

export default function ReviewForm({
  p,
  onDone,
  onCancel,
}: {
  p: Problem;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [fam, setFam] = useState(p.familiarity + 1);
  const [mem, setMem] = useState(1);
  const [imp, setImp] = useState(p.importance + 1);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const showMemory = fam >= 3; // 1-based: Medium or better

  async function submit() {
    setBusy(true);
    setErr('');
    try {
      await api.review({
        target: String(p.id),
        familiarity: fam - 1,
        importance: imp - 1,
        memory: showMemory ? mem - 1 : 0,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'review failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="review-form">
      <div className="field">
        <label>Familiarity</label>
        <select value={fam} onChange={(e) => setFam(Number(e.target.value))}>
          {FAMILIARITY_LABELS.map((l, i) => (
            <option key={l} value={i + 1}>
              {i + 1} · {l}
            </option>
          ))}
        </select>
      </div>
      {showMemory && (
        <div className="field">
          <label>Memory use</label>
          <select value={mem} onChange={(e) => setMem(Number(e.target.value))}>
            {MEMORY_LABELS.map((l, i) => (
              <option key={l} value={i + 1}>
                {i + 1} · {l}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="field">
        <label>Importance</label>
        <select value={imp} onChange={(e) => setImp(Number(e.target.value))}>
          {IMPORTANCE_LABELS.map((l, i) => (
            <option key={l} value={i + 1}>
              {i + 1} · {l}
            </option>
          ))}
        </select>
      </div>
      {err && <p className="error">{err}</p>}
      <div className="row">
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? 'Saving…' : 'Submit review'}
        </button>
        <button onClick={onCancel} disabled={busy}>
          Cancel
        </button>
      </div>
    </div>
  );
}
