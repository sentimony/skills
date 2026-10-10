import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer]);

interface Props {
  data: [number, number][]; // [timestamp, value]
}

export function TimeSeriesChart({ data }: Props) {
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'time' },
      yAxis: { type: 'value' },
      dataZoom: [{ type: 'inside' }],
      series: [{ type: 'line', showSymbol: false, data }],
    }),
    [data],
  );

  // Wrapper handles init/resize/dispose; option updates merge by default.
  return <ReactECharts echarts={echarts} option={option} style={{ height: 400 }} />;
}
