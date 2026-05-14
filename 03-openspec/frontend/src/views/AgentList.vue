<template>
  <div class="agent-list">
    <!-- 标题 + 创建按钮 -->
    <div class="toolbar">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">创建 Agent</el-button>
    </div>

    <!-- 状态筛选 -->
    <el-tabs v-model="activeTab" @tab-change="handleFilterChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="草稿" name="draft" />
      <el-tab-pane label="已激活" name="active" />
      <el-tab-pane label="已停用" name="inactive" />
    </el-tabs>

    <!-- 列表表格 -->
    <el-table v-loading="agentStore.loading" :data="agentStore.agents" style="width: 100%" empty-text="暂无数据">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model_name" label="关联 Model" min-width="120">
        <template #default="{ row }">
          <span>{{ row.model_name || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="prompt_name" label="关联 Prompt" min-width="120">
        <template #default="{ row }">
          <span>{{ row.prompt_name || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button type="success" size="small" @click="confirmActivate(row)">激活</el-button>
          </template>
          <template v-else-if="row.status === 'active'">
            <el-button type="warning" size="small" @click="confirmDeactivate(row)">停用</el-button>
          </template>
          <template v-else-if="row.status === 'inactive'">
            <el-button type="success" size="small" @click="confirmActivate(row)">激活</el-button>
            <el-button type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建 Agent 对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建 Agent" width="500px" destroy-on-close>
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="关联 Model">
          <el-select v-model="createForm.model_id" clearable placeholder="可选，激活前关联即可" style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联 Prompt">
          <el-select v-model="createForm.prompt_id" clearable placeholder="可选，激活前关联即可" style="width: 100%">
            <el-option v-for="p in promptOptions" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAgentStore } from '../stores/agent'
import api from '../api'

const agentStore = useAgentStore()
const activeTab = ref('')
const showCreateDialog = ref(false)
const submitting = ref(false)

const modelOptions = ref([])
const promptOptions = ref([])

const createForm = reactive({
  name: '',
  description: '',
  model_id: null,
  prompt_id: null,
})

function statusLabel(s) {
  return { draft: '草稿', active: '已激活', inactive: '已停用' }[s] || s
}

function statusTagType(s) {
  return { draft: 'info', active: 'success', inactive: 'warning' }[s] || 'info'
}

async function loadOptions() {
  try {
    const [models, prompts] = await Promise.all([
      api.get('/api/v1/models/'),
      api.get('/api/v1/prompts/'),
    ])
    modelOptions.value = models.data || []
    promptOptions.value = prompts.data || []
  } catch { /* 静默 */ }
}

function handleFilterChange(status) {
  agentStore.loadAgents(status)
}

async function handleCreate() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入 Agent 名称')
    return
  }
  submitting.value = true
  try {
    await agentStore.createAgent({ ...createForm })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    Object.assign(createForm, { name: '', description: '', model_id: null, prompt_id: null })
  } finally {
    submitting.value = false
  }
}

async function confirmActivate(agent) {
  try {
    await ElMessageBox.confirm(
      `确定激活 Agent「${agent.name}」？激活后 Agent 将变为可用状态。`,
      '激活确认',
      { type: 'info', confirmButtonText: '激活', cancelButtonText: '取消' },
    )
  } catch { return }
  try {
    await agentStore.changeStatus(agent.id, 'active', '手动激活')
    ElMessage.success('激活成功')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '激活失败'
    ElMessage.error(msg)
  }
}

async function confirmDeactivate(agent) {
  try {
    await ElMessageBox.confirm(
      `确定停用 Agent「${agent.name}」？停用后其关联的 Skill 将不可用。`,
      '停用确认',
      { type: 'warning', confirmButtonText: '停用', cancelButtonText: '取消' },
    )
  } catch { return }
  try {
    await agentStore.changeStatus(agent.id, 'inactive', '手动停用')
    ElMessage.success('停用成功')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '停用失败')
  }
}

async function confirmDelete(agent) {
  try {
    await ElMessageBox.confirm(
      `确定删除 Agent「${agent.name}」？此操作不可恢复。`,
      '删除确认',
      { type: 'error', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch { return }
  try {
    await agentStore.removeAgent(agent.id)
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  agentStore.loadAgents()
  loadOptions()
})
</script>

<style scoped>
.agent-list {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 60px);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar h2 {
  margin: 0;
}
</style>
