<script setup lang="ts">
import { computed } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer]);

const props = defineProps<{
  data: [number, number][]; // [timestamp, value]
}>();

const option = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'time' },
  yAxis: { type: 'value' },
  dataZoom: [{ type: 'inside' }],
  series: [{ type: 'line', showSymbol: false, data: props.data }],
}));
</script>

<template>
  <!-- autoresize observes the container; parent must give it a height -->
  <VChart :option="option" autoresize style="height: 400px" />
</template>
