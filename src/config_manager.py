import json
import os

# 定义配置文件路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "hints_config.json")

# 默认配置（如果文件不存在时使用）
DEFAULT_CONFIG = {
    "categories": ["学习", "工作", "游乐", "想法"],
    "actions": ["读论文", "数据处理", "写代码", "看书"],
    "domains": ["统计", "心理学", "数学"]
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """加载配置，如果不存在则创建默认配置"""
        if not os.path.exists(CONFIG_PATH):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG

    def save_config(self, config_data):
        """保存配置到文件"""
        # 确保目录存在
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

    def update_from_entry(self, parsed_entries):
        """
        根据解析出的条目自动更新配置。
        parsed_entries 是 parser.parse 返回的 LogEntry 列表
        """
        changed = False
        
        # 提取当前所有已知项（转为集合方便去重）
        known_cats = set(self.config.get("categories", []))
        known_acts = set(self.config.get("actions", []))
        known_doms = set(self.config.get("domains", []))

        for entry in parsed_entries:
            # 更新类别
            if entry.category and entry.category not in known_cats:
                self.config["categories"].append(entry.category)
                known_cats.add(entry.category)
                changed = True
            
            # 更新动作
            if entry.action and entry.action not in known_acts:
                self.config["actions"].append(entry.action)
                known_acts.add(entry.action)
                changed = True
                
            # 更新领域
            if entry.domain and entry.domain not in known_doms:
                self.config["domains"].append(entry.domain)
                known_doms.add(entry.domain)
                changed = True

        if changed:
            self.save_config(self.config)
            print("配置已自动更新！")

    def get_display_hints(self):
        """生成 GUI 右侧显示的提示文本列表"""
        # 将列表转为字符串，如 "学习 工作 游乐"
        cat_str = " ".join(self.config.get("categories", []))
        act_str = " ".join(self.config.get("actions", []))
        dom_str = " ".join(self.config.get("domains", []))

        return [
            f"## {cat_str}",
            f"### {act_str}",
            f"@ {dom_str}",
            "$$ 可以备注所涉及参考材料以备后用！",
            "“” 留下一句将来的自己也许可以看了会心一笑的话吧"
        ]