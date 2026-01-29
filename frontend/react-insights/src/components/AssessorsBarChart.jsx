import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import InfoTooltip from './InfoTooltip';

export default function AssessorsBarChart({ data }) {
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
      cellStartLocation: 0.1,
      cellEndLocation: 0.9,
    });
    yRenderer.grid.template.set('visible', false);
    yRenderer.labels.template.setAll({
      fontSize: 12,
      paddingRight: 10,
    });

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
          labelText: '{name}\n{unidade}\n{valueX} interacoes',
        }),
      })
    );
    seriesRef.current = series;

    series.columns.template.setAll({
      strokeOpacity: 0,
      cornerRadiusBR: 8,
      cornerRadiusTR: 8,
      cornerRadiusBL: 8,
      cornerRadiusTL: 8,
      height: am5.percent(70),
      fillOpacity: 0.9,
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

    series.bullets.push(function (root, series, dataItem) {
      const bulletContainer = am5.Container.new(root, {});

      bulletContainer.children.push(
        am5.Circle.new(root, { radius: 16 }, circleTemplate)
      );

      const initials = (dataItem.dataContext.name || '')
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase();

      bulletContainer.children.push(
        am5.Label.new(root, {
          text: initials,
          centerX: am5.p50,
          centerY: am5.p50,
          fontSize: 9,
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
        min: am5.color(0x6ee7b7),
        max: am5.color(0x047857),
        target: series.columns.template,
        key: 'fill',
      },
      {
        dataField: 'valueX',
        min: am5.color(0x6ee7b7),
        max: am5.color(0x047857),
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
    if (!seriesRef.current || !yAxisRef.current || !data) return;

    const chartData = data.slice(0, 10).map((item) => ({
      name: item.nome || item.assessor_name,
      unidade: item.unidade || '',
      count: item.count,
    }));

    yAxisRef.current.data.setAll(chartData);
    seriesRef.current.data.setAll(chartData);
  }, [data]);

  return (
    <div className="bg-white rounded-xl border border-border p-5 shadow-card h-full">
      <div className="flex items-center mb-4">
        <h3 className="text-base font-semibold text-foreground">Top 10 Assessores por Engajamento</h3>
        <InfoTooltip text="Ranking de assessores com maior volume de interacoes com o agente IA no periodo selecionado." />
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '440px' }} />
    </div>
  );
}
