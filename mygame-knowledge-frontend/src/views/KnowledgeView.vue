<template>
  <div class="knowledge">
    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="stats-row" v-if="!statsLoading">
      <el-col :span="6" v-for="stat in statsCards" :key="stat.label">
        <el-card class="stat-card" :body-style="{ padding: '20px' }" shadow="hover">
          <div class="stat-icon" :style="{ color: stat.color }">
            <el-icon :size="32"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-skeleton :rows="1" animated v-else class="stats-skeleton" />

    <!-- 搜索和过滤栏 -->
    <el-card class="search-card" shadow="hover">
      <div class="search-header">
        <div class="search-input">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索实体名称或属性..."
            :prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" @click="handleSearch" :loading="searchLoading">
            搜索
          </el-button>
        </div>
        <div class="filter-options">
          <el-select v-model="filterType" placeholder="全部类型" clearable @change="handleFilterChange">
            <el-option
              v-for="type in typeStats"
              :key="type.type"
              :label="`${type.type} (${type.count})`"
              :value="type.type"
            />
          </el-select>
          <el-radio-group v-model="viewMode" size="default">
            <el-radio-button value="grid">网格</el-radio-button>
            <el-radio-button value="list">列表</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-card>

    <!-- 实体列表/网格区域 -->
    <el-card class="entities-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>📚 知识库实体 ({{ totalEntities }})</span>
          <div class="header-actions">
            <el-button size="small" @click="refreshData" :loading="refreshing">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
            <el-button size="small" type="primary" @click="showStatsDialog = true">
              <el-icon><DataAnalysis /></el-icon>详细统计
            </el-button>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="entitiesLoading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <!-- 空状态 -->
      <el-empty v-else-if="!entities.length" description="暂无实体数据" :image-size="200" />

      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="entity-grid">
        <el-row :gutter="20">
          <el-col
            v-for="entity in entities"
            :key="entity.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <el-card class="entity-card" shadow="hover" @click="viewEntityDetail(entity)">
              <div class="entity-card-header" :class="entity.type">
                <div class="entity-type-tag">
                  <el-tag :type="getEntityTypeTag(entity.type)" size="small">
                    {{ getEntityTypeName(entity.type) }}
                  </el-tag>
                </div>
                <div class="entity-name">{{ entity.name }}</div>
                <div class="entity-confidence">
                  置信度: {{ (entity.confidence * 100).toFixed(0) }}%
                </div>
              </div>
              <div class="entity-card-body">
                <template v-if="Object.keys(entity.attributes).length">
                  <div v-for="(value, key) in topAttributes(entity)" :key="key" class="entity-attr">
                    <span class="attr-key">{{ key }}:</span>
                    <span class="attr-value">{{ value }}</span>
                  </div>
                  <div v-if="Object.keys(entity.attributes).length > 3" class="entity-more">
                    等{{ Object.keys(entity.attributes).length }}个属性
                  </div>
                </template>
                <div v-else class="entity-empty">
                  暂无属性数据
                </div>
              </div>
              <div class="entity-card-footer">
                <el-tag size="small" type="info">
                  {{ formatDate(entity.created_at) }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 列表视图 -->
      <div v-else class="entity-list">
        <el-table :data="entities" stripe style="width: 100%" @row-click="viewEntityDetail">
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getEntityTypeTag(row.type)" size="small">
                {{ getEntityTypeName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="主要属性">
            <template #default="{ row }">
              <el-space wrap>
                <el-tag
                  v-for="(value, key) in topAttributes(row, 3)"
                  :key="key"
                  size="small"
                  effect="plain"
                >
                  {{ key }}: {{ value }}
                </el-tag>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="row.confidence * 100"
                :format="() => (row.confidence * 100).toFixed(0) + '%'"
                :color="getConfidenceColor(row.confidence)"
              />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="!entitiesLoading && entities.length">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalEntities"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 实体详情抽屉 -->
    <el-drawer
      v-model="detailDrawer.visible"
      :title="detailDrawer.entity?.name || '实体详情'"
      size="50%"
      destroy-on-close
    >
      <div v-if="detailDrawer.loading" class="drawer-loading">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="detailDrawer.entity" class="entity-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detailDrawer.entity.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getEntityTypeTag(detailDrawer.entity.type)">
              {{ getEntityTypeName(detailDrawer.entity.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度">
            <el-progress
              :percentage="detailDrawer.entity.confidence * 100"
              :format="() => (detailDrawer.entity.confidence * 100).toFixed(0) + '%'"
              :color="getConfidenceColor(detailDrawer.entity.confidence)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            <span v-if="detailDrawer.entity.source_url">
              <el-link :href="detailDrawer.entity.source_url" target="_blank">
                查看原网页
              </el-link>
            </span>
            <span v-else>未知</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(detailDrawer.entity.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(detailDrawer.entity.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="detail-section">属性详情</h4>
        <el-table :data="attributeList" stripe size="small">
          <el-table-column prop="key" label="属性名" width="200" />
          <el-table-column prop="value" label="属性值" />
        </el-table>

        <h4 class="detail-section">关系网络</h4>
        <div class="relations-preview">
          <div v-if="detailDrawer.relations?.length" class="relations-list">
            <el-tag
              v-for="rel in detailDrawer.relations.slice(0, 10)"
              :key="rel.id"
              class="relation-tag"
              :type="getRelationTypeTag(rel.relation_type)"
              effect="plain"
            >
              {{ rel.source_name }} → {{ rel.relation_type }} → {{ rel.target_name }}
            </el-tag>
            <div v-if="detailDrawer.relations.length > 10" class="relations-more">
              等{{ detailDrawer.relations.length }}个关系
            </div>
          </div>
          <el-empty v-else description="暂无关系" :image-size="60" />
        </div>

        <h4 class="detail-section">补充历史</h4>
        <div class="supplements-list">
          <el-timeline v-if="detailDrawer.supplements?.length">
            <el-timeline-item
              v-for="sup in detailDrawer.supplements"
              :key="sup.id"
              :timestamp="formatDateTime(sup.created_at)"
              :type="sup.status === 'approved' ? 'success' : 'info'"
            >
              <p><strong>{{ sup.field_name }}:</strong> {{ sup.field_value }}</p>
              <p v-if="sup.original_value" class="original-value">
                原值: {{ sup.original_value }}
              </p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无补充历史" :image-size="60" />
        </div>
      </div>
    </el-drawer>

    <!-- 统计详情对话框 -->
    <el-dialog v-model="showStatsDialog" title="知识库统计" width="600px">
      <div v-if="statsLoading" class="dialog-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else class="stats-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总实体数">{{ stats?.total_entities || 0 }}</el-descriptions-item>
          <el-descriptions-item label="总关系数">{{ stats?.total_relations || 0 }}</el-descriptions-item>
          <el-descriptions-item label="总补充数">{{ stats?.total_supplements || 0 }}</el-descriptions-item>
          <el-descriptions-item label="今日新增">{{ stats?.today_new || 0 }}</el-descriptions-item>
        </el-descriptions>

        <h4>类型分布</h4>
        <el-table :data="stats?.type_distribution || []" stripe>
          <el-table-column prop="type" label="类型" />
          <el-table-column prop="count" label="数量" />
          <el-table-column label="占比">
            <template #default="{ row }">
              {{ ((row.count / (stats?.total_entities || 1)) * 100).toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>

        <p class="stats-update">最后更新: {{ formatDateTime(stats?.last_update || '') }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Search,
  Refresh,
  DataAnalysis,
  Platform,
  Medal,
  MagicStick,
  MapLocation,
  TrendCharts
} from '@element-plus/icons-vue';
import { knowledgeApi } from '@/api/config';
import type { Entity, TypeStat, KnowledgeStats } from '@/api/config';
import dayjs from 'dayjs';

// 类型扩展
interface EntityDetail {
  entity: Entity;
  relations: any[];
  supplements: any[];
}

// ========== 状态 ==========
// 列表数据
const entities = ref<Entity[]>([]);
const totalEntities = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const entitiesLoading = ref(false);

// 统计和类型
const stats = ref<KnowledgeStats | null>(null);
const typeStats = ref<TypeStat[]>([]);
const statsLoading = ref(false);
const refreshing = ref(false);

// 搜索和过滤
const searchKeyword = ref('');
const filterType = ref('');
const searchLoading = ref(false);

// 视图模式
const viewMode = ref<'grid' | 'list'>('grid');

// 对话框
const showStatsDialog = ref(false);
const detailDrawer = reactive({
  visible: false,
  loading: false,
  entity: null as Entity | null,
  relations: [] as any[],
  supplements: [] as any[]
});

// ========== 计算属性 ==========
const statsCards = computed(() => [
  {
    icon: Platform,
    label: '总实体数',
    value: stats.value?.total_entities || 0,
    color: '#409eff'
  },
  {
    icon: TrendCharts,
    label: '关系数',
    value: stats.value?.total_relations || 0,
    color: '#67c23a'
  },
  {
    icon: Medal,
    label: '补充数',
    value: stats.value?.total_supplements || 0,
    color: '#e6a23c'
  },
  {
    icon: MapLocation,
    label: '今日新增',
    value: stats.value?.today_new || 0,
    color: '#f56c6c'
  }
]);

const attributeList = computed(() => {
  if (!detailDrawer.entity) return [];
  return Object.entries(detailDrawer.entity.attributes).map(([key, value]) => ({
    key,
    value: String(value)
  }));
});

// ========== 工具函数 ==========
const getEntityTypeTag = (type: string): string => {
  const map: Record<string, string> = {
    pet: 'success',
    skill: 'danger',
    equipment: 'warning',
    item: 'info',
    npc: 'primary',
    monster: 'danger',
    quest: 'info'
  };
  return map[type] || 'info';
};

const getEntityTypeName = (type: string): string => {
  const map: Record<string, string> = {
    pet: '幻兽',
    skill: '技能',
    equipment: '装备',
    item: '道具',
    npc: 'NPC',
    monster: '怪物',
    quest: '任务'
  };
  return map[type] || type;
};

const getRelationTypeTag = (type: string): string => {
  const map: Record<string, string> = {
    has_skill: 'danger',
    drops_from: 'warning',
    rewards: 'success',
    located_in: 'info',
    evolves_to: 'primary'
  };
  return map[type] || 'info';
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.9) return '#67c23a';
  if (confidence >= 0.7) return '#e6a23c';
  return '#f56c6c';
};

const topAttributes = (entity: Entity, count: number = 3): Record<string, any> => {
  return Object.fromEntries(Object.entries(entity.attributes).slice(0, count));
};

const formatDate = (date: string): string => {
  if (!date) return '未知';
  return dayjs(date).format('MM-DD HH:mm');
};

const formatDateTime = (date: string): string => {
  if (!date) return '未知';
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

// ========== 数据加载 ==========
const loadEntities = async () => {
  entitiesLoading.value = true;
  try {
    const data = await knowledgeApi.getEntities({
      type: filterType.value || undefined,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    });
    entities.value = data || [];
  } catch (error: any) {
    console.error('加载实体失败:', error);
    ElMessage.error('加载实体失败: ' + (error.message || '未知错误'));
    entities.value = [];
  } finally {
    entitiesLoading.value = false;
  }
};

const loadStats = async () => {
  statsLoading.value = true;
  try {
    stats.value = await knowledgeApi.getStats();
  } catch (error: any) {
    console.error('加载统计失败:', error);
  } finally {
    statsLoading.value = false;
  }
};

const loadTypeStats = async () => {
  try {
    typeStats.value = await knowledgeApi.getTypeStats() || [];
  } catch (error: any) {
    console.error('加载类型统计失败:', error);
  }
};

// 刷新所有数据
const refreshData = async () => {
  refreshing.value = true;
  try {
    await Promise.all([loadStats(), loadTypeStats(), loadEntities()]);
    ElMessage.success('刷新成功');
  } catch (error) {
    // 错误已内部处理
  } finally {
    refreshing.value = false;
  }
};

// ========== 搜索与过滤 ==========
const handleSearch = async () => {
  if (!searchKeyword.value) {
    // 如果搜索词为空，重新加载列表（按当前过滤条件）
    await loadEntities();
    return;
  }

  searchLoading.value = true;
  try {
    const result = await knowledgeApi.search(searchKeyword.value, filterType.value || undefined);
    entities.value = result.results || [];
    totalEntities.value = result.total || 0;
  } catch (error: any) {
    console.error('搜索失败:', error);
    ElMessage.error('搜索失败: ' + (error.message || '未知错误'));
  } finally {
    searchLoading.value = false;
  }
};

const handleFilterChange = () => {
  currentPage.value = 1;
  if (searchKeyword.value) {
    handleSearch();
  } else {
    loadEntities();
  }
};

// ========== 分页 ==========
const handlePageChange = (page: number) => {
  currentPage.value = page;
  if (searchKeyword.value) {
    handleSearch();
  } else {
    loadEntities();
  }
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  if (searchKeyword.value) {
    handleSearch();
  } else {
    loadEntities();
  }
};

// ========== 详情抽屉 ==========
const viewEntityDetail = async (entity: Entity) => {
  detailDrawer.visible = true;
  detailDrawer.loading = true;
  detailDrawer.entity = entity;
  detailDrawer.relations = [];
  detailDrawer.supplements = [];

  try {
    const detail = await knowledgeApi.getEntityDetail(entity.id) as EntityDetail;
    detailDrawer.relations = detail.relations || [];
    detailDrawer.supplements = detail.supplements || [];
  } catch (error: any) {
    console.error('加载详情失败:', error);
    ElMessage.error('加载详情失败: ' + (error.message || '未知错误'));
  } finally {
    detailDrawer.loading = false;
  }
};

// ========== 初始化 ==========
onMounted(async () => {
  await Promise.all([loadStats(), loadTypeStats(), loadEntities()]);
});

// 监听过滤类型变化（已通过 handleFilterChange 处理）
// 监听分页变化由分页组件触发
</script>

<style scoped>
.knowledge {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  margin-right: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stats-skeleton {
  margin-bottom: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.search-input {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 300px;
}

.filter-options {
  display: flex;
  gap: 12px;
  align-items: center;
}

.entities-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.loading-container {
  padding: 40px;
}

.entity-grid {
  padding: 10px;
}

.entity-card {
  margin-bottom: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.entity-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.entity-card-header {
  padding: 16px;
  color: white;
  position: relative;
  border-radius: 4px 4px 0 0;
}

.entity-card-header.pet {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}

.entity-card-header.skill {
  background: linear-gradient(135deg, #f56c6c 0%, #c45656 100%);
}

.entity-card-header.equipment {
  background: linear-gradient(135deg, #e6a23c 0%, #b88230 100%);
}

.entity-card-header.item {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
}

.entity-card-header.npc {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.entity-card-header.monster {
  background: linear-gradient(135deg, #f56c6c 0%, #c45656 100%);
}

.entity-card-header.quest {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
}

.entity-type-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.entity-name {
  font-size: 18px;
  font-weight: 600;
  margin: 8px 0 4px;
}

.entity-confidence {
  font-size: 12px;
  opacity: 0.9;
}

.entity-card-body {
  padding: 16px;
  min-height: 100px;
  background: #f8f9fa;
}

.entity-attr {
  display: flex;
  margin-bottom: 6px;
  font-size: 13px;
}

.attr-key {
  width: 80px;
  color: #666;
}

.attr-value {
  flex: 1;
  color: #333;
  font-weight: 500;
}

.entity-more {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.entity-empty {
  color: #999;
  text-align: center;
  padding: 20px 0;
  font-size: 13px;
}

.entity-card-footer {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #eee;
}

.entity-list {
  padding: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.drawer-loading {
  padding: 20px;
}

.entity-detail {
  padding: 10px;
}

.detail-section {
  margin: 20px 0 10px;
  font-size: 16px;
  font-weight: 500;
}

.relations-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.relation-tag {
  cursor: default;
}

.relations-more {
  color: #909399;
  font-size: 13px;
  padding: 4px 0;
}

.supplements-list {
  max-height: 300px;
  overflow-y: auto;
}

.original-value {
  font-size: 12px;
  color: #909399;
  margin: 2px 0 0;
}

.stats-detail {
  padding: 10px;
}

.stats-update {
  margin-top: 16px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.dialog-loading {
  padding: 30px;
}

@media (max-width: 768px) {
  .search-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-options {
    width: 100%;
    justify-content: space-between;
  }
  
  .stat-card {
    margin-bottom: 10px;
  }
}
</style>