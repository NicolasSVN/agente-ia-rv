import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import { getUnitName } from '../data/unitsData';

export default function UnitsBarChart({ data }) {
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
        paddingLeft: 0,
        paddingRight: 30,
        wheelX: 'none',
        wheelY: 'none',
      })
    );

    const yRenderer = am5xy.AxisRendererY.new(root, {
      minorGridEnabled: true,
    });
    yRenderer.grid.template.set('visible', false);

    const yAxis = chart.yAxes.push(
      am5xy.CategoryAxis.new(root, {
        categoryField: 'name',
        renderer: yRenderer,
        paddingRight: 40,
      })
    );

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
        name: 'Interacoes',
        xAxis: xAxis,
        yAxis: yAxis,
        valueXField: 'count',
        categoryYField: 'name',
        sequencedInterpolation: true,
        calculateAggregates: true,
        maskBullets: false,
        tooltip: am5.Tooltip.new(root, {
          dy: -30,
          pointerOrientation: 'vertical',
          labelText: '{name}: {valueX} interacoes',
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
      maxHeight: 40,
      fillOpacity: 0.8,
    });

    let currentlyHovered = null;

    series.columns.template.events.on('pointerover', function (e) {
      handleHover(e.target.dataItem);
    });

    series.columns.template.events.on('pointerout', function () {
      handleOut();
    });

    function handleHover(dataItem) {
      if (dataItem && currentlyHovered !== dataItem) {
        handleOut();
        currentlyHovered = dataItem;
        const bullet = dataItem.bullets?.[0];
        if (bullet) {
          bullet.animate({
            key: 'locationX',
            to: 1,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
          });
        }
      }
    }

    function handleOut() {
      if (currentlyHovered) {
        const bullet = currentlyHovered.bullets?.[0];
        if (bullet) {
          bullet.animate({
            key: 'locationX',
            to: 0,
            duration: 600,
            easing: am5.ease.out(am5.ease.cubic),
          });
        }
      }
    }

    const circleTemplate = am5.Template.new({});

    series.bullets.push(function (root) {
      const bulletContainer = am5.Container.new(root, {});

      bulletContainer.children.push(
        am5.Circle.new(root, { radius: 20 }, circleTemplate)
      );

      const maskCircle = bulletContainer.children.push(
        am5.Circle.new(root, { radius: 16 })
      );

      const imageContainer = bulletContainer.children.push(
        am5.Container.new(root, { mask: maskCircle })
      );

      imageContainer.children.push(
        am5.Label.new(root, {
          text: '',
          centerX: am5.p50,
          centerY: am5.p50,
          fontSize: 10,
          fontWeight: '700',
          fill: am5.color(0xffffff),
        })
      );

      return am5.Bullet.new(root, {
        locationX: 0,
        sprite: bulletContainer,
      });
    });

    series.set('heatRules', [
      {
        dataField: 'valueX',
        min: am5.color(0xCFE3DA),
        max: am5.color(0x772B21),
        target: series.columns.template,
        key: 'fill',
      },
      {
        dataField: 'valueX',
        min: am5.color(0xCFE3DA),
        max: am5.color(0x772B21),
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
    if (!seriesRef.current || !data) return;

    const chartData = data.slice(0, 10).map((item) => ({
      name: getUnitName(item.unidade) || item.unidade,
      count: item.count,
    }));

    const root = rootRef.current;
    const chart = root.container.children.getIndex(0);
    if (chart && chart.yAxes) {
      const yAxis = chart.yAxes.getIndex(0);
      if (yAxis) {
        yAxis.data.setAll(chartData);
      }
    }
    seriesRef.current.data.setAll(chartData);
  }, [data]);

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <h3 className="text-base font-semibold text-foreground mb-4">Top 10 Unidades</h3>
      <div ref={chartRef} style={{ width: '100%', height: '400px' }} />
    </div>
  );
}
