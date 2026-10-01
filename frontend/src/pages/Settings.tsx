import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api';
import type { Settings as SettingsT } from '../types';

export default function SettingsPage() {
  const [s, setS] = useState<SettingsT | null>(null);
  const [share, setShare] = useState<{ token: string; url: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [ok, setOk] = useState('');

  async function load() {
    try {
      setS(await api.settings());
      setShare(await api.share());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to load');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function save(e: FormEvent) {
    e.preventDefault();
    if (!s) return;
    setBusy(true);
    setErr('');
    setOk('');
    try {
      setS(await api.updateSettings(s));
      setOk('Saved.');
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : 'failed to save');
    } finally {
      setBusy(false);
    }
  }

  async function resetShare() {
    try {
      setShare(await api.resetShare());
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : 'failed to reset share link');
    }
  }

  if (!s) return <p className="loading">Loading…</p>;

  return (
    <div>
      <h1>Settings</h1>
      <form className="form" onSubmit={save}>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={s.randomize_interval}
            onChange={(e) => setS({ ...s, randomize_interval: e.target.checked })}
          />
          Randomize intervals (±1 day)
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={s.overdue_penalty}
            onChange={(e) => setS({ ...s, overdue_penalty: e.target.checked })}
          />
          Penalize overdue reviews
        </label>
        <div className="field">
          <label>Overdue limit (days)</label>
          <input
            type="number"
            min={1}
            max={90}
            value={s.overdue_limit}
            onChange={(e) => setS({ ...s, overdue_limit: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>Top-K due</label>
          <input
            type="number"
            min={1}
            max={100}
            value={s.top_k_due}
            onChange={(e) => setS({ ...s, top_k_due: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>Top-K upcoming</label>
          <input
            type="number"
            min={1}
            max={100}
            value={s.top_k_upcoming}
            onChange={(e) => setS({ ...s, top_k_upcoming: Number(e.target.value) })}
          />
        </div>
        {err && <p className="error">{err}</p>}
        {ok && <p className="ok">{ok}</p>}
        <button className="primary" type="submit" disabled={busy}>
          Save
        </button>
      </form>

      <section className="card">
        <h2>Mentor share link</h2>
        <p className="sub">Anyone with this link gets a read-only view of the whole app, including notes.</p>
        {share && (
          <div className="row">
            <input readOnly value={share.url} onFocus={(e) => e.target.select()} style={{ flex: 1 }} />
            <button onClick={() => navigator.clipboard.writeText(share.url)}>Copy</button>
            <button className="danger" onClick={resetShare}>
              Regenerate
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
