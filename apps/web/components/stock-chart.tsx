"use client";

import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { MarketCandle } from "../lib/market-api";

function movingAverage(candles: MarketCandle[], period: number): LineData<Time>[] {
  if (candles.length < period) return [];
  const output: LineData<Time>[] = [];
  let total = 0;
  for (let index = 0; index < candles.length; index += 1) {
    total += Number(candles[index].close);
    if (index >= period) total -= Number(candles[index - period].close);
    if (index >= period - 1) {
      output.push({
        time: candles[index].timestamp.slice(0, 10) as Time,
        value: total / period,
      });
    }
  }
  return output;
}

function chartDescription(candles: MarketCandle[]): string {
  const first = candles[0];
  const latest = candles.at(-1);
  if (!first || !latest) return "표시할 차트 데이터가 없습니다.";

  const startClose = Number(first.close);
  const latestClose = Number(latest.close);
  const change = startClose ? ((latestClose - startClose) / startClose) * 100 : null;
  const formattedLatest = Number.isFinite(latestClose)
    ? new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(latestClose)
    : latest.close;
  const changeText = change != null && Number.isFinite(change)
    ? `시작 대비 ${change >= 0 ? "+" : ""}${change.toFixed(2)}%`
    : "시작 대비 변동률을 계산할 수 없음";

  return `${first.timestamp.slice(0, 10)}부터 ${latest.timestamp.slice(0, 10)}까지 ${candles.length}개 캔들입니다. 최신 종가 ${formattedLatest}, ${changeText}. 이동평균 5·20과 거래량을 함께 표시합니다.`;
}

export function StockChart({ candles }: { candles: MarketCandle[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 430,
      layout: { background: { type: ColorType.Solid, color: "#15110f" }, textColor: "#b7a998" },
      grid: { vertLines: { color: "#2b231d" }, horzLines: { color: "#2b231d" } },
      rightPriceScale: { borderColor: "#46392d", scaleMargins: { top: 0.08, bottom: 0.25 } },
      timeScale: { borderColor: "#46392d", timeVisible: false },
      crosshair: { vertLine: { color: "#89684b" }, horzLine: { color: "#89684b" } },
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#27d6a1",
      downColor: "#ff5c75",
      wickUpColor: "#27d6a1",
      wickDownColor: "#ff5c75",
      borderVisible: false,
    });
    const ma5Series = chart.addSeries(LineSeries, {
      color: "#d59a5d",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: "MA 5",
    });
    const ma20Series = chart.addSeries(LineSeries, {
      color: "#9ec493",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: "MA 20",
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      priceLineVisible: false,
      lastValueVisible: false,
      title: "Volume",
    });
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    const candleData: CandlestickData<Time>[] = candles.map((candle) => ({
      time: candle.timestamp.slice(0, 10) as Time,
      open: Number(candle.open),
      high: Number(candle.high),
      low: Number(candle.low),
      close: Number(candle.close),
    }));
    const volumeData: HistogramData<Time>[] = candles.map((candle) => ({
      time: candle.timestamp.slice(0, 10) as Time,
      value: candle.volume,
      color: Number(candle.close) >= Number(candle.open) ? "#27d6a166" : "#ff5c7566",
    }));
    candleSeries.setData(candleData);
    ma5Series.setData(movingAverage(candles, 5));
    ma20Series.setData(movingAverage(candles, 20));
    volumeSeries.setData(volumeData);
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(([entry]) => {
      chart.applyOptions({ width: entry.contentRect.width });
    });
    observer.observe(container);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [candles]);

  return (
    <div className="chart-with-legend">
      <div className="chart-legend"><span className="ma5">MA 5</span><span className="ma20">MA 20</span><span className="volume">거래량</span></div>
      <div
        aria-label={chartDescription(candles)}
        className="chart-canvas"
        ref={containerRef}
        role="img"
      />
    </div>
  );
}
