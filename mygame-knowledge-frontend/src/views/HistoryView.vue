<template>
  <div class="history">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📜 分析历史记录</span>
          <div>
            <el-button type="primary" link @click="handleRefresh">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
            <el-button type="danger" link @click="handleClearAll">
              <el-icon><Delete /></el-icon>清空
            </el-button>
          </div>
        </div>
      </template>

      <el-timeline v-if="historyList.length > 0">
        <el-timeline-item
          v-for="item in historyList"
          :key="item.id"
          :timestamp="item.time"
          :type="getTypeTag(item.type)"
          placement="top"
        >
          <el-card shadow="hover">
            <div class="history-item">
              <div class="history-info">
                <el-tag :type="getTypeTag(item.type)" size="small">
                  {{ getTypeName(item.type) }}
                </el-tag>
                <span class="history-title">{{ item.title }}</span>
              </div>
              <div class="history-actions">
                <el-button size="small" type="primary" @click="handleReanalyze(item)">
                  <el-icon><Refresh /></el-icon>重新分析
                </el-button>
                <el-button size="small" @click="handleViewDetail(item)">
                  <el-icon><View /></el-icon>查看
                </el-button>
                <el-button size="small" type="danger" link @click="handleDelete(item.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="history-url">
              <el-link :href="item.url" target="_blank" type="info" :underline="false">
                {{ item.url }}
              </el-link>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-else description="暂无历史记录" :image-size="200" />
    </el-card>

    <!-- 历史详情对话框 -->
    <el-dialog
      v-model="detailDialog.visible"
      :title="detailDialog.title"
      width="700px"
      destroy-on-close
    >
      <div v-if="detailDialog.loading" class="detail-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="detailDialog.data" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            <el-tag size="small">{{ detailDialog.data.task_id }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getTypeTag(detailDialog.data.data_type)" size="small">
              {{ getTypeName(detailDialog.data.data_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ detailDialog.data.source }}</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ detailDialog.data.analyze_time }}</el-descriptions-item>
          <el-descriptions-item label="URL" :span="2">
            <el-link :href="detailDialog.data.url" target="_blank">{{ detailDialog.data.url }}</el-link>
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">提取的实体 ({{ detailDialog.data.entities.length }})</h4>
        <el-table :data="detailDialog.data.entities" stripe size="small" style="width: 100%">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTag(row.type)" size="small">
                {{ getTypeName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="属性">
            <template #default="{ row }">
              <el-space wrap>
                <el-tag 
                  v-for="(value, key) in row.attributes" 
                  :key="key" 
                  size="small" 
                  effect="plain"
                >
                  {{ key }}: {{ value }}
                </el-tag>
              </el-space>
            </template>
          </el-table-column>
        </el-table>

        <h4 class="section-title">AI建议</h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in detailDialog.data.suggestions" :key="index">
            <el-tag size="small" :type="index === 0 ? 'primary' : 'info'" effect="plain">
              建议 {{ index + 1 }}
            </el-tag>
            <span>{{ suggestion }}</span>
          </li>
        </ul>
      </div>
      <div v-else class="detail-empty">
        <el-empty description="无数据" :image-size="100" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Delete, View } from '@element-plus/icons-vue';
import { analyzeApi } from '@/api/config';
import type { HistoryItem, AnalysisResult } from '@/types';

const router = useRouter();
const historyList = ref<HistoryItem[]>([]);

// 详情对话框
const detailDialog = reactive({
  visible: false,
  title: '',
  loading: false,
  data: null as AnalysisResult | null
});

// 生命周期钩子
onMounted(() => {
  loadHistoryData();
});

// 加载历史记录
const loadHistoryData = () => {
  const saved = localStorage.getItem('analysis_history');
  if (saved) {
    try {
      historyList.value = JSON.parse(saved);
    } catch (e) {
      console.error('加载历史失败:', e);
      historyList.value = getExampleData();
    }
  } else {
    historyList.value = getExampleData();
  }
};

// 获取示例数据
const getExampleData = (): HistoryItem[] => {
  return [
    {
      id: '1',
      title: '幻兽·奇迹龙',
      type: 'pet',
      url: 'https://my.99.com/data/pet/123.html',
      time: new Date().toLocaleString(),
      task_id: 'task_123'
    },
    {
      id: '2',
      title: '装备·众神之袍',
      type: 'equipment',
      url: 'https://my.99.com/data/equip/456.html',
      time: new Date(Date.now() - 3600000).toLocaleString(),
      task_id: 'task_456'
    }
  ];
};

// 获取类型标签样式
const getTypeTag = (type: string): string => {
  const map: Record<string, string> = {
    pet: 'success',
    equipment: 'warning',
    skill: 'danger',
    dungeon: 'info',
    map: 'primary',
    general: 'info'
  };
  return map[type] || 'info';
};

// 获取类型名称
const getTypeName = (type: string): string => {
  const map: Record<string, string> = {
    pet: '幻兽',
    equipment: '装备',
    skill: '技能',
    dungeon: '副本',
    map: '地图',
    general: '通用'
  };
  return map[type] || type;
};

// 查看详情
const handleViewDetail = async (item: HistoryItem) => {
  detailDialog.title = item.title;
  detailDialog.visible = true;
  detailDialog.loading = true;
  
  try {
    // 从后端获取完整数据
    const result = await analyzeApi.getTask(item.task_id);
    detailDialog.data = result;
  } catch (error) {
    console.error('获取详情失败:', error);
    ElMessage.error('获取详情失败');
    
    // 如果后端获取失败，显示本地保存的简化数据
    detailDialog.data = {
      task_id: item.task_id,
      title: item.title,
      url: item.url,
      data_type: item.type,
      entities: [],
      suggestions: ['无详细数据'],
      analyze_time: item.time,
      source: '本地缓存'
    } as AnalysisResult;
  } finally {
    detailDialog.loading = false;
  }
};

// 重新分析
const handleReanalyze = (item: HistoryItem) => {
  router.push({
    path: '/',
    query: { url: item.url }
  });
};

// 删除单条记录
const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    historyList.value = historyList.value.filter(item => item.id !== id);
    localStorage.setItem('analysis_history', JSON.stringify(historyList.value));
    ElMessage.success('删除成功');
  } catch {
    // 取消删除
  }
};

// 刷新列表
const handleRefresh = () => {
  loadHistoryData();
  ElMessage.success('刷新成功');
};

// 清空所有记录
const handleClearAll = async () => {
  if (historyList.value.length === 0) return;
  
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？', '提示', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    historyList.value = [];
    localStorage.removeItem('analysis_history');
    ElMessage.success('已清空');
  } catch {
    // 取消清空
  }
};
</script>

<style scoped>
.history {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-title {
  font-size: 16px;
  font-weight: 500;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.history-url {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  font-size: 12px;
  word-break: break-all;
}

.detail-content {
  padding: 10px 0;
}

.section-title {
  margin: 20px 0 10px;
  font-size: 16px;
  font-weight: 500;
}

.suggestions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestions-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.suggestions-list li:last-child {
  border-bottom: none;
}

.suggestions-list li span {
  flex: 1;
  line-height: 1.6;
}

.detail-loading {
  padding: 20px;
}

.detail-empty {
  padding: 40px;
}

:deep(.el-descriptions) {
  margin-bottom: 20px;
}

:deep(.el-table) {
  margin-bottom: 20px;
}
</style>