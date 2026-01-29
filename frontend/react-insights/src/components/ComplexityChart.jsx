import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import { getUnitName } from '../data/unitsData';
import InfoTooltip from './InfoTooltip';

export default function ComplexityChart({ data }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);
  const yAxisRef = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        paddingLeft: 0,
        paddingRight: 30,
        wheelX: 'none',
        wheelY: 'none',
      })
    );

    const yRenderer = am5xy.AxisRendererY.new(root, {
      minorGridEnabled: true,
      inversed: true,
    });
    yRenderer.grid.template.set('visible', false);

    const yAxis = chart.yAxes.push(
      am5xy.CategoryAxis.new(root, {
        categoryField: 'name',
        renderer: yRenderer,
        paddingRight: 40,
      })
    );
    yAxisRef.current = yAxis;

    const xRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 80,
      minorGridEnabled: true,
    });

    const xAxis = chart.xAxes.push(
      am5xy.ValueAxis.new(root, {
        min: 0,
        renderer: xRenderer,
      })
    );

    const series = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: 'Chamados',
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: 'count',
        categoryYField: 'name',
        sequencedInterpolation: true,
        calculateAggregates: true,
        tooltip: am5.Tooltip.new(root, {
          labelText: '{name}: {valueX} chamados',
        }),
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      strokeOpacity: 0,
      cornerRadiusBR: 6,
      cornerRadiusTR: 6,
      cornerRadiusBL: 6,
      cornerRadiusTL: 6,
      maxHeight: 28,
      fillOpacity: 0.9,
    });

    series.set('heatRules', [
      {
        dataField: 'valueX',
        min: am5.color(0xfbbf24),
        max: am5.color(0xdc2626),
        target: series.columns.template,
        key: 'fill',
      },
    ]);

    const cursor = chart.set('cursor', am5xy.XYCursor.new(root, {}));
    cursor.lineX.set('visible', false);
    cursor.lineY.set('visible', false);

    series.appear();
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !yAxisRef.current || !data) return;

    const chartData = data.slice(0, 10).map((item) => ({
      name: getUnitName(item.unidade) || item.unidade,
      count: item.count,
    }));

    yAxisRef.current.data.setAll(chartData);
    seriesRef.current.data.setAll(chartData);
  }, [data]);

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <div className="flex items-center mb-4">
        <h3 className="text-base font-semibold text-foreground">Mapa de Complexidade</h3>
        <InfoTooltip text="Volume de chamados escalados para humanos por unidade. Indica onde estao as maiores dificuldades ou duvidas nao resolvidas pela IA." />
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '350px' }} />
    </div>
  );
}
