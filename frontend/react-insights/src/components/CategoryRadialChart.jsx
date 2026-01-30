import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import * as am5radar from '@amcharts/amcharts5/radar';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

const COLORS = [
  0x772B21,
  0x10b981,
  0xf59e0b,
  0x6b8e23,
  0xdc7f37,
  0x8b4513,
  0x3b82f6,
  0x8b5cf6,
  0xAC3631,
  0x381811,
  0xCFE3DA,
  0x5a4f4c,
];

export default function CategoryRadialChart({ title, data, tooltip }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);
  const xAxisRef = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5radar.RadarChart.new(root, {
        panX: false,
        panY: false,
        wheelX: 'none',
        wheelY: 'none',
        startAngle: -84,
        endAngle: 264,
        innerRadius: am5.percent(35),
        paddingTop: 20,
        paddingBottom: 20,
      })
    );

    const xRenderer = am5radar.AxisRendererCircular.new(root, {
      minGridDistance: 30,
    });
    xRenderer.grid.template.set('forceHidden', true);
    xRenderer.labels.template.setAll({
      fontSize: 11,
      fontWeight: '500',
      fill: am5.color(0x666666),
      textType: 'adjusted',
      radius: 10,
    });

    const xAxis = chart.xAxes.push(
      am5xy.CategoryAxis.new(root, {
        maxDeviation: 0,
        categoryField: 'category',
        renderer: xRenderer,
      })
    );
    xAxisRef.current = xAxis;

    const yRenderer = am5radar.AxisRendererRadial.new(root, {
      minGridDistance: 30,
    });
    yRenderer.labels.template.setAll({
      centerX: am5.p50,
      fontSize: 10,
      fill: am5.color(0x999999),
    });
    yRenderer.grid.template.setAll({
      stroke: am5.color(0xe5e5e5),
      strokeOpacity: 0.5,
    });

    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        maxDeviation: 0.3,
        min: 0,
        renderer: yRenderer,
      })
    );

    const series = chart.series.push(
      am5radar.RadarColumnSeries.new(root, {
        name: 'Categorias',
        sequencedInterpolation: true,
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: 'value',
        categoryXField: 'category',
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      cornerRadius: 5,
      tooltipText: '{categoryX}: {valueY} interações',
      strokeOpacity: 0,
      fillOpacity: 0.9,
      width: am5.percent(80),
    });

    series.columns.template.adapters.add('fill', function (fill, target) {
      const dataItem = target.dataItem;
      if (dataItem) {
        const ctx = dataItem.dataContext;
        if (ctx && ctx.colorIndex !== undefined) {
          return am5.color(COLORS[ctx.colorIndex % COLORS.length]);
        }
      }
      return am5.color(0x772B21);
    });

    series.columns.template.adapters.add('stroke', function (stroke, target) {
      const dataItem = target.dataItem;
      if (dataItem) {
        const ctx = dataItem.dataContext;
        if (ctx && ctx.colorIndex !== undefined) {
          return am5.color(COLORS[ctx.colorIndex % COLORS.length]);
        }
      }
      return am5.color(0x772B21);
    });

    series.columns.template.states.create('hover', {
      fillOpacity: 1,
      scale: 1.05,
    });

    const cursor = chart.set('cursor', am5radar.RadarCursor.new(root, {
      behavior: 'none',
    }));
    cursor.lineX.set('forceHidden', true);
    cursor.lineY.set('forceHidden', true);

    series.appear(1000);
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !xAxisRef.current || !data || data.length === 0) return;

    const chartData = data
      .filter((item) => (item.value || item.count || 0) > 0)
      .map((item, index) => ({
        category: item.label || item.category || 'Sem categoria',
        value: item.value || item.count || 0,
        colorIndex: index,
      }));

    xAxisRef.current.data.setAll(chartData);
    seriesRef.current.data.setAll(chartData);
  }, [data]);

  const total = data?.reduce((sum, item) => sum + (item.value || item.count || 0), 0) || 0;

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          {tooltip && (
            <div className="ml-2 relative group">
              <svg className="w-4 h-4 text-muted cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 w-64 text-center">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <div className="text-sm text-muted">
          Total: <span className="font-semibold text-foreground">{total}</span>
        </div>
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '420px' }} />
    </div>
  );
}
