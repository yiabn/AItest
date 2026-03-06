declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 解决 Element Plus 图标类型问题
declare module '@element-plus/icons-vue' {
  import type { DefineComponent } from 'vue'
  const Icon: DefineComponent<{}, {}, any>
  export const Platform: DefineComponent<{}, {}, any>
  export const Medal: DefineComponent<{}, {}, any>
  export const MagicStick: DefineComponent<{}, {}, any>
  export const MapLocation: DefineComponent<{}, {}, any>
  export const TrendCharts: DefineComponent<{}, {}, any>
}