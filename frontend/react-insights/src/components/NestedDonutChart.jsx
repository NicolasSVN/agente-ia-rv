import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5percent from '@amcharts/amcharts5/percent';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

export default function NestedDonutChart({ title, data, innerData, centerLabel, tooltip }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const series0Ref = useRef(null);
  const series1Ref = useRef(null);
  const labelRef = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5percent.PieChart.new(root, {
        startAngle: 160,
        endAngle: 380,
      })
    );

    const series0 = chart.series.push(
      am5percent.PieSeries.new(root, {
        valueField: 'value',
        categoryField: 'category',
        startAngle: 160,
        endAngle: 380,
        radius: am5.percent(60),
        innerRadius: am5.percent(40),
      })
    );
    series0Ref.current = series0;

    series0.slices.template.setAll({
      strokeWidth: 3,
      stroke: am5.color(0xffffff),
      tooltipText: '{category}: {value}',
    });

    series0.ticks.template.set('forceHidden', true);
    series0.labels.template.set('forceHidden', true);

    const series1 = chart.series.push(
      am5percent.PieSeries.new(root, {
        startAngle: 160,
        endAngle: 380,
        valueField: 'value',
        innerRadius: am5.percent(70),
        radius: am5.percent(95),
        categoryField: 'category',
      })
    );
    series1Ref.current = series1;

    series1.slices.template.setAll({
      strokeWidth: 3,
      stroke: am5.color(0xffffff),
      tooltipText: '{category}: {value}',
    });

    series1.ticks.template.set('forceHidden', true);
    series1.labels.template.set('forceHidden', true);

    const label = chart.seriesContainer.children.push(
      am5.Label.new(root, {
        textAlign: 'center',
        centerY: am5.p100,
        centerX: am5.p50,
        text: '',
        fontSize: 14,
        fontWeight: '600',
      })
    );
    labelRef.current = label;

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!series0Ref.current || !data) return;

    const colors = [
      am5.color(0x772B21),
      am5.color(0x10b981),
      am5.color(0xf59e0b),
      am5.color(0x6b8e23),
      am5.color(0xdc7f37),
      am5.color(0x8b4513),
      am5.color(0x381811),
      am5.color(0xAC3631),
      am5.color(0xCFE3DA),
      am5.color(0x5a4f4c),
      am5.color(0x3b82f6),
      am5.color(0x8b5cf6),
    ];

    const chartData = data.map((item, index) => ({
      category: item.label || item.category,
      value: item.value || item.count,
      sliceSettings: { fill: colors[index % colors.length] },
    }));

    series0Ref.current.slices.template.adapters.add('fill', function (fill, target) {
      return target.dataItem?.dataContext?.sliceSettings?.fill || fill;
    });

    series0Ref.current.data.setAll(chartData);

    if (innerData && series1Ref.current) {
      const innerChartData = innerData.map((item, index) => ({
        category: item.label || item.category,
        value: item.value || item.count,
        sliceSettings: { fill: colors[index % colors.length] },
      }));

      series1Ref.current.slices.template.adapters.add('fill', function (fill, target) {
        return target.dataItem?.dataContext?.sliceSettings?.fill || fill;
      });

      series1Ref.current.data.setAll(innerChartData);
    }

    if (centerLabel && labelRef.current) {
      labelRef.current.set('text', centerLabel);
    }
  }, [data, innerData, centerLabel]);

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <div className="flex items-center mb-4">
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
      <div ref={chartRef} style={{ width: '100%', height: '350px' }} />
      {data && (
        <div className="mt-3 flex flex-wrap gap-3 justify-center text-xs">
          {data.slice(0, 6).map((item, index) => (
            <div key={index} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: [
                    '#772B21', '#10b981', '#f59e0b', '#6b8e23', '#dc7f37', '#8b4513',
                  ][index % 6],
                }}
              />
              <span className="text-muted">{item.label || item.category}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
