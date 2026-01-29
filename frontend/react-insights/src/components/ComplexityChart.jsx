import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

export default function ComplexityChart({ data }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);
  const xAxisRef = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: 'none',
        wheelY: 'none',
        paddingLeft: 0,
        paddingRight: 20,
        paddingBottom: 10,
      })
    );

    const xAxis = chart.xAxes.push(
      am5xy.CategoryAxis.new(root, {
        categoryField: 'unidade',
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 30,
          cellStartLocation: 0.1,
          cellEndLocation: 0.9,
        }),
        tooltip: am5.Tooltip.new(root, {}),
      })
    );
    xAxisRef.current = xAxis;

    xAxis.get('renderer').labels.template.setAll({
      rotation: -35,
      centerY: am5.p50,
      centerX: am5.p100,
      paddingRight: 10,
      fontSize: 11,
      fill: am5.color(0x5a4f4c),
      oversizedBehavior: 'truncate',
      maxWidth: 120,
    });

    xAxis.get('renderer').grid.template.setAll({
      visible: false,
    });

    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        min: 0,
        renderer: am5xy.AxisRendererY.new(root, {
          strokeOpacity: 0.1,
        }),
      })
    );

    yAxis.get('renderer').labels.template.setAll({
      fontSize: 11,
      fill: am5.color(0x5a4f4c),
    });

    yAxis.get('renderer').grid.template.setAll({
      strokeOpacity: 0.1,
    });

    const series = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: 'count',
        categoryXField: 'unidade',
        tooltip: am5.Tooltip.new(root, {
          labelText: '{categoryX}: {valueY} escalados',
        }),
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      cornerRadiusTL: 6,
      cornerRadiusTR: 6,
      strokeOpacity: 0,
      fillOpacity: 0.9,
      width: am5.percent(70),
    });

    series.set('heatRules', [
      {
        dataField: 'valueY',
        min: am5.color(0xfbbf24),
        max: am5.color(0xAC3631),
        target: series.columns.template,
        key: 'fill',
      },
    ]);

    series.bullets.push(function () {
      return am5.Bullet.new(root, {
        locationY: 1,
        sprite: am5.Label.new(root, {
          text: '{valueY}',
          fill: am5.color(0x772B21),
          centerY: am5.p100,
          centerX: am5.p50,
          populateText: true,
          fontSize: 12,
          fontWeight: '600',
          dy: -5,
        }),
      });
    });

    series.appear(1000);
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !xAxisRef.current || !data) return;

    const sortedData = [...data]
      .filter(d => d.unidade && d.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    xAxisRef.current.data.setAll(sortedData);
    seriesRef.current.data.setAll(sortedData);
  }, [data]);

  const totalEscalados = data?.reduce((sum, d) => sum + (d.count || 0), 0) || 0;

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <h3 className="text-base font-semibold text-foreground">Mapa de Complexidade</h3>
          <div className="ml-2 relative group">
            <svg className="w-4 h-4 text-muted cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 w-64 text-center">
              Volume de conversas escaladas para atendimento humano por unidade. Indica areas que demandam mais suporte especializado.
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted">Total escalados:</span>
          <span className="font-semibold text-danger">{totalEscalados}</span>
        </div>
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '320px' }} />
    </div>
  );
}
