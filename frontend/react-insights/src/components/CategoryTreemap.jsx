import { useLayoutEffect, useRef, useEffect } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5hierarchy from '@amcharts/amcharts5/hierarchy';
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

export default function CategoryTreemap({ title, data, tooltip }) {
  const chartRef = useRef(null);
  const rootRef = useRef(null);
  const seriesRef = useRef(null);

  useLayoutEffect(() => {
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const container = root.container.children.push(
      am5.Container.new(root, {
        width: am5.percent(100),
        height: am5.percent(100),
        layout: root.verticalLayout,
      })
    );

    const series = container.children.push(
      am5hierarchy.Treemap.new(root, {
        singleBranchOnly: false,
        downDepth: 1,
        upDepth: 0,
        initialDepth: 1,
        topDepth: 1,
        valueField: 'value',
        categoryField: 'name',
        childDataField: 'children',
        nodePaddingOuter: 4,
        nodePaddingInner: 4,
        nodePaddingTop: 4,
        nodePaddingBottom: 4,
        layoutAlgorithm: 'squarify',
      })
    );
    seriesRef.current = series;

    series.rectangles.template.setAll({
      strokeWidth: 3,
      stroke: am5.color(0xffffff),
      cornerRadiusTL: 10,
      cornerRadiusTR: 10,
      cornerRadiusBL: 10,
      cornerRadiusBR: 10,
      fillOpacity: 0.95,
    });

    series.rectangles.template.states.create('hover', {
      fillOpacity: 0.75,
      strokeWidth: 4,
    });

    series.labels.template.setAll({
      fontSize: 14,
      fontWeight: '600',
      fill: am5.color(0xffffff),
      oversizedBehavior: 'truncate',
      textAlign: 'center',
      centerX: am5.p50,
      centerY: am5.p50,
      paddingLeft: 5,
      paddingRight: 5,
    });

    series.rectangles.template.adapters.add('fill', function (fill, target) {
      const dataItem = target.dataItem;
      if (dataItem) {
        const ctx = dataItem.dataContext || dataItem.get('dataContext');
        if (ctx && ctx.name !== 'Root' && ctx.colorIndex !== undefined) {
          return am5.color(COLORS[ctx.colorIndex % COLORS.length]);
        }
        const depth = dataItem.get('depth');
        if (depth === 1) {
          const index = dataItem.get('index') || 0;
          return am5.color(COLORS[index % COLORS.length]);
        }
      }
      return am5.color(0x772B21);
    });

    series.set('tooltip', am5.Tooltip.new(root, {
      labelText: '{name}: {value}',
    }));

    return () => {
      root.dispose();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !data || data.length === 0) return;

    const children = data
      .filter((item) => (item.value || item.count || 0) > 0)
      .map((item, index) => ({
        name: item.label || item.category || 'Sem categoria',
        value: item.value || item.count || 0,
        colorIndex: index,
      }));

    const treeData = [{
      name: 'Root',
      value: 0,
      children: children,
    }];

    seriesRef.current.data.setAll(treeData);
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
      <div ref={chartRef} style={{ width: '100%', height: '320px' }} />
    </div>
  );
}
