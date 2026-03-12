import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'workshop',
      component: () => import('@/views/WorkshopView.vue'),
      meta: { title: '创作工坊' },
    },
    {
      path: '/config',
      name: 'config',
      component: () => import('@/views/ConfigView.vue'),
      meta: { title: '模型配置' },
    },
    {
      path: '/presets',
      name: 'presets',
      component: () => import('@/views/PresetsView.vue'),
      meta: { title: '提示词方案' },
    },
    {
      path: '/styles',
      name: 'styles',
      component: () => import('@/views/StylesView.vue'),
      meta: { title: '文风与DNA' },
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: () => import('@/views/KnowledgeView.vue'),
      meta: { title: '知识库' },
    },
    {
      path: '/consistency',
      name: 'consistency',
      component: () => import('@/views/ConsistencyView.vue'),
      meta: { title: '一致性检查' },
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('@/views/FilesView.vue'),
      meta: { title: '文件管理' },
    },
    {
      path: '/reader',
      name: 'reader',
      component: () => import('@/views/ReaderView.vue'),
      meta: { title: '小说阅读' },
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('@/views/LogsView.vue'),
      meta: { title: '运行日志' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${to.meta.title ?? 'NovelWriter'} — NovelWriter`
})

export default router
