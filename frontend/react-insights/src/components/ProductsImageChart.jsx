import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

const productIcons = {
  HGLG11: '/static/icons/fii-logistica.svg',
  XPML11: '/static/icons/fii-shopping.svg',
  KNRI11: '/static/icons/fii-corporate.svg',
  VISC11: '/static/icons/fii-shopping.svg',
  BTLG11: '/static/icons/fii-logistica.svg',
  MXRF11: '/static/icons/fii-papel.svg',
  DEFAULT: '/static/icons/fii-default.svg',
};

export default function ProductsImageChart({ data, title, tooltip }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);

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
        layout: root.verticalLayout,
      })
    );

    const colors = chart.get('colors');

    const xRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 30,
      minorGridEnabled: true,
    });

    xRenderer.grid.template.setAll({ location: 1 });
    xRenderer.labels.template.setAll({ paddingTop: 20 });

    const xAxis = chart.xAxes.push(
      am5xy.CategoryAxis.new(root, {
        categoryField: 'product',
        renderer: xRenderer,
        bullet: function (root, axis, dataItem) {
          return am5xy.AxisBullet.new(root, {
            location: 0.5,
            sprite: am5.Circle.new(root, {
              radius: 12,
              fill: dataItem.dataContext?.columnSettings?.fill || am5.color(0x772B21),
              centerY: am5.p50,
              centerX: am5.p50,
            }),
          });
        },
      })
    );

    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          strokeOpacity: 0.1,
        }),
      })
    );

    const series = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: 'count',
        categoryXField: 'product',
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      tooltipText: '{categoryX}: {valueY} mencoes',
      tooltipY: 0,
      strokeOpacity: 0,
      cornerRadiusTL: 6,
      cornerRadiusTR: 6,
      templateField: 'columnSettings',
    });

    series.appear();
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !data) return;

    const root = rootRef.current;
    const chart = root.container.children.getIndex(0);
    const colors = chart?.get('colors');

    const chartData = data.slice(0, 8).map((item, index) => ({
      product: item.label || item.product,
      count: item.value || item.count,
      columnSettings: { fill: colors?.next() || am5.color(0x772B21) },
    }));

    if (chart && chart.xAxes) {
      const xAxis = chart.xAxes.getIndex(0);
      if (xAxis) {
        xAxis.data.setAll(chartData);
      }
    }
    seriesRef.current.data.setAll(chartData);
  }, [data]);

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
      <div ref={chartRef} style={{ width: '100%', height: '300px' }} />
    </div>
  );
}
