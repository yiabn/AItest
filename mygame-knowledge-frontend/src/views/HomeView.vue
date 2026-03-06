<template>
  <div class="home">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-card" :body-style="{ padding: '20px' }">
      <div class="welcome-content">
        <div>
          <h1 class="welcome-title">魔域资料分析工具</h1>
          <p class="welcome-desc">输入网址，自动提取幻兽、装备、技能等游戏数据，支持对话式补充</p>
        </div>
        <el-button type="primary" :icon="Document" @click="showExamples = !showExamples">
          查看示例
        </el-button>
      </div>

      <!-- 示例网址 -->
      <el-collapse-transition>
        <div v-if="showExamples" class="examples-panel">
          <div class="examples-title">📚 常用资料页面：</div>
          <div class="examples-list">
            <el-tag
              v-for="example in examples"
              :key="example.url"
              :type="example.type"
              effect="plain"
              class="example-tag"
              @click="useExample(example)"
            >
              <el-icon><component :is="getExampleIcon(example.type)" /></el-icon>
              {{ example.name }}
            </el-tag>
          </div>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 网址输入卡片 -->
    <el-card class="input-card" shadow="hover">
      <div class="url-input-area">
        <el-input
          v-model="url"
          placeholder="请输入魔域资料页面网址，例如：https://my.99.com/data/pet/123.html"
          size="large"
          clearable
          @keyup.enter="analyzeUrl"
        >
          <template #prepend>
            <el-icon><Link /></el-icon>
          </template>
          <template #append>
            <el-button
              type="primary"
              :loading="loading"
              @click="analyzeUrl"
              :icon="Search"
            >
              开始分析
            </el-button>
          </template>
        </el-input>

        <!-- 分析选项 -->
        <div class="analyze-options">
          <el-checkbox v-model="includeRaw">包含原始HTML</el-checkbox>
          <el-select v-model="depth" size="small" style="width: 120px">
            <el-option :value="1" label="深度1级" />
            <el-option :value="2" label="深度2级" />
            <el-option :value="3" label="深度3级" />
          </el-select>
        </div>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 分析结果区域 -->
    <div v-else-if="analysisResult" class="result-area">
      <!-- 结果标题栏 -->
      <div class="result-header">
        <div class="result-title">
          <el-icon><InfoFilled /></el-icon>
          <span>分析结果 - {{ analysisResult.title }}</span>
          <el-tag :type="getDataTypeTag(analysisResult.data_type)" size="small">
            {{ getDataTypeName(analysisResult.data_type) }}
          </el-tag>
        </div>
        <div class="result-actions">
          <el-button size="small" @click="refreshAnalysis">
            <el-icon><Refresh /></el-icon>重新分析
          </el-button>
          <el-button size="small" type="primary" @click="saveToKnowledge">
            <el-icon><Collection /></el-icon>保存到知识库
          </el-button>
        </div>
      </div>

      <!-- 基础信息卡片 -->
      <el-card class="result-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>📋 基础信息</span>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            <el-tag size="small">{{ analysisResult.task_id.slice(0, 8) }}...</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据类型">
            <el-tag :type="getDataTypeTag(analysisResult.data_type)" size="small">
              {{ getDataTypeName(analysisResult.data_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ analysisResult.source }}</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ formatTime(analysisResult.analyze_time) }}</el-descriptions-item>
          <el-descriptions-item label="页面URL" :span="2">
            <el-link :href="analysisResult.url" target="_blank" type="primary">
              {{ analysisResult.url }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 实体信息卡片 -->
      <el-card class="result-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <span>🧩 提取的实体信息</span>
              <el-tag size="small" type="info">{{ analysisResult.entities.length }}个实体</el-tag>
            </div>
            <div class="header-right">
              <el-radio-group v-model="entityViewMode" size="small">
                <el-radio-button value="card">卡片视图</el-radio-button>
                <el-radio-button value="table">表格视图</el-radio-button>
                <el-radio-button value="graph">关系图谱</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <!-- 卡片视图 -->
        <div v-if="entityViewMode === 'card'" class="entity-cards">
          <el-row :gutter="20">
            <el-col v-for="entity in analysisResult.entities" :key="entity.id" :xs="24" :sm="12" :md="8" :lg="6">
              <el-card class="entity-card" :body-style="{ padding: '0' }">
                <div class="entity-card-header" :class="entity.type">
                  <div class="entity-type-tag">
                    <el-tag :type="getEntityTypeTag(entity.type)" size="small">
                      {{ getEntityTypeName(entity.type) }}
                    </el-tag>
                  </div>
                  <div class="entity-name">{{ entity.name }}</div>
                </div>
                <div class="entity-card-body">
                  <div v-for="(value, key) in entity.attributes" :key="key" class="entity-attr">
                    <span class="attr-key">{{ key }}：</span>
                    <span class="attr-value">{{ value }}</span>
                  </div>
                  <div v-if="Object.keys(entity.attributes).length === 0" class="entity-empty">
                    暂无属性数据
                  </div>
                </div>
                <div class="entity-card-footer">
                  <el-button type="primary" link @click="openChatDialog(entity)">
                    <el-icon><ChatDotRound /></el-icon>补充信息
                  </el-button>
                  <el-button type="info" link @click="viewEntityDetail(entity)">
                    <el-icon><View /></el-icon>详情
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 表格视图 -->
        <div v-else-if="entityViewMode === 'table'" class="entity-table">
          <el-table :data="analysisResult.entities" stripe style="width: 100%">
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getEntityTypeTag(row.type)" size="small">
                  {{ getEntityTypeName(row.type) }}
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
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openChatDialog(row)">
                  补充
                </el-button>
                <el-button type="info" link @click="viewEntityDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 关系图谱视图 -->
        <div v-else class="graph-view">
          <div ref="graphRef" style="height: 500px; width: 100%"></div>
        </div>
      </el-card>

      <!-- AI建议卡片 -->
      <el-card class="result-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>💡 AI 分析建议</span>
          </div>
        </template>

        <div class="ai-suggestions">
          <el-timeline>
            <el-timeline-item
              v-for="(suggestion, index) in analysisResult.suggestions"
              :key="index"
              :type="index === 0 ? 'primary' : 'info'"
              :timestamp="'建议 ' + (index + 1)"
            >
              {{ suggestion }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-card>

      <!-- 原始内容卡片 -->
      <el-card v-if="includeRaw" class="result-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>📄 原始内容</span>
            <el-switch
              v-model="showRawHtml"
              active-text="HTML"
              inactive-text="文本"
              size="small"
            />
          </div>
        </template>

        <div class="raw-content">
          <pre v-if="!showRawHtml">{{ analysisResult.raw_text || '无文本内容' }}</pre>
          <pre v-else>{{ analysisResult.raw_html || '无HTML内容' }}</pre>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="输入网址开始分析" :image-size="200">
      <template #image>
        <el-icon :size="100" color="#909399"><Search /></el-icon>
      </template>
    </el-empty>

    <!-- 对话补充对话框 -->
    <el-dialog
      v-model="chatDialog.visible"
      :title="`补充信息 - ${chatDialog.entityName}`"
      width="600px"
      destroy-on-close
    >
      <div class="chat-container">
        <div class="chat-messages" ref="chatMessagesRef">
          <div
            v-for="(msg, index) in chatDialog.messages"
            :key="index"
            :class="['message', msg.role]"
          >
            <el-avatar :size="36" :src="msg.avatar || getDefaultAvatar(msg.role)" />
            <div class="message-content">
              <div class="message-sender">{{ msg.sender }}</div>
              <div class="message-text">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="chatDialog.sending" class="message assistant">
            <el-avatar :size="36" src="https://cube.elemecdn.com/9/c2/f0ee8a3c7c9638a54940382568c9dpng.png" />
            <div class="message-content">
              <div class="message-sender">AI助手</div>
              <div class="message-text typing">正在思考<span class="dots">...</span></div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <el-input
            v-model="chatDialog.input"
            type="textarea"
            :rows="2"
            :placeholder="`输入关于「${chatDialog.entityName}」的补充信息...`"
            @keyup.enter.prevent="sendChatMessage"
          />
          <div class="chat-actions">
            <div class="chat-tips">
              <el-tag size="small" effect="plain">例如：获取方式、属性数值、技能描述</el-tag>
            </div>
            <el-button
              type="primary"
              @click="sendChatMessage"
              :loading="chatDialog.sending"
              :icon="Promotion"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Link,
  Search,
  Refresh,
  Document,
  Collection,
  InfoFilled,
  ChatDotRound,
  View,
  Promotion,
  Platform,
  Medal,
  MagicStick,
  MapLocation,
  TrendCharts
} from '@element-plus/icons-vue';
import { analyzeApi, chatApi } from '@/api/config';
import type { AnalysisResult, Entity, ChatMessage } from '@/types';
import dayjs from 'dayjs';
import * as echarts from 'echarts';

// ========== 状态变量 ==========
const url = ref('');
const loading = ref(false);
const depth = ref(1);
const includeRaw = ref(false);
const analysisResult = ref<AnalysisResult | null>(null);
const entityViewMode = ref('card');
const showRawHtml = ref(false);
const showExamples = ref(false);
const graphRef = ref<HTMLElement>();

// ========== 示例数据 ==========
const examples = [
  { name: '幻兽·奇迹龙', url: 'https://my.99.com/data/pet/123.html', type: 'success' },
  { name: '装备·众神之袍', url: 'https://my.99.com/data/equip/456.html', type: 'warning' },
  { name: '技能·龙息术', url: 'https://my.99.com/data/skill/789.html', type: 'danger' },
  { name: '副本·冰封要塞', url: 'https://my.99.com/data/dungeon/321.html', type: 'info' }
];

// ========== 对话框状态 ==========
const chatDialog = reactive({
  visible: false,
  entityName: '',
  entityId: '',
  entityType: '',
  input: '',
  sending: false,
  messages: [] as ChatMessage[]
});

const chatMessagesRef = ref<HTMLElement>();

// ========== 方法 ==========
// 获取示例图标
const getExampleIcon = (type: string) => {
  const map: Record<string, any> = {
    success: Medal,
    warning: MagicStick,
    danger: Platform,
    info: MapLocation
  };
  return map[type] || Document;
};

// 使用示例
const useExample = (example: any) => {
  url.value = example.url;
  analyzeUrl();
};

// 查看实体详情
const viewEntityDetail = (entity: Entity) => {
  ElMessageBox.alert(
    `
    <div class="entity-detail">
      <h3>${entity.name}</h3>
      <p><strong>类型：</strong>${getEntityTypeName(entity.type)}</p>
      <p><strong>置信度：</strong>${entity.confidence ? (entity.confidence * 100).toFixed(0) + '%' : '未知'}</p>
      <h4>属性列表：</h4>
      <ul>
        ${Object.entries(entity.attributes).map(([key, value]) => 
          `<li><strong>${key}：</strong>${value}</li>`
        ).join('')}
      </ul>
    </div>
    `,
    '实体详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  );
};

// 分析URL
const analyzeUrl = async () => {
  if (!url.value) {
    ElMessage.warning('请输入网址');
    return;
  }

  loading.value = true;
  try {
    const result = await analyzeApi.analyzeUrl({
      url: url.value,
      depth: depth.value,
      include_raw: includeRaw.value
    });
    analysisResult.value = result;
    ElMessage.success('分析完成');

    saveToHistory(result);

    // 初始化关系图谱
    nextTick(() => {
      if (entityViewMode.value === 'graph') {
        initGraph();
      }
    });
  } catch (error) {
    console.error('分析失败:', error);
  } finally {
    loading.value = false;
  }
};

// 保存到历史记录
const saveToHistory = (result: AnalysisResult) => {
  const history = JSON.parse(localStorage.getItem('analysis_history') || '[]');
  history.unshift({
    id: result.task_id,
    title: result.title,
    type: result.data_type,
    url: result.url,
    time: new Date().toLocaleString(),
    task_id: result.task_id
  });
  // 只保留最近20条
  if (history.length > 20) history.pop();
  localStorage.setItem('analysis_history', JSON.stringify(history));
};

// 刷新分析
const refreshAnalysis = () => {
  if (url.value) {
    analyzeUrl();
  }
};

// 保存到知识库
const saveToKnowledge = async () => {
  if (!analysisResult.value) return;
  ElMessage.success('已保存到知识库（演示功能）');
};

// 获取数据类型标签
const getDataTypeTag = (type: string) => {
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

// 获取数据类型名称
const getDataTypeName = (type: string) => {
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

// 获取实体类型标签
const getEntityTypeTag = (type: string) => {
  const map: Record<string, string> = {
    pet: 'success',
    skill: 'danger',
    equipment: 'warning',
    item: 'info',
    npc: 'primary',
    monster: 'danger'
  };
  return map[type] || 'info';
};

// 获取实体类型名称
const getEntityTypeName = (type: string) => {
  const map: Record<string, string> = {
    pet: '幻兽',
    skill: '技能',
    equipment: '装备',
    item: '道具',
    npc: 'NPC',
    monster: '怪物'
  };
  return map[type] || type;
};

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

// 获取默认头像
const getDefaultAvatar = (role: string) => {
  const avatars: Record<string, string> = {
    system: 'https://cube.elemecdn.com/9/c2/f0ee8a3c7c9638a54940382568c9dpng.png',
    user: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png',
    assistant: 'https://cube.elemecdn.com/9/c2/f0ee8a3c7c9638a54940382568c9dpng.png'
  };
  return avatars[role] || avatars.system;
};

// 打开对话对话框
const openChatDialog = (entity: Entity) => {
  chatDialog.entityName = entity.name;
  chatDialog.entityId = entity.id || '';
  chatDialog.entityType = entity.type;
  chatDialog.visible = true;
  chatDialog.messages = [
    {
      role: 'system',
      sender: '系统',
      avatar: getDefaultAvatar('system'),
      content: `正在为${getEntityTypeName(entity.type)}「${entity.name}」补充信息，你可以告诉我：\n• 获取方式\n• 属性数值\n• 技能描述\n• 其他相关信息`
    }
  ];
  chatDialog.input = '';
};

// 发送聊天消息
const sendChatMessage = async () => {
  if (!chatDialog.input.trim()) {
    ElMessage.warning('请输入内容');
    return;
  }

  // 添加用户消息
  const userMessage: ChatMessage = {
    role: 'user',
    sender: '我',
    avatar: getDefaultAvatar('user'),
    content: chatDialog.input
  };
  chatDialog.messages.push(userMessage);

  const message = chatDialog.input;
  chatDialog.input = '';
  chatDialog.sending = true;

  await nextTick();
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }

  try {
    const response = await chatApi.supplementEntity({
      entity_id: chatDialog.entityId,
      entity_name: chatDialog.entityName,
      message: message
    });

    // 添加AI回复
    chatDialog.messages.push({
      role: 'assistant',
      sender: 'AI助手',
      avatar: getDefaultAvatar('assistant'),
      content: response.reply
    });

    // 如果返回了更新后的实体，刷新显示
    if (response.updated_entity && analysisResult.value) {
      const entity = analysisResult.value.entities.find(e => e.id === chatDialog.entityId);
      if (entity) {
        Object.assign(entity.attributes, response.updated_entity);
      }
    }
  } catch (error) {
    console.error('发送失败:', error);
    chatDialog.messages.push({
      role: 'assistant',
      sender: 'AI助手',
      avatar: getDefaultAvatar('assistant'),
      content: '抱歉，发送失败，请稍后重试。'
    });
  } finally {
    chatDialog.sending = false;
    await nextTick();
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
    }
  }
};

// 初始化关系图谱
const initGraph = () => {
  if (!graphRef.value || !analysisResult.value) return;

  const chart = echarts.init(graphRef.value);

  // 准备节点数据
  const nodes = analysisResult.value.entities.map((entity, index) => ({
    id: entity.id || `node_${index}`,
    name: entity.name,
    category: entity.type,
    symbolSize: 50,
    itemStyle: {
      color: getNodeColor(entity.type)
    }
  }));

  // 准备关系数据
  const links = analysisResult.value.relations?.map(rel => ({
    source: rel.source,
    target: rel.target,
    label: {
      show: true,
      formatter: rel.relation_type
    }
  })) || [];

  const option = {
    title: {
      text: '实体关系图谱',
      left: 'center'
    },
    tooltip: {},
    series: [{
      type: 'graph',
      layout: 'force',
      symbolSize: 50,
      roam: true,
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      edgeSymbol: ['none', 'arrow'],
      edgeLabel: {
        fontSize: 12
      },
      force: {
        repulsion: 1000,
        edgeLength: 200,
        gravity: 0.1
      },
      data: nodes,
      links: links,
      lineStyle: {
        color: '#999',
        width: 2,
        curveness: 0.3
      }
    }]
  };

  chart.setOption(option);
};

// 获取节点颜色
const getNodeColor = (type: string) => {
  const colors: Record<string, string> = {
    pet: '#67c23a',
    skill: '#f56c6c',
    equipment: '#e6a23c',
    item: '#909399',
    npc: '#409eff',
    monster: '#f56c6c'
  };
  return colors[type] || '#409eff';
};

// 监听视图切换
watch(entityViewMode, (newMode) => {
  if (newMode === 'graph' && analysisResult.value) {
    nextTick(() => {
      initGraph();
    });
  }
});

// 从URL参数加载
onMounted(() => {
  const query = new URLSearchParams(window.location.search);
  const urlParam = query.get('url');
  if (urlParam) {
    url.value = urlParam;
    analyzeUrl();
  }
});
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.welcome-desc {
  margin: 8px 0 0;
  opacity: 0.9;
}

.examples-panel {
  margin-top: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.examples-title {
  font-size: 14px;
  margin-bottom: 12px;
  opacity: 0.9;
}

.examples-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.example-tag {
  cursor: pointer;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.example-tag:hover {
  transform: translateY(-2px);
}

.input-card {
  margin-bottom: 20px;
}

.url-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analyze-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-state {
  padding: 40px;
  background: white;
  border-radius: 8px;
}

.result-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.result-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  gap: 8px;
}

.entity-cards {
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

.entity-type-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.entity-name {
  font-size: 18px;
  font-weight: 600;
  margin-top: 8px;
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

.entity-empty {
  color: #999;
  text-align: center;
  padding: 20px 0;
  font-size: 13px;
}

.entity-card-footer {
  padding: 12px 16px;
  display: flex;
  justify-content: space-around;
  border-top: 1px solid #eee;
}

.entity-table {
  padding: 10px;
}

.graph-view {
  height: 500px;
  width: 100%;
  background: #f5f7fa;
  border-radius: 4px;
}

.ai-suggestions {
  padding: 10px;
}

.raw-content {
  max-height: 400px;
  overflow-y: auto;
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.raw-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 聊天对话框样式 */
.chat-container {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.system {
  opacity: 0.8;
}

.message.user {
  flex-direction: row-reverse;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-sender {
  font-size: 12px;
  color: #909399;
}

.message-text {
  background-color: white;
  padding: 10px 14px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  line-height: 1.5;
  white-space: pre-wrap;
}

.message.user .message-text {
  background-color: #409eff;
  color: white;
}

.message.system .message-text {
  background-color: #f0f2f5;
  color: #666;
}

.typing {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dots {
  animation: typing 1.4s infinite;
}

@keyframes typing {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

.chat-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-tips {
  color: #909399;
  font-size: 12px;
}

@media (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .result-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .chat-actions {
    flex-direction: column;
    gap: 8px;
  }
}
</style>