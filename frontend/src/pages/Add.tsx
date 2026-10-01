import { useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api';
import { FAMILIARITY_LABELS, IMPORTANCE_LABELS, MEMORY_LABELS } from '../types';

export default function Add() {
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [fam, setFam] = useState(3);
  const [mem, setMem] = useState(1);
  const [imp, setImp] = useState(2);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [ok, setOk] = useState('');

  const showMemory = fam >= 3;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr('');
    setOk('');
    try {
      const p = await api.add({
        url,
        note,
        familiarity: fam - 1,
        importance: imp - 1,
        memory: showMemory ? mem - 1 : 0,
      });
      setOk(`Added “${p.title || p.slug}”.`);
      setUrl('');
      setNote('');
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : 'failed to add');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Add problem</h1>
      <form className="form" onSubmit={submit}>
        <div className="field">
          <label>LeetCode URL</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://leetcode.com/problems/two-sum"
            required
          />
        </div>
        <div className="field">
          <label>Note</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="Your approach / gotchas (optional)"
          />
        </div>
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
        {ok && <p className="ok">{ok}</p>}
        <button className="primary" type="submit" disabled={busy}>
          {busy ? 'Adding…' : 'Add problem'}
        </button>
      </form>
    </div>
  );
}
