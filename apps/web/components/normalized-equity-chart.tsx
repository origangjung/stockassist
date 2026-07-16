export interface NormalizedEquityPoint {
  timestamp: string;
  normalized_equity: number;
  drawdown: number;
}

export interface EquitySeries {
  name: string;
  color: string;
  points: NormalizedEquityPoint[];
}

interface NormalizedEquityChartProps {
  title: string;
  ariaLabel: string;
  series: EquitySeries[];
  footerNote?: string;
}

export function NormalizedEquityChart({
  title,
  ariaLabel,
  series,
  footerNote,
}: NormalizedEquityChartProps) {
  const activeSeries = series.filter((item) => item.points.length > 0);
  if (activeSeries.length === 0) return null;

  const values = [
    100,
    ...activeSeries.flatMap((item) =>
      item.points.map((point) => point.normalized_equity),
    ),
  ];
  const rawMinimum = Math.min(...values);
  const rawMaximum = Math.max(...values);
  const padding = Math.max((rawMaximum - rawMinimum) * 0.08, 0.5);
  const minimum = rawMinimum - padding;
  const maximum = rawMaximum + padding;
  const width = 1000;
  const height = 280;
  const inset = 24;
  const baselineY =
    height - inset - ((100 - minimum) / (maximum - minimum)) * (height - inset * 2);

  const polyline = (points: NormalizedEquityPoint[]) =>
    points
      .map((point, index) => {
        const x = inset + (index / Math.max(points.length - 1, 1)) * (width - inset * 2);
        const y =
          height - inset -
          ((point.normalized_equity - minimum) / (maximum - minimum)) *
            (height - inset * 2);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(" ");

  const first = activeSeries[0].points;
  const maximumPointCount = Math.max(...activeSeries.map((item) => item.points.length));

  return (
    <article className="equity-comparison-chart">
      <header>
        <div><span>NORMALIZED EQUITY</span><h2>{title}</h2></div>
        <div className="comparison-legend">
          {activeSeries.map((item) => (
            <span key={item.name}><i style={{ backgroundColor: item.color }} />{item.name}</span>
          ))}
        </div>
      </header>
      <div className="equity-chart-frame">
        <span className="equity-axis maximum">{maximum.toFixed(1)}</span>
        <span className="equity-axis baseline" style={{ top: `${(baselineY / height) * 100}%` }}>100.0</span>
        <span className="equity-axis minimum">{minimum.toFixed(1)}</span>
        <svg aria-label={ariaLabel} preserveAspectRatio="none" role="img" viewBox={`0 0 ${width} ${height}`}>
          <line className="equity-grid-line" x1={inset} x2={width - inset} y1={baselineY} y2={baselineY} />
          {activeSeries.map((item) => (
            <polyline
              className="equity-line"
              key={item.name}
              points={polyline(item.points)}
              style={{ stroke: item.color }}
            />
          ))}
        </svg>
      </div>
      <footer>
        <span>{new Date(first[0].timestamp).toLocaleDateString("ko-KR")}</span>
        <span>{footerNote ?? `초기 자산 = 100 · 최대 ${maximumPointCount}개 표시점`}</span>
        <span>{new Date(first[first.length - 1].timestamp).toLocaleDateString("ko-KR")}</span>
      </footer>
    </article>
  );
}
