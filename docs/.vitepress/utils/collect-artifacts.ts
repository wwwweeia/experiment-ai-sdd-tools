/**
 * collect-artifacts: 把分散在仓库各处的 markdown 和图片，复制进 docs/ 内部
 * 并改写图片引用路径。原始文件零改动。
 *
 * 由 npm run docs:collect / docs:dev / docs:build 触发。
 * dev 模式下由 hmrCollectPlugin 在源文件变更时自动再跑。
 */

import * as fs from 'node:fs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const ROOT = path.resolve(__dirname, '../../..')
const DOCS = path.resolve(__dirname, '../..')

interface MdRule {
  /** 源路径，相对仓库根 */
  source: string
  /** 目标路径，相对 docs/ */
  target: string
  /** 改写后图片引用走的 URL 前缀（如 /screenshots/r1/）；不填则不改写 */
  imagePrefix?: string
}

interface ImageRule {
  /** 源目录，相对仓库根 */
  source: string
  /** 目标目录，相对 docs/ */
  target: string
}

interface GalleryRule {
  round: 'r1' | 'r2' | 'r3' | 'r4'
  imagesDir: string
  target: string
  title: string
}

const MD_RULES: MdRule[] = [
  // ── Round 1: Superpowers ──
  {
    source: 'notes/round1-superpowers.md',
    target: 'rounds/r1/index.md',
    imagePrefix: '/screenshots/r1/',
  },
  {
    source: '01-superpowers/docs/experiments/round-1-superpowers-observation.md',
    target: 'rounds/r1/ai-observation.md',
    imagePrefix: '/screenshots/r1/',
  },
  {
    source: '01-superpowers/docs/superpowers/specs/2026-05-13-agent-status-management-design.md',
    target: 'rounds/r1/artifacts/design.md',
    imagePrefix: '/screenshots/r1/',
  },
  {
    source: '01-superpowers/docs/superpowers/plans/2026-05-13-agent-status-management.md',
    target: 'rounds/r1/artifacts/plan.md',
    imagePrefix: '/screenshots/r1/',
  },

  // ── Round 2: Spec-Kit ──
  {
    source: 'notes/round2-speckit.md',
    target: 'rounds/r2/index.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/experiment-observation.md',
    target: 'rounds/r2/ai-observation.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/spec.md',
    target: 'rounds/r2/artifacts/spec.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/plan.md',
    target: 'rounds/r2/artifacts/plan.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/tasks.md',
    target: 'rounds/r2/artifacts/tasks.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/data-model.md',
    target: 'rounds/r2/artifacts/data-model.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/research.md',
    target: 'rounds/r2/artifacts/research.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/quickstart.md',
    target: 'rounds/r2/artifacts/quickstart.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/contracts/agents-api.md',
    target: 'rounds/r2/artifacts/contracts/agents-api.md',
    imagePrefix: '/screenshots/r2/',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/checklists/requirements.md',
    target: 'rounds/r2/artifacts/checklists/requirements.md',
    imagePrefix: '/screenshots/r2/',
  },

  // ── Round 3: OpenSpec ──
  {
    source: 'notes/round3-openspec.md',
    target: 'rounds/r3/index.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/observation-notes.md',
    target: 'rounds/r3/ai-observation.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/proposal.md',
    target: 'rounds/r3/artifacts/proposal.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/design.md',
    target: 'rounds/r3/artifacts/design.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/tasks.md',
    target: 'rounds/r3/artifacts/tasks.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/specs/agent-crud/spec.md',
    target: 'rounds/r3/artifacts/specs/agent-crud/spec.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/specs/agent-management-ui/spec.md',
    target: 'rounds/r3/artifacts/specs/agent-management-ui/spec.md',
    imagePrefix: '/screenshots/r3/',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/specs/agent-status-management/spec.md',
    target: 'rounds/r3/artifacts/specs/agent-status-management/spec.md',
    imagePrefix: '/screenshots/r3/',
  },

  // ── Round 4: GSD ──
  {
    source: 'notes/round4-gsd.md',
    target: 'rounds/r4/index.md',
  },
  {
    source: '04-get-shit-done/.planning/PROJECT.md',
    target: 'rounds/r4/artifacts/project.md',
  },
  {
    source: '04-get-shit-done/.planning/REQUIREMENTS.md',
    target: 'rounds/r4/artifacts/requirements.md',
  },
  {
    source: '04-get-shit-done/.planning/ROADMAP.md',
    target: 'rounds/r4/artifacts/roadmap.md',
  },
  {
    source: '04-get-shit-done/.planning/phases/01-backend/01-RESEARCH.md',
    target: 'rounds/r4/artifacts/phase1-research.md',
  },
  {
    source: '04-get-shit-done/.planning/phases/01-backend/01-VERIFICATION.md',
    target: 'rounds/r4/artifacts/phase1-verification.md',
  },
  {
    source: '04-get-shit-done/.planning/phases/02-frontend/02-UI-SPEC.md',
    target: 'rounds/r4/artifacts/phase2-ui-spec.md',
  },
  {
    source: '04-get-shit-done/.planning/phases/02-frontend/02-VERIFICATION.md',
    target: 'rounds/r4/artifacts/phase2-verification.md',
  },

  // ── 共享：复现 + 贡献 ──
  { source: 'docs/HOW-TO-REPLICATE.md', target: 'replicate/index.md' },
  { source: 'CONTRIBUTING.md', target: 'contribute/index.md' },
]

const IMAGE_RULES: ImageRule[] = [
  {
    source: '01-superpowers/docs/images',
    target: 'public/screenshots/r1',
  },
  {
    source: '02-speckit/specs/001-agent-status-management/images',
    target: 'public/screenshots/r2',
  },
  {
    source: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images',
    target: 'public/screenshots/r3',
  },
]

const GALLERY_RULES: GalleryRule[] = [
  {
    round: 'r1',
    imagesDir: '01-superpowers/docs/images',
    target: 'rounds/r1/gallery.md',
    title: 'Round 1: Superpowers 过程截图',
  },
  {
    round: 'r2',
    imagesDir: '02-speckit/specs/001-agent-status-management/images',
    target: 'rounds/r2/gallery.md',
    title: 'Round 2: Spec-Kit 过程截图',
  },
  {
    round: 'r3',
    imagesDir: '03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images',
    target: 'rounds/r3/gallery.md',
    title: 'Round 3: OpenSpec 过程截图',
  },
  {
    round: 'r4',
    imagesDir: '04-get-shit-done/.planning/phases',
    target: 'rounds/r4/gallery.md',
    title: 'Round 4: GSD 过程截图',
  },
]

/** 改写一段 markdown 中所有图片引用，让它们指向 /screenshots/rN/ 下的 basename */
function rewriteImageRefs(md: string, imagePrefix: string): string {
  // 匹配 ![alt](path) 和 <img src="path" />
  // path 形如 images/xxx.png、./images/xxx.png、../images/xxx.png、../../images/xxx.png 等
  const replaceOne = (orig: string): string => {
    // 只处理本地相对路径，跳过 http(s)://、绝对 / 开头、已经是 /screenshots/ 的
    if (/^(https?:|\/)/i.test(orig)) return orig
    // 仅处理图片扩展名
    if (!/\.(png|jpe?g|svg|gif|webp)(\?.*)?$/i.test(orig)) return orig
    const base = path.basename(orig.split(/[?#]/)[0])
    return imagePrefix + base
  }

  return md
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => `![${alt}](${replaceOne(src.trim())})`)
    .replace(/<img\b([^>]*?)\bsrc=(["'])([^"']+)\2/gi, (_, pre, q, src) => `<img${pre}src=${q}${replaceOne(src)}${q}`)
}

/** 复制单个 markdown 文件，按需改写图片引用 */
function collectMd(rule: MdRule) {
  const srcPath = path.resolve(ROOT, rule.source)
  const dstPath = path.resolve(DOCS, rule.target)
  if (!fs.existsSync(srcPath)) {
    console.warn(`[collect-md] SKIP missing source: ${rule.source}`)
    return
  }
  fs.mkdirSync(path.dirname(dstPath), { recursive: true })
  let content = fs.readFileSync(srcPath, 'utf8')
  if (rule.imagePrefix) {
    content = rewriteImageRefs(content, rule.imagePrefix)
  }
  // 在头部加一行来源标注（友好提示这是 collect 来的，不要直接改）
  const banner =
    `<!-- 此文件由 docs:collect 自动生成，源：${rule.source}。请编辑源文件而非本文件。 -->\n\n`
  fs.writeFileSync(dstPath, banner + content, 'utf8')
}

/** 递归复制目录（增量按 mtime 比对） */
function copyDirIncremental(src: string, dst: string) {
  if (!fs.existsSync(src)) return
  fs.mkdirSync(dst, { recursive: true })
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const sp = path.join(src, entry.name)
    const dp = path.join(dst, entry.name)
    if (entry.isDirectory()) {
      copyDirIncremental(sp, dp)
    } else {
      const ss = fs.statSync(sp)
      let needCopy = true
      if (fs.existsSync(dp)) {
        const ds = fs.statSync(dp)
        if (ss.size === ds.size && ss.mtimeMs <= ds.mtimeMs) {
          needCopy = false
        }
      }
      if (needCopy) {
        fs.copyFileSync(sp, dp)
      }
    }
  }
}

function collectImages(rule: ImageRule) {
  const src = path.resolve(ROOT, rule.source)
  const dst = path.resolve(DOCS, rule.target)
  if (!fs.existsSync(src)) {
    console.warn(`[collect-img] SKIP missing source: ${rule.source}`)
    return
  }
  copyDirIncremental(src, dst)
}

function generateGallery(rule: GalleryRule) {
  const src = path.resolve(ROOT, rule.imagesDir)
  const dst = path.resolve(DOCS, rule.target)
  if (!fs.existsSync(src)) {
    console.warn(`[gallery] SKIP missing source: ${rule.imagesDir}`)
    return
  }
  const files = fs
    .readdirSync(src)
    .filter((f) => /\.(png|jpe?g|svg|gif|webp)$/i.test(f))
    .sort()

  const lines: string[] = [
    `<!-- 此文件由 docs:collect 自动生成。 -->`,
    ``,
    `# ${rule.title}`,
    ``,
    `> 共 ${files.length} 张，按文件名顺序排列。点击图片可放大查看。`,
    ``,
    `> 说明：截图原始位置在 \`${rule.imagesDir}\`，文档站通过 collect 脚本复制到 \`/screenshots/${rule.round}/\` 下。`,
    ``,
  ]

  for (const f of files) {
    const alt = path.basename(f, path.extname(f))
    lines.push(`## ${alt}`, ``, `![${alt}](/screenshots/${rule.round}/${f})`, ``)
  }

  fs.mkdirSync(path.dirname(dst), { recursive: true })
  fs.writeFileSync(dst, lines.join('\n'), 'utf8')
}

export function collectAll() {
  const t0 = Date.now()
  let mdCount = 0
  let imgCount = 0
  for (const rule of MD_RULES) {
    collectMd(rule)
    mdCount++
  }
  for (const rule of IMAGE_RULES) {
    collectImages(rule)
    const dst = path.resolve(DOCS, rule.target)
    if (fs.existsSync(dst)) {
      imgCount += fs.readdirSync(dst).filter((f) => /\.(png|jpe?g|svg|gif|webp)$/i.test(f)).length
    }
  }
  for (const rule of GALLERY_RULES) {
    generateGallery(rule)
  }
  console.log(
    `[collect] ${mdCount} markdown + ${imgCount} images + ${GALLERY_RULES.length} galleries in ${Date.now() - t0}ms`,
  )
}

// CLI 入口
if (import.meta.url === `file://${process.argv[1]}`) {
  collectAll()
}
