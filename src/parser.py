import re
import itertools
from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class LogEntry:
    timestamp: str            # 时间 (作为唯一ID)
    raw_content: str          # 原始输入
    
    category: Optional[str]   # 单个类别
    action: Optional[str]     # 单个动作
    domain: Optional[str]     # 单个领域
    
    reference: Optional[str]  # 参考材料
    thoughts: Optional[str]   # 碎碎念

    def to_dict(self):
        return asdict(self)

class LogParser:
    def __init__(self):
        flags = re.MULTILINE
        
        # --- 核心修复 ---
        # 1. ## 类别
        # (?![#]) 意思是：## 后面紧跟着的字符，不能是 #
        # 这样就能把 ## 和 ### 彻底分开了
        self.re_category = re.compile(r'^\s*##(?![#])\s*(.+)$', flags)
        
        # 2. ### 动作
        self.re_action = re.compile(r'^\s*###\s*(.+)$', flags)
        
        # 3. @ 领域
        self.re_domain = re.compile(r'^\s*@\s*(.+)$', flags)
        
        # 4. $ 参考材料 $
        self.re_ref_wrapped = re.compile(r'\$(.*?)\$')
        
        # 5. “碎碎念”
        self.re_note = re.compile(r'[“"”](.*?)[”"“]', re.DOTALL)

    def parse(self, raw_text: str, timestamp: str) -> List[LogEntry]:
        if not raw_text:
            return []
        
        text_process = raw_text.strip()

        # 1. 提取所有类别 (List)
        cat_list = []
        for m in self.re_category.findall(text_process):
            # 处理一行多个标签：## 学习 工作
            cat_list.extend(m.split())
        cat_list = list(set(cat_list)) # 去重
        if not cat_list: cat_list = [None]

        # 2. 提取动作 (单数)
        action = None
        match = self.re_action.search(text_process)
        if match: 
            action = match.group(1).strip()

        # 3. 提取所有领域 (List)
        dom_list = []
        for m in self.re_domain.findall(text_process):
            dom_list.extend(m.split())
        dom_list = list(set(dom_list))
        if not dom_list: dom_list = [None]

        # 4. 提取资源 (单数)
        reference = None
        match = self.re_ref_wrapped.search(text_process)
        if match: reference = match.group(1).strip()

        # 5. 提取碎碎念
        thoughts = None
        match = self.re_note.search(text_process)
        if match: thoughts = match.group(1).strip()

        # === 生成笛卡尔积 ===
        # 修正：动作(Action)通常是唯一的，所以我们只对 (Category x Domain) 做乘积
        entries = []
        
        for cat, dom in itertools.product(cat_list, dom_list):
            entry = LogEntry(
                timestamp=timestamp,
                raw_content=raw_text,
                category=cat,
                action=action, # 动作共享
                domain=dom,
                reference=reference, # 资源共享
                thoughts=thoughts    # 碎碎念共享
            )
            entries.append(entry)
            
        return entries

# === 自测代码 ===
if __name__ == "__main__":
    parser = LogParser()
    
    # 模拟那个会“打架”的测试用例
    txt = """
## 工作 学习
### 写代码
@ 统计 心理学
$PyQt$
"""
    timestamp = "2026-01-01"
    
    results = parser.parse(txt, timestamp)
    print(f"原始记录 1 条，拆分成了 {len(results)} 条：")
    for r in results:
        print(f"类别:[{r.category}] | 动作:[{r.action}] | 领域:[{r.domain}]")