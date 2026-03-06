/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 解决 Element Plus 类型问题
declare module 'element-plus/dist/locale/zh-cn.mjs' {
  const locale: any
  export default locale
}

declare module 'element-plus/es/locale/lang/zh-cn' {
  const locale: any
  export default locale
}

declare module 'element-plus/lib/locale/lang/zh-cn' {
  const locale: any
  export default locale
}