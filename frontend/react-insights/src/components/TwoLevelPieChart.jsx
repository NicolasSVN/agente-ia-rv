import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5percent from '@amcharts/amcharts5/percent';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

const COLORS = [
  0x772B21,
  0x10b981,
  0xf59e0b,
  0x6b8e23,
  0xdc7f37,
  0x8b4513,
  0x381811,
  0xAC3631,
  0x3b82f6,
  0x8b5cf6,
  0xCFE3DA,
  0x5a4f4c,
];

export default function TwoLevelPieChart({ title, data, tooltip }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const series0Ref = useRef(null);
  const series1Ref = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5percent.PieChart.new(root, {
        layout: root.verticalLayout,
      })
    );

    const series0 = chart.series.push(
      am5percent.PieSeries.new(root, {
        valueField: 'value',
        categoryField: 'category',
        alignLabels: false,
        radius: am5.percent(100),
        innerRadius: am5.percent(75),
      })
    );
    series0Ref.current = series0;

    series0.states.create('hidden', {
      startAngle: 180,
      endAngle: 180,
    });

    series0.slices.template.setAll({
      fillOpacity: 0.5,
      strokeOpacity: 0,
      templateField: 'settings',
      tooltipText: '{category}: {value}',
    });

    series0.slices.template.states.create('hover', { scale: 1.02 });
    series0.slices.template.states.create('active', { shiftRadius: 0 });

    series0.labels.template.setAll({
      forceHidden: true,
    });

    series0.ticks.template.setAll({
      forceHidden: true,
    });

    const series1 = chart.series.push(
      am5percent.PieSeries.new(root, {
        radius: am5.percent(70),
        innerRadius: am5.percent(55),
        valueField: 'value',
        categoryField: 'category',
        alignLabels: false,
      })
    );
    series1Ref.current = series1;

    series1.states.create('hidden', {
      startAngle: 180,
      endAngle: 180,
    });

    series1.slices.template.setAll({
      templateField: 'sliceSettings',
      strokeOpacity: 0,
      tooltipText: '{category}: {value}',
    });

    series1.labels.template.setAll({
      textType: 'circular',
      fontSize: 11,
      fill: am5.color(0x5a4f4c),
    });

    series1.labels.template.adapters.add('radius', function (radius, target) {
      const dataItem = target.dataItem;
      if (dataItem) {
        const slice = dataItem.get('slice');
        if (slice) {
          return -(slice.get('radius') - slice.get('innerRadius')) / 2 - 10;
        }
      }
      return radius;
    });

    series1.slices.template.states.create('hover', { scale: 1.05 });
    series1.slices.template.states.create('active', { shiftRadius: 0 });

    series1.ticks.template.setAll({
      forceHidden: true,
    });

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!series0Ref.current || !series1Ref.current || !data || data.length === 0) return;

    const innerData = data.map((item, index) => ({
      category: item.label || item.category,
      value: item.value || item.count,
      sliceSettings: { fill: am5.color(COLORS[index % COLORS.length]) },
    }));

    series1Ref.current.data.setAll(innerData);

    const total = data.reduce((sum, item) => sum + (item.value || item.count || 0), 0);
    const grouped = [];
    const topItems = data.slice(0, Math.min(3, data.length));
    const topTotal = topItems.reduce((sum, item) => sum + (item.value || item.count || 0), 0);

    topItems.forEach((item, index) => {
      grouped.push({
        category: item.label || item.category,
        value: item.value || item.count,
        settings: { fill: am5.color(COLORS[index % COLORS.length]) },
      });
    });

    if (data.length > 3) {
      const othersTotal = total - topTotal;
      grouped.push({
        category: 'Outros',
        value: othersTotal,
        settings: { fill: am5.color(0xdedede) },
      });
    }

    series0Ref.current.slices.template.adapters.add('fill', function (fill, target) {
      return target.dataItem?.dataContext?.settings?.fill || fill;
    });

    series0Ref.current.data.setAll(grouped);
  }, [data]);

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <div className="flex items-center mb-2">
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
      <div ref={chartRef} style={{ width: '100%', height: '320px' }} />
      {data && data.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 justify-center text-xs">
          {data.slice(0, 6).map((item, index) => (
            <div key={index} className="flex items-center gap-1.5">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{
                  backgroundColor: `#${COLORS[index % COLORS.length].toString(16).padStart(6, '0')}`,
                }}
              />
              <span className="text-muted truncate max-w-[100px]">{item.label || item.category}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
