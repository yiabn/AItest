# app/services/test_point_generator.py
import re
from typing import List, Dict, Any, Optional
from loguru import logger
from app.models.response import TestPoint, EntityInfo

class TestPointGenerator:
    """增强版测试点生成器，支持结构化数据和复杂规则"""

    def __init__(self):
        # 原有的简单规则可以保留，但我们将优先处理结构化数据
        self.rules = [
            # 结构化数据规则（优先）
            {"name": "伤害等级验证", "handler": self._gen_damage_level_points},
            {"name": "套装加成验证", "handler": self._gen_set_bonus_points},
            {"name": "评分条件验证", "handler": self._gen_score_condition_points},
            {"name": "技能效果验证", "handler": self._gen_skill_effect_points},
            # 原有的简单规则作为备选（可保留或移除）
            {"name": "技能伤害验证", "condition": lambda e: e.type == "skill" and "伤害" in str(e.attributes), "handler": self._gen_skill_damage},
            {"name": "技能冷却验证", "condition": lambda e: e.type == "skill" and "冷却" in str(e.attributes), "handler": self._gen_skill_cooldown},
            {"name": "印记生成周期", "condition": lambda e: "印记" in str(e.attributes) and "凝聚" in str(e.attributes), "handler": self._gen_mark_rule},
            {"name": "幻兽技能归属", "condition": lambda e: e.type == "pet", "handler": self._gen_pet_skills},
        ]

    def generate(self, entities: List[EntityInfo], task_id: str) -> List[TestPoint]:
        """为实体列表生成测试点，关联到指定的任务ID"""
        points = []
        logger.info(f"实体数量: {len(entities)}")
        for e in entities:
            logger.info(f"实体 {e.name} 的 attributes: {e.attributes}")
        for entity in entities:
            logger.debug(f"为实体 {entity.name}({entity.type}) 生成测试点")
            # 优先尝试结构化规则（无条件，直接尝试）
            for rule in self.rules:
                # 如果规则定义了 condition，则先判断
                if "condition" in rule:
                    if rule["condition"](entity):
                        try:
                            point = rule["handler"](entity)
                            if point:
                                if isinstance(point, list):
                                    for p in point:
                                        p.entity_id = entity.id
                                        p.task_id = task_id
                                        points.append(p)
                                else:
                                    point.entity_id = entity.id
                                    point.task_id = task_id
                                    points.append(point)
                        except Exception as e:
                            logger.error(f"生成测试点失败（规则 {rule['name']}）: {e}")
                else:
                    # 无条件规则，直接调用（handler 内部应自己判断是否适用）
                    try:
                        result = rule["handler"](entity)
                        if result:
                            if isinstance(result, list):
                                for p in result:
                                    p.entity_id = entity.id
                                    p.task_id = task_id
                                    points.append(p)
                            else:
                                result.entity_id = entity.id
                                result.task_id = task_id
                                points.append(result)
                    except Exception as e:
                        logger.error(f"生成测试点失败（规则 {rule['name']}）: {e}")

        # 去重（基于描述）
        seen = set()
        unique = []
        for p in points:
            if p.description not in seen:
                seen.add(p.description)
                unique.append(p)
        logger.info(f"共生成 {len(unique)} 个测试点")
        return unique

    # ========== 结构化数据规则 ==========

    def _gen_damage_level_points(self, entity: EntityInfo) -> List[TestPoint]:
        """根据伤害等级数据生成测试点"""
        points = []
        damage_levels = entity.attributes.get("damage_levels")
        if not damage_levels or not isinstance(damage_levels, list):
            return points

        for level_info in damage_levels:
            level = level_info.get("level")
            damage = level_info.get("damage")
            if damage:
                points.append(TestPoint(
                    category="数值验证",
                    description=f"验证技能「{entity.name}」Lv.{level} 的伤害系数是否为 {damage}%",
                    expected_result=f"Lv.{level} 技能造成 {damage}% 伤害",
                    test_steps=f"1. 确保技能等级为 Lv.{level}；2. 使用技能攻击目标；3. 记录伤害值；4. 计算是否符合 {damage}% 系数",
                    priority="high",
                    confidence=0.9
                ))
            fixed_damage_cap = level_info.get("fixed_damage_cap")
            if fixed_damage_cap:
                points.append(TestPoint(
                    category="数值验证",
                    description=f"验证技能「{entity.name}」Lv.{level} 的固定伤害封顶值是否为 {fixed_damage_cap}",
                    expected_result=f"额外固定伤害不超过 {fixed_damage_cap}",
                    test_steps=f"1. 使用技能攻击高防御目标；2. 记录额外固定伤害数值；3. 验证是否 ≤ {fixed_damage_cap}",
                    priority="high",
                    confidence=0.9
                ))
        return points

    def _gen_set_bonus_points(self, entity: EntityInfo) -> List[TestPoint]:
        """根据套装加成数据生成测试点"""
        points = []
        set_bonus = entity.attributes.get("set_bonus")
        if not set_bonus or not isinstance(set_bonus, list):
            return points

        for bonus in set_bonus:
            score = bonus.get("score")
            effects = bonus.get("effects", [])
            for effect in effects:
                desc = effect.get("description", "")
                value = effect.get("value")
                if value:
                    points.append(TestPoint(
                        category="机制验证",
                        description=f"验证幻兽「{entity.name}」评分达 {score} 时，{desc} 是否正确生效",
                        expected_result=f"获得 {desc}",
                        test_steps=f"1. 将幻兽评分提升至 {score}；2. 检查属性面板或战斗效果；3. 确认 {desc} 已生效",
                        priority="medium",
                        confidence=0.8
                    ))
        return points

    def _gen_score_condition_points(self, entity: EntityInfo) -> List[TestPoint]:
        """根据评分条件生成测试点"""
        points = []
        score_req = entity.attributes.get("score_requirement")
        if not score_req:
            return points

        # 例如：某些技能需要评分达到一定值才能解锁
        desc = score_req.get("description", "")
        required = score_req.get("required")
        if required and desc:
            points.append(TestPoint(
                category="条件验证",
                description=f"验证「{entity.name}」的 {desc} 是否在评分达 {required} 时生效",
                expected_result=f"评分 ≥ {required} 时，{desc} 生效",
                test_steps=f"1. 将幻兽评分调整至 {required-100}；2. 验证 {desc} 是否未生效；3. 将评分提升至 {required}；4. 再次验证是否生效",
                priority="high",
                confidence=0.9
            ))
        return points

    def _gen_skill_effect_points(self, entity: EntityInfo) -> List[TestPoint]:
        """根据技能效果描述生成测试点"""
        points = []
        effects = entity.attributes.get("effects", [])
        if not effects:
            return points

        for effect in effects:
            effect_type = effect.get("type")
            target = effect.get("target", "")
            value = effect.get("value")
            duration = effect.get("duration")

            if effect_type == "击飞":
                points.append(TestPoint(
                    category="机制验证",
                    description=f"验证技能「{entity.name}」的击飞效果",
                    expected_result="命中目标后将其击飞",
                    test_steps="1. 使用技能攻击可被击飞的目标；2. 观察目标是否被击飞",
                    priority="medium",
                    confidence=0.8
                ))
                if duration:
                    points.append(TestPoint(
                        category="机制验证",
                        description=f"验证击飞后的眩晕持续时间是否为 {duration} 秒",
                        expected_result=f"目标眩晕 {duration} 秒",
                        test_steps=f"1. 使用技能击飞目标；2. 计时目标从击飞落地到恢复行动的时间；3. 验证是否为 {duration} 秒",
                        priority="high",
                        confidence=0.9
                    ))
            elif effect_type == "减伤" and value and duration:
                points.append(TestPoint(
                    category="数值验证",
                    description=f"验证「{entity.name}」的减伤效果是否为 {value}% 持续 {duration} 秒",
                    expected_result=f"获得 {value}% 减伤，持续 {duration} 秒",
                    test_steps=f"1. 触发减伤效果；2. 记录受到的伤害；3. 计算减伤比例；4. 计时效果持续时间",
                    priority="high",
                    confidence=0.9
                ))
            elif effect_type == "回复" and value:
                points.append(TestPoint(
                    category="数值验证",
                    description=f"验证「{entity.name}」的生命回复效果是否为 {value}%",
                    expected_result=f"回复 {value}% 生命值",
                    test_steps=f"1. 记录当前生命值；2. 触发回复效果；3. 计算回复量是否匹配 {value}%",
                    priority="high",
                    confidence=0.9
                ))
            # 可以继续添加更多效果类型
        return points

    # ========== 原有的简单规则（保留作为备选）==========

    def _gen_skill_damage(self, entity: EntityInfo) -> Optional[TestPoint]:
        desc = str(entity.attributes)
        match = re.search(r'(\d+)%', desc)
        if match:
            damage = match.group(1)
            return TestPoint(
                category="数值验证",
                description=f"验证技能「{entity.name}」的伤害系数是否为 {damage}%",
                expected_result=f"技能对目标造成 {damage}% 魔法伤害",
                test_steps=f"1. 使用技能攻击目标；2. 记录伤害值；3. 计算是否符合 {damage}% 系数",
                priority="high",
                confidence=0.8
            )
        return None

    def _gen_skill_cooldown(self, entity: EntityInfo) -> Optional[TestPoint]:
        desc = str(entity.attributes)
        match = re.search(r'冷却[时间]?[：:]\s*(\d+)', desc)
        if match:
            cd = match.group(1)
            return TestPoint(
                category="数值验证",
                description=f"验证技能「{entity.name}」的冷却时间是否为 {cd} 秒",
                expected_result=f"技能使用后需等待 {cd} 秒才能再次使用",
                test_steps=f"1. 使用技能；2. 记录冷却时间；3. 验证是否为 {cd} 秒",
                priority="high",
                confidence=0.8
            )
        return None

    def _gen_mark_rule(self, entity: EntityInfo) -> Optional[TestPoint]:
        desc = str(entity.attributes)
        match = re.search(r'(\w+印记)每(\d+)秒凝聚(\d+)枚', desc)
        if match:
            mark, sec, count = match.groups()
            return TestPoint(
                category="机制验证",
                description=f"验证{mark}生成周期是否为每{sec}秒凝聚{count}枚",
                expected_result=f"每{sec}秒自动凝聚{count}枚{mark}",
                test_steps=f"1. 观察{mark}数量；2. 计时{sec}秒；3. 检查是否增加{count}枚",
                priority="high",
                confidence=0.9
            )
        match = re.search(r'最多持有(\d+)枚', desc)
        if match:
            max_count = match.group(1)
            return TestPoint(
                category="机制验证",
                description=f"验证{entity.name}最多持有{max_count}枚",
                expected_result=f"当已有{max_count}枚时，不再增加",
                test_steps=f"1. 累积到{max_count}枚；2. 尝试再次获得；3. 验证数量不增加",
                priority="high",
                confidence=0.9
            )
        return None

    def _gen_pet_skills(self, entity: EntityInfo) -> Optional[TestPoint]:
        skills = entity.attributes.get("skills", [])
        if skills and isinstance(skills, list):
            skill_names = ", ".join(skills[:3])
            return TestPoint(
                category="关系验证",
                description=f"验证幻兽「{entity.name}」是否拥有技能：{skill_names}",
                expected_result=f"幻兽应能使用这些技能",
                test_steps=f"1. 查看幻兽技能列表；2. 确认包含{skill_names}",
                priority="medium",
                confidence=0.7
            )
        return None