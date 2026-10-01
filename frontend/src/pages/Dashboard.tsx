import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Delta, Problem } from '../types';
import { FAMILIARITY_LABELS } from '../types';
import Bars from '../components/Bars';
import type { BarDatum } from '../components/Bars';

function isoDay(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function Dashboard() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [history, setHistory] = useState<Delta[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [ps, hs] = await Promise.all([api.problems(), api.history()]);
        setProblems(ps);
        setHistory(hs);
      } catch (e) {
        setErr(e instanceof Error ? e.message : 'failed to load');
      }
    })();
  }, []);

  if (err) return <p className="error">{err}</p>;

  const famCounts: BarDatum[] = FAMILIARITY_LABELS.map((label, i) => ({
    label,
    value: problems.filter((p) => p.familiarity === i).length,
  }));

  const today = new Date();
  const activity: BarDatum[] = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
    const key = isoDay(d);
    const value = history.filter(
      (h) => (h.action === 'add' || h.action === 'update') && h.created_at.slice(0, 10) === key,
    ).length;
    activity.push({ label: `${d.getMonth() + 1}/${d.getDate()}`, value });
  }

  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const dueOverTime: BarDatum[] = [];
  for (let i = 0; i < 30; i++) {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    const key = isoDay(d);
    const value = problems.filter((p) => p.next_review && p.next_review <= key).length;
    dueOverTime.push({ label: i % 7 === 0 || i === 29 ? `${i}d` : '', value });
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="dash-grid">
        <section className="card dash">
          <h2>Familiarity distribution</h2>
          <Bars data={famCounts} />
        </section>
        <section className="card dash">
          <h2>Review activity · last 14 days</h2>
          <Bars data={activity} />
        </section>
        <section className="card dash wide">
          <h2>Due over time · next 30 days</h2>
          <Bars data={dueOverTime} />
        </section>
      </div>
    </div>
  );
}
