import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

export default function ComplexityChart({ data }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);
  const xAxisRef = useRef(null);
  const currentlyHoveredRef = useRef(null);
  const circleTemplateRef = useRef(null);

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
        paddingBottom: 50,
        paddingTop: 40,
        paddingLeft: 0,
        paddingRight: 0,
      })
    );

    const xRenderer = am5xy.AxisRendererX.new(root, {
      minorGridEnabled: true,
      minGridDistance: 60,
    });
    xRenderer.grid.template.set('visible', false);

    const xAxis = chart.xAxes.push(
      am5xy.CategoryAxis.new(root, {
        paddingTop: 40,
        categoryField: 'unidade',
        renderer: xRenderer,
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
      maxWidth: 100,
    });

    const yRenderer = am5xy.AxisRendererY.new(root, {});
    yRenderer.grid.template.set('strokeDasharray', [3]);

    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        min: 0,
        renderer: yRenderer,
      })
    );

    yAxis.get('renderer').labels.template.setAll({
      fontSize: 11,
      fill: am5.color(0x5a4f4c),
    });

    const series = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: 'Escalados',
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: 'count',
        categoryXField: 'unidade',
        sequencedInterpolation: true,
        calculateAggregates: true,
        maskBullets: false,
        tooltip: am5.Tooltip.new(root, {
          dy: -30,
          pointerOrientation: 'vertical',
          labelText: '{categoryX}: {valueY} escalados',
        }),
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      strokeOpacity: 0,
      cornerRadiusBR: 10,
      cornerRadiusTR: 10,
      cornerRadiusBL: 10,
      cornerRadiusTL: 10,
      maxWidth: 50,
      fillOpacity: 0.8,
    });

    function handleHover(dataItem) {
      if (dataItem && currentlyHoveredRef.current !== dataItem) {
        handleOut();
        currentlyHoveredRef.current = dataItem;
        const bullet = dataItem.bullets?.[0];
        if (bullet) {
          bullet.animate({
            key: 'locationY',
            to: 1,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
          });
        }
      }
    }

    function handleOut() {
      if (currentlyHoveredRef.current) {
        const bullet = currentlyHoveredRef.current.bullets?.[0];
        if (bullet) {
          bullet.animate({
            key: 'locationY',
            to: 0,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
          });
        }
        currentlyHoveredRef.current = null;
      }
    }

    series.columns.template.events.on('pointerover', function (e) {
      handleHover(e.target.dataItem);
    });

    series.columns.template.events.on('pointerout', function () {
      handleOut();
    });

    const circleTemplate = am5.Template.new({});
    circleTemplateRef.current = circleTemplate;

    series.bullets.push(function (root) {
      const bulletContainer = am5.Container.new(root, {});

      bulletContainer.children.push(
        am5.Circle.new(root, { radius: 28 }, circleTemplate)
      );

      const maskCircle = bulletContainer.children.push(
        am5.Circle.new(root, { radius: 22 })
      );

      const imageContainer = bulletContainer.children.push(
        am5.Container.new(root, { mask: maskCircle })
      );

      imageContainer.children.push(
        am5.Circle.new(root, {
          radius: 22,
          fill: am5.color(0xffffff),
          fillOpacity: 0.9,
        })
      );

      const label = bulletContainer.children.push(
        am5.Label.new(root, {
          text: '{valueY}',
          fill: am5.color(0x772B21),
          fontSize: 14,
          fontWeight: '700',
          centerX: am5.p50,
          centerY: am5.p50,
          populateText: true,
        })
      );

      return am5.Bullet.new(root, {
        locationY: 0,
        sprite: bulletContainer,
      });
    });

    series.set('heatRules', [
      {
        dataField: 'valueY',
        min: am5.color(0xfbbf24),
        max: am5.color(0xAC3631),
        target: series.columns.template,
        key: 'fill',
      },
      {
        dataField: 'valueY',
        min: am5.color(0xfbbf24),
        max: am5.color(0xAC3631),
        target: circleTemplate,
        key: 'fill',
      },
    ]);

    const cursor = chart.set('cursor', am5xy.XYCursor.new(root, {}));
    cursor.lineX.set('visible', false);
    cursor.lineY.set('visible', false);

    cursor.events.on('cursormoved', function () {
      const dataItem = series.get('tooltip')?.dataItem;
      if (dataItem) {
        handleHover(dataItem);
      } else {
        handleOut();
      }
    });

    series.appear();
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !xAxisRef.current || !data) return;

    const sortedData = [...data]
      .filter((d) => d.unidade && d.count > 0)
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
      <div ref={chartRef} style={{ width: '100%', height: '380px' }} />
    </div>
  );
}
