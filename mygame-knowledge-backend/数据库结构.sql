-- =====================================================
-- 1. 核心实体表：entities
--    存储所有从页面提取的实体（幻兽、技能、装备、任务等）
-- =====================================================
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,          -- 实体类型：pet, skill, equipment, quest, npc, monster, map 等
    source_url TEXT,                     -- 来源页面URL
    source_game VARCHAR(100) DEFAULT '魔域',
    version VARCHAR(50),                  -- 数据版本（用于游戏版本更新）
    attributes JSONB NOT NULL DEFAULT '{}', -- 动态属性，JSON格式
    confidence FLOAT DEFAULT 1.0,          -- 数据置信度（0-1）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_attributes ON entities USING gin(attributes);
CREATE INDEX IF NOT EXISTS idx_entities_created_at ON entities(created_at DESC);

-- 注释
COMMENT ON TABLE entities IS '游戏实体主表';
COMMENT ON COLUMN entities.id IS '实体唯一ID（UUID）';
COMMENT ON COLUMN entities.name IS '实体名称';
COMMENT ON COLUMN entities.type IS '实体类型';
COMMENT ON COLUMN entities.attributes IS '动态属性（JSON格式）';
COMMENT ON COLUMN entities.confidence IS '置信度';


-- =====================================================
-- 2. 关系表：relations
--    存储实体之间的关联关系（如幻兽拥有技能）
-- =====================================================
CREATE TABLE IF NOT EXISTS relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,   -- 关系类型：has_skill, drops_from, rewards, located_in, evolves_to 等
    properties JSONB DEFAULT '{}',         -- 关系属性（如数量、概率等）
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_id, target_id, relation_type)  -- 避免重复关系
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_created_at ON relations(created_at DESC);

COMMENT ON TABLE relations IS '实体关系表';
COMMENT ON COLUMN relations.source_id IS '源实体ID';
COMMENT ON COLUMN relations.target_id IS '目标实体ID';
COMMENT ON COLUMN relations.relation_type IS '关系类型';
COMMENT ON COLUMN relations.properties IS '关系属性（JSON）';


-- =====================================================
-- 3. 用户补充表：user_supplements
--    记录用户通过对话补充的信息
-- =====================================================
CREATE TABLE IF NOT EXISTS user_supplements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    user_id VARCHAR(255),                -- 用户标识（若实现用户系统）
    field_name VARCHAR(100),              -- 补充的字段名
    field_value TEXT,                      -- 补充的内容
    original_value TEXT,                   -- 原始值（用于对比）
    source VARCHAR(50) DEFAULT 'chat',     -- 来源：chat/form/import
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'   -- pending/approved/rejected
);

CREATE INDEX IF NOT EXISTS idx_supplements_entity ON user_supplements(entity_id);
CREATE INDEX IF NOT EXISTS idx_supplements_created ON user_supplements(created_at DESC);

COMMENT ON TABLE user_supplements IS '用户补充信息记录表';
COMMENT ON COLUMN user_supplements.status IS '状态：pending待审核，approved已采纳，rejected拒绝';


-- =====================================================
-- 4. 页面快照表：page_snapshots
--    存储抓取的原始页面内容，用于回溯和重新解析
-- =====================================================
CREATE TABLE IF NOT EXISTS page_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title VARCHAR(500),
    raw_html TEXT,                       -- 原始HTML（可能很大，可根据需要压缩）
    raw_text TEXT,                       -- 提取的纯文本
    fetch_time TIMESTAMP DEFAULT NOW(),
    version VARCHAR(50),
    parse_status VARCHAR(20) DEFAULT 'pending'  -- pending/success/failed
);

CREATE INDEX IF NOT EXISTS idx_snapshots_url ON page_snapshots(url);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON page_snapshots(fetch_time DESC);

COMMENT ON TABLE page_snapshots IS '页面原始快照表，用于回溯和重新解析';


-- =====================================================
-- 5. 分析任务记录表：analysis_tasks（可选）
--    记录每次分析请求的任务状态，便于跟踪
-- =====================================================
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(100) UNIQUE NOT NULL,  -- 与前端返回的task_id一致
    url TEXT NOT NULL,
    depth INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/processing/completed/failed
    result JSONB,                          -- 完整的分析结果（可选）
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON analysis_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON analysis_tasks(created_at DESC);

COMMENT ON TABLE analysis_tasks IS '分析任务记录表';


-- =====================================================
-- 6. 触发器：自动更新 entities 的 updated_at 字段
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_entities_updated_at ON entities;
CREATE TRIGGER update_entities_updated_at
    BEFORE UPDATE ON entities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();