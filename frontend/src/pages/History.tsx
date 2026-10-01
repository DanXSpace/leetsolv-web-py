import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Delta } from '../types';
import { deltaSlug } from '../types';

export default function History() {
  const [items, setItems] = useState<Delta[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function load() {
    try {
      setItems(await api.history());
      setErr('');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to load');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function undo() {
    setBusy(true);
    setErr('');
    try {
      await api.undo();
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'nothing to undo');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>History</h1>
      <div className="row">
        <button className="primary" onClick={undo} disabled={busy || items.length === 0}>
          Undo last action
        </button>
      </div>
      {err && <p className="error">{err}</p>}
      <ul className="cards">
        {items.map((d) => (
          <li className="card history-item" key={d.id}>
            <span className={`badge badge-action badge-${d.action}`}>{d.action}</span>
            <span className="title">{deltaSlug(d)}</span>
            <span className="muted">{d.created_at.replace('T', ' ').slice(0, 16)}</span>
          </li>
        ))}
      </ul>
      {items.length === 0 && <p className="empty">No history yet.</p>}
    </div>
  );
}
