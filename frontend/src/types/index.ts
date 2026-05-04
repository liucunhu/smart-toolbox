/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

export interface Account {
  id: number
  platform: string
  username: string
  status: string
  health_score: number
}

export interface ContentTask {
  task_id: string
  topic: string
  script?: string
}
