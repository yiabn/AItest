# backend/utils/term_dict.py
import jieba

# 游戏术语映射：标准化属性名
term_mapping = {
    "skill": {
        "CD": "冷却时间",
        "冷却": "冷却时间",
        "伤害": "伤害倍率",
        "耗蓝": "魔法消耗",
        "施法距离": "释放距离",
        "持续时间": "效果时长"
    },
    "equipment": {
        "攻击": "物理攻击",
        "法攻": "魔法攻击",
        "防御": "物理防御",
        "法防": "魔法防御",
        "攻速": "攻击速度",
        "暴击": "暴击率"
    },
    "pet": {
        "成长": "成长率",
        "资质": "主属性资质",
        "亲密度": "亲密度加成",
        "合体": "合体效果"
    },
    "common": {
        "等级": "等级要求",
        "获取方式": "获取途径"
    }
}

# 游戏专属词典（提升jieba分词精度）
game_dict = [
    "幻兽", "技能专精", "魔石", "神火", "圣器", "魂兽",
    "物攻", "法攻", "暴击率", "冷却时间", "成长率",
    "亡灵巫师", "血族", "战士", "法师", "异能者"
]

def load_custom_dict():
    """加载自定义游戏词典到jieba"""
    # 临时生成词典文件（也可直接加载文件）
    with open("game_custom_dict.txt", "w", encoding="utf-8") as f:
        for word in game_dict:
            f.write(f"{word} 1000\n")  # 1000为权重，越高越优先
    
    jieba.load_userdict("game_custom_dict.txt")
    print("✅ 游戏自定义词典加载完成")

# 初始化加载词典
load_custom_dict()