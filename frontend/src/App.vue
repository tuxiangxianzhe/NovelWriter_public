<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import ProjectBar from '@/components/ProjectBar.vue'

const route = useRoute()
const mobileMenuOpen = ref(false)

const navLinks = [
  { to: '/', label: '创作工坊', icon: '✍️' },
  { to: '/config', label: '模型配置', icon: '⚙️' },
  { to: '/presets', label: '提示词方案', icon: '📋' },
  { to: '/styles', label: '文风与DNA', icon: '🎨' },
  { to: '/knowledge', label: '知识库', icon: '📚' },
  { to: '/consistency', label: '一致性检查', icon: '🔍' },
  { to: '/brainstorm', label: '创意讨论', icon: '💡' },
  { to: '/files', label: '文件管理', icon: '📁' },
  { to: '/logs', label: '运行日志', icon: '📜' },
  { to: '/reader', label: '小说阅读', icon: '📖' },
]
</script>

<template>
  <div class="min-h-screen flex flex-col" style="background-color: var(--color-parchment)">
    <!-- 顶部导航栏 -->
    <header
      class="sticky top-0 z-50 shadow-lg"
      style="background-color: var(--color-spine)"
    >
      <!-- 主导航行 -->
      <div class="flex items-center gap-4 px-4 py-3">
        <!-- Logo -->
        <div class="flex-shrink-0 flex items-center gap-2">
          <span class="text-xl">📖</span>
          <h1
            class="text-lg font-bold hidden sm:block"
            style="color: var(--color-gold)"
          >
            NovelWriter
          </h1>
        </div>

        <!-- 桌面导航链接 -->
        <nav class="hidden lg:flex items-center gap-1 flex-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="px-3 py-1.5 rounded-md text-sm transition-colors whitespace-nowrap"
            :class="
              route.path === link.to
                ? 'bg-[var(--color-leather)] text-[var(--color-gold-light)] font-semibold'
                : 'text-[var(--color-parchment-dark)] hover:bg-[var(--color-spine-light)] hover:text-[var(--color-parchment)]'
            "
          >
            {{ link.label }}
          </router-link>
        </nav>

        <!-- 移动端汉堡菜单 -->
        <button
          class="lg:hidden ml-auto text-[var(--color-parchment)] p-1"
          @click="mobileMenuOpen = !mobileMenuOpen"
          type="button"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="mobileMenuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'"
            />
          </svg>
        </button>
      </div>

      <!-- 项目栏 -->
      <div
        class="px-4 py-2 border-t"
        style="border-color: var(--color-spine-light); background-color: var(--color-ink-light)"
      >
        <ProjectBar />
      </div>

      <!-- 移动端下拉菜单 -->
      <Transition name="slide">
        <nav
          v-if="mobileMenuOpen"
          class="lg:hidden border-t px-4 py-2 flex flex-col gap-1"
          style="border-color: var(--color-spine-light)"
        >
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors"
            :class="
              route.path === link.to
                ? 'bg-[var(--color-leather)] text-[var(--color-gold-light)] font-semibold'
                : 'text-[var(--color-parchment-dark)] hover:bg-[var(--color-spine-light)]'
            "
            @click="mobileMenuOpen = false"
          >
            <span>{{ link.icon }}</span>
            <span>{{ link.label }}</span>
          </router-link>
        </nav>
      </Transition>
    </header>

    <!-- 页面内容 -->
    <main class="flex-1 overflow-auto">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>

    <!-- 底部 -->
    <footer
      class="text-center text-xs py-2 border-t"
      style="
        background-color: var(--color-spine);
        color: var(--color-parchment-dark);
        border-color: var(--color-spine-light);
      "
    >
      NovelWriter 2.0 &nbsp;·&nbsp; FastAPI + Vue 3
    </footer>
  </div>
</template>
