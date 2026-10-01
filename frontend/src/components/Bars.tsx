export interface BarDatum {
  label: string;
  value: number;
}

export default function Bars({ data, height = 140 }: { data: BarDatum[]; height?: number }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div className="bars" style={{ height }}>
      {data.map((d) => (
        <div className="bar-col" key={d.label + d.value}>
          <div className="bar-num">{d.value}</div>
          <div className="bar-track">
            <div className="bar-fill" style={{ height: `${(d.value / max) * 100}%` }} />
          </div>
          <div className="bar-label">{d.label}</div>
        </div>
      ))}
    </div>
  );
}
