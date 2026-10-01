import type { Problem } from '../types';
import { familiarityLabel, importanceLabel } from '../types';

export default function ProblemBadges({ p }: { p: Problem }) {
  return (
    <span className="badges">
      <span className="badge">{familiarityLabel(p.familiarity)}</span>
      <span className="badge badge-imp">{importanceLabel(p.importance)}</span>
      <span className="badge badge-muted">EF {p.ease_factor.toFixed(2)}</span>
      <span className="badge badge-muted">{p.review_count}×</span>
    </span>
  );
}
