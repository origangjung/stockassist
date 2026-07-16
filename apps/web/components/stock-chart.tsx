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

export function StockChart({ candles }: { candles: MarketCandle[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 430,
      layout: { background: { type: ColorType.Solid, color: "#0b1525" }, textColor: "#8fa0b7" },
      grid: { vertLines: { color: "#15243a" }, horzLines: { color: "#15243a" } },
      rightPriceScale: { borderColor: "#283a54", scaleMargins: { top: 0.08, bottom: 0.25 } },
      timeScale: { borderColor: "#283a54", timeVisible: false },
      crosshair: { vertLine: { color: "#557aa6" }, horzLine: { color: "#557aa6" } },
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#27d6a1",
      downColor: "#ff5c75",
      wickUpColor: "#27d6a1",
      wickDownColor: "#ff5c75",
      borderVisible: false,
    });
    const ma5Series = chart.addSeries(LineSeries, {
      color: "#72b8ff",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: "MA 5",
    });
    const ma20Series = chart.addSeries(LineSeries, {
      color: "#f3cb66",
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
      <div ref={containerRef} className="chart-canvas" aria-label="종목 캔들, 이동평균 및 거래량 차트" />
    </div>
  );
}
