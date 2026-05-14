import { defineConfig, type Plugin } from 'vitepress'
import * as path from 'node:path'
import { collectAll } from './utils/collect-artifacts'

const ROOT = path.resolve(__dirname, '../..')

function hmrCollectPlugin(): Plugin {
  const watchPaths = [
    path.resolve(ROOT, 'notes'),
    path.resolve(ROOT, '01-superpowers/docs'),
    path.resolve(ROOT, '02-speckit/specs/001-agent-status-management'),
    path.resolve(ROOT, '03-openspec/openspec/changes/archive'),
    path.resolve(ROOT, 'CONTRIBUTING.md'),
    path.resolve(ROOT, 'docs/HOW-TO-REPLICATE.md'),
  ]
  return {
    name: 'hmr-collect-artifacts',
    configureServer(server) {
      watchPaths.forEach((p) => server.watcher.add(p))
      server.watcher.on('all', (event, file) => {
        if (event !== 'change' && event !== 'add' && event !== 'unlink') return
        if (!/\.(md|png|jpe?g|svg|gif|webp)$/i.test(file)) return
        if (!watchPaths.some((wp) => file.startsWith(wp))) return
        console.log(`[hmr-collect] ${event} ${path.relative(ROOT, file)} → re-collecting...`)
        try {
          collectAll()
        } catch (e) {
          console.error('[hmr-collect] failed:', e)
        }
      })
    },
  }
}

export default defineConfig({
  base: '/experiment-ai-sdd-tools/',
  lang: 'zh-CN',
  title: 'AI 编程 SDD 工具实战对比',
  description: '同一个需求、同一份基础项目，用 Superpowers / Spec-Kit / OpenSpec 各跑一遍的体验笔记',

  ignoreDeadLinks: true,

  head: [['meta', { name: 'theme-color', content: '#ea580c' }]],

  markdown: {
    lineNumbers: true,
  },

  vite: {
    plugins: [hmrCollectPlugin()],
  },

  themeConfig: {
    outline: { level: [2, 3], label: '本页目录' },

    nav: [
      { text: '速览', link: '/overview/' },
      { text: '对比', link: '/compare/' },
      {
        text: '各轮深记',
        items: [
          { text: 'Round 1: Superpowers', link: '/rounds/r1/' },
          { text: 'Round 2: Spec-Kit', link: '/rounds/r2/' },
          { text: 'Round 3: OpenSpec', link: '/rounds/r3/' },
        ],
      },
      { text: '复现', link: '/replicate/' },
      { text: '贡献', link: '/contribute/' },
      { text: 'GitHub', link: 'https://github.com/wwwweeia/experiment-ai-sdd-tools' },
    ],

    sidebar: {
      '/overview/': [
        {
          text: '速览',
          items: [
            { text: '30 秒看懂', link: '/overview/' },
            { text: '我该选哪个？', link: '/overview/selection' },
            { text: '如何阅读本报告（N=1 声明）', link: '/overview/disclaimer' },
          ],
        },
      ],
      '/compare/': [
        {
          text: '横向对比',
          items: [
            { text: '1. 概览', link: '/compare/' },
            { text: '2. 状态机实现', link: '/compare/state-machine' },
            { text: '3. 代码模式（错误处理 / 加载 / 模型 / Schema / 前端）', link: '/compare/code-patterns' },
            { text: '4. 任务分解与设计文档', link: '/compare/workflow' },
            { text: '5. 自主决策质量', link: '/compare/autonomy' },
            { text: '6. Token 效率', link: '/compare/token-efficiency' },
            { text: '7. 综合评价与启发', link: '/compare/synthesis' },
          ],
        },
      ],
      '/rounds/': [
        {
          text: '各轮深记',
          items: [
            { text: '入口', link: '/rounds/' },
            { text: 'Round 1: Superpowers', link: '/rounds/r1/' },
            { text: 'Round 2: Spec-Kit', link: '/rounds/r2/' },
            { text: 'Round 3: OpenSpec', link: '/rounds/r3/' },
          ],
        },
      ],
      '/rounds/r1/': [
        {
          text: 'Round 1: Superpowers',
          items: [
            { text: '观察笔记（人评）', link: '/rounds/r1/' },
            { text: 'AI 自我观察笔记', link: '/rounds/r1/ai-observation' },
            { text: '过程截图', link: '/rounds/r1/gallery' },
          ],
        },
        {
          text: '工具制品',
          items: [
            { text: '设计文档', link: '/rounds/r1/artifacts/design' },
            { text: '实施计划', link: '/rounds/r1/artifacts/plan' },
          ],
        },
      ],
      '/rounds/r2/': [
        {
          text: 'Round 2: Spec-Kit',
          items: [
            { text: '观察笔记（人评）', link: '/rounds/r2/' },
            { text: 'AI 自我观察笔记', link: '/rounds/r2/ai-observation' },
            { text: '过程截图', link: '/rounds/r2/gallery' },
          ],
        },
        {
          text: '工具制品',
          items: [
            { text: 'Spec', link: '/rounds/r2/artifacts/spec' },
            { text: 'Plan', link: '/rounds/r2/artifacts/plan' },
            { text: 'Tasks', link: '/rounds/r2/artifacts/tasks' },
            { text: 'Data Model', link: '/rounds/r2/artifacts/data-model' },
            { text: 'Research', link: '/rounds/r2/artifacts/research' },
            { text: 'Quickstart', link: '/rounds/r2/artifacts/quickstart' },
            { text: 'API 契约', link: '/rounds/r2/artifacts/contracts/agents-api' },
            { text: '需求 Checklist', link: '/rounds/r2/artifacts/checklists/requirements' },
          ],
        },
      ],
      '/rounds/r3/': [
        {
          text: 'Round 3: OpenSpec',
          items: [
            { text: '观察笔记（人评）', link: '/rounds/r3/' },
            { text: 'AI 自我观察笔记', link: '/rounds/r3/ai-observation' },
            { text: '过程截图', link: '/rounds/r3/gallery' },
          ],
        },
        {
          text: '工具制品',
          items: [
            { text: 'Proposal', link: '/rounds/r3/artifacts/proposal' },
            { text: 'Design', link: '/rounds/r3/artifacts/design' },
            { text: 'Tasks', link: '/rounds/r3/artifacts/tasks' },
            { text: 'Spec: agent-crud', link: '/rounds/r3/artifacts/specs/agent-crud/spec' },
            { text: 'Spec: agent-management-ui', link: '/rounds/r3/artifacts/specs/agent-management-ui/spec' },
            { text: 'Spec: agent-status-management', link: '/rounds/r3/artifacts/specs/agent-status-management/spec' },
          ],
        },
      ],
      '/replicate/': [
        {
          text: '复现实验',
          items: [{ text: '完整指南', link: '/replicate/' }],
        },
      ],
      '/contribute/': [
        {
          text: '贡献',
          items: [{ text: '贡献指南', link: '/contribute/' }],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/wwwweeia/experiment-ai-sdd-tools' },
    ],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档', buttonAriaLabel: '搜索文档' },
          modal: {
            displayDetails: '显示详情',
            resetButtonTitle: '清除搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '没有结果',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },

    editLink: {
      pattern:
        'https://github.com/wwwweeia/experiment-ai-sdd-tools/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页',
    },

    lastUpdated: { text: '最后更新于' },
    docFooter: { prev: '上一页', next: '下一页' },

    footer: {
      message:
        'MIT License · 数据出自 N=1 实验，结论仅供参考',
      copyright: '© 2026 wwwweeia',
    },
  },
})
