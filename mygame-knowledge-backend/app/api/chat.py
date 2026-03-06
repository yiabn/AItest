# app/api/chat.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List, Tuple
import re
import logging
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import db

# 在文件内直接定义请求和响应模型，避免循环导入
class ChatRequest(BaseModel):
    entity_id: str
    entity_name: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    updated_entity: Optional[Dict[str, Any]] = None

# 创建 router 实例
router = APIRouter()
logger = logging.getLogger(__name__)

# 移除内存中的 knowledge_base，改用数据库存储
# knowledge_base = {}

@router.post("/supplement", response_model=ChatResponse)
async def supplement_entity(request: ChatRequest):
    """智能对话补充实体信息（支持数据库持久化）"""
    try:
        logger.info(f"收到补充请求: {request.entity_name} - {request.message}")
        
        # 1. 从数据库获取实体现有信息
        existing_entity = await db.get_entity(request.entity_id)
        existing_info = existing_entity.get('attributes', {}) if existing_entity else {}
        
        # 2. 智能解析用户消息
        new_info, reply = process_chat_message(
            request.message, 
            request.entity_name,
            existing_info
        )
        
        # 3. 更新数据库中的实体
        if new_info:
            # 从实体ID判断是临时ID还是数据库UUID
            if is_uuid(request.entity_id):
                # 是数据库UUID，直接更新
                success = await db.update_entity_attributes(request.entity_id, new_info)
                if success:
                    logger.info(f"实体更新成功: {request.entity_id}")
                    
                    # 记录用户补充信息
                    for key, value in new_info.items():
                        await db.add_user_supplement(
                            entity_id=request.entity_id,
                            user_id=request.context.get('user_id') if request.context else None,
                            field_name=key,
                            field_value=str(value),
                            original_value=str(existing_info.get(key)) if existing_info.get(key) else None,
                            source='chat'
                        )
                else:
                    logger.warning(f"实体更新失败: {request.entity_id}")
            else:
                # 是临时ID（如 task_id_entity_0），无法直接更新数据库
                # 可以尝试通过名称查找对应的实体
                logger.warning(f"收到临时ID，无法直接更新: {request.entity_id}")
                reply += " 注意：这是临时ID，数据可能不会永久保存。建议刷新页面后重试。"
        
        # 4. 返回响应
        return ChatResponse(
            reply=reply,
            updated_entity=new_info
        )
        
    except Exception as e:
        logger.error(f"补充信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{entity_id}")
async def get_chat_history(entity_id: str):
    """获取实体的对话补充历史"""
    try:
        query = """
            SELECT * FROM user_supplements 
            WHERE entity_id = $1 
            ORDER BY created_at DESC 
            LIMIT 50
        """
        rows = await db.fetch(query, entity_id)
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'field_name': row['field_name'],
                'field_value': row['field_value'],
                'original_value': row['original_value'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'status': row['status']
            })
        
        return {"entity_id": entity_id, "history": history}
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity/{entity_id}")
async def get_entity_info(entity_id: str):
    """获取实体的完整信息"""
    try:
        entity = await db.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取关系信息
        relations = await db.get_relations(entity_id)
        
        return {
            "entity": entity,
            "relations": relations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_entities(keyword: str, entity_type: Optional[str] = None):
    """搜索实体"""
    try:
        results = await db.search_entities(keyword, entity_type)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test():
    """测试路由"""
    return {"message": "chat API is working", "status": "ok"}

# ========== 辅助函数 ==========

def is_uuid(value: str) -> bool:
    """判断字符串是否为UUID格式"""
    import uuid
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def process_chat_message(message: str, entity_name: str, existing_info: Dict) -> Tuple[Dict, str]:
    """处理聊天消息，返回新信息和回复"""
    
    message_lower = message.lower()
    new_info = {}
    
    # 1. 识别信息类型
    info_type = identify_info_type(message)
    
    # 2. 提取具体内容
    if info_type == "acquisition":
        content = extract_acquisition(message)
        new_info["acquisition"] = content
        reply = f"好的，已记录「{entity_name}」的获取方式：{content}"
        
    elif info_type == "attribute":
        attr_name, attr_value = extract_attribute(message)
        if attr_name and attr_value:
            new_info[f"attr_{attr_name}"] = attr_value
            reply = f"已更新属性「{attr_name}」为：{attr_value}"
        else:
            new_info["note"] = message
            reply = f"收到关于「{entity_name}」的补充信息"
            
    elif info_type == "skill":
        skill_name, skill_desc = extract_skill(message)
        new_info["skill"] = {"name": skill_name, "description": skill_desc}
        reply = f"已记录技能「{skill_name}」"
        
    elif info_type == "question":
        # 如果是问题，尝试从已有知识回答
        answer = try_answer_question(message, existing_info, entity_name)
        if answer:
            reply = answer
        else:
            reply = f"关于「{entity_name}」，我目前知道的是：\n" + format_existing_info(existing_info)
            
    elif info_type == "correction":
        # 纠正信息
        corrected = extract_correction(message)
        new_info.update(corrected)
        reply = "好的，已修正信息"
        
    else:
        # 默认识别为补充信息
        new_info["note"] = message
        reply = f"收到关于「{entity_name}」的补充信息，已记录。还有什么需要补充的吗？"
    
    # 如果有现有信息，可以在回复中体现
    if existing_info and info_type != "question":
        reply += " " + suggest_next_question(existing_info)
    
    return new_info, reply

def identify_info_type(message: str) -> str:
    """识别信息类型"""
    message_lower = message.lower()
    
    # 获取方式
    if any(kw in message_lower for kw in ["获得", "获取", "掉落", "兑换", "购买", "得到"]):
        return "acquisition"
    
    # 属性数值
    if any(kw in message_lower for kw in ["属性", "数值", "攻击", "防御", "生命", "速度", "力量", "智力"]):
        return "attribute"
    
    # 技能
    if any(kw in message_lower for kw in ["技能", "天赋", "战技", "能力"]):
        return "skill"
    
    # 问题
    if any(kw in message_lower for kw in ["?", "？", "什么", "如何", "怎么", "多少", "为什么"]):
        return "question"
    
    # 纠正
    if any(kw in message_lower for kw in ["不对", "错误", "更正", "不是", "应该是"]):
        return "correction"
    
    return "general"

def extract_acquisition(message: str) -> str:
    """提取获取方式"""
    # 尝试提取掉落地点
    match = re.search(r'([\u4e00-\u9fa5]+)(?:副本|地图|场景|boss|BOSS).*?(?:掉落|获得|获取)', message)
    if match:
        return f"掉落自：{match.group(1)}"
    
    # 尝试提取购买方式
    match = re.search(r'([\u4e00-\u9fa5]+)(?:商店|商人|NPC).*?(?:购买|兑换)', message)
    if match:
        return f"购买自：{match.group(1)}"
    
    return message.strip()

def extract_attribute(message: str) -> Tuple[Optional[str], Optional[str]]:
    """提取属性名和值"""
    # 匹配如 "攻击力是8500" 或 "攻击:8500"
    patterns = [
        r'([\u4e00-\u9fa5]{2,})(?:是|为|：|:|\s+)(\d+\.?\d*)',
        r'([\u4e00-\u9fa5]{2,})\s*(\d+\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1), match.group(2)
    
    return None, None

def extract_skill(message: str) -> Tuple[str, str]:
    """提取技能信息"""
    # 尝试提取技能名
    match = re.search(r'(?:技能|拥有)\s*[‘’""]?([\u4e00-\u9fa5]{2,})[’’""]?', message)
    if match:
        skill_name = match.group(1)
        return skill_name, message
    
    # 提取技能描述
    match = re.search(r'([\u4e00-\u9fa5]{2,})(?:技能|效果|描述)[：:]\s*([^\n]+)', message)
    if match:
        return match.group(1), match.group(2)
    
    return "未知技能", message

def try_answer_question(message: str, existing_info: Dict, entity_name: str) -> Optional[str]:
    """尝试回答问题"""
    message_lower = message.lower()
    
    if "怎么获得" in message_lower or "如何获取" in message_lower or "哪里掉落" in message_lower:
        if "acquisition" in existing_info:
            return f"「{entity_name}」的获取方式是：{existing_info['acquisition']}"
        else:
            return f"抱歉，我还不清楚「{entity_name}」的获取方式，你可以告诉我吗？"
    
    if "什么属性" in message_lower or "属性是多少" in message_lower or "数值" in message_lower:
        attrs = [f"{k[5:]}: {v}" for k, v in existing_info.items() if k.startswith("attr_")]
        if attrs:
            return f"「{entity_name}」的属性有：{', '.join(attrs)}"
        else:
            return f"「{entity_name}」暂时没有记录属性信息，你可以补充吗？"
    
    if "有什么技能" in message_lower or "技能有哪些" in message_lower:
        if "skill" in existing_info:
            skill = existing_info["skill"]
            return f"「{entity_name}」拥有技能「{skill.get('name', '未知')}」：{skill.get('description', '')}"
    
    return None

def format_existing_info(info: Dict) -> str:
    """格式化现有信息"""
    if not info:
        return "暂无记录"
    
    parts = []
    for k, v in info.items():
        if k == "acquisition":
            parts.append(f"• 获取方式：{v}")
        elif k.startswith("attr_"):
            parts.append(f"• {k[5:]}：{v}")
        elif k == "skill":
            parts.append(f"• 技能：{v.get('name', '未知')}")
        elif k == "note":
            parts.append(f"• 备注：{v}")
    
    return "\n".join(parts) if parts else "暂无记录"

def suggest_next_question(info: Dict) -> str:
    """根据已有信息建议下一步"""
    if "acquisition" not in info:
        return "需要补充获取方式吗？"
    if not any(k.startswith("attr_") for k in info):
        return "需要补充属性数值吗？"
    if "skill" not in info:
        return "需要补充技能信息吗？"
    return "还有什么需要补充的吗？"

def extract_correction(message: str) -> Dict:
    """提取纠正信息"""
    correction = {}
    
    # 尝试提取纠正的内容
    match = re.search(r'(?:不是|应该是|更正为)[\s]*([^，。]*)', message)
    if match:
        correction["corrected"] = match.group(1)
    
    return correction