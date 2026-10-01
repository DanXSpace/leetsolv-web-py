import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import type { Problem, Status } from '../types';
import ProblemBadges from '../components/ProblemBadges';
import ReviewForm from '../components/ReviewForm';

export default function Queue() {
  const { role } = useAuth();
  const isOwner = role === 'owner';
  const [status, setStatus] = useState<Status | null>(null);
  const [err, setErr] = useState('');
  const [reviewing, setReviewing] = useState<Problem | null>(null);

  const load = useCallback(async () => {
    try {
      setStatus(await api.status());
      setErr('');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'failed to load');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function renderRow(p: Problem) {
    const open = reviewing?.id === p.id;
    return (
      <li className="card" key={p.id}>
        <div className="card-head">
          <div>
            <a className="title" href={p.url} target="_blank" rel="noreferrer">
              {p.title || p.slug}
            </a>
            {p.title && <div className="slug">{p.slug}</div>}
            <div className="meta">
              <ProblemBadges p={p} />
              <span className="due">due {p.next_review}</span>
            </div>
          </div>
          {isOwner && !open && (
            <button className="primary" onClick={() => setReviewing(p)}>
              Review
            </button>
          )}
        </div>
        {open && (
          <ReviewForm
            p={p}
            onDone={() => {
              setReviewing(null);
              void load();
            }}
            onCancel={() => setReviewing(null)}
          />
        )}
      </li>
    );
  }

  return (
    <div>
      <h1>Review</h1>
      {err && <p className="error">{err}</p>}
      {status && (
        <p className="sub">
          {status.total_due} due · {status.total_upcoming} upcoming · {status.total} total
        </p>
      )}
      {status && (
        <>
          <section>
            <h2>Due</h2>
            {status.due.length === 0 ? (
              <p className="empty">Nothing due — nice.</p>
            ) : (
              <ul className="cards">{status.due.map(renderRow)}</ul>
            )}
          </section>
          <section>
            <h2>Upcoming tomorrow</h2>
            {status.upcoming.length === 0 ? (
              <p className="empty">Nothing due tomorrow.</p>
            ) : (
              <ul className="cards">{status.upcoming.map(renderRow)}</ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
