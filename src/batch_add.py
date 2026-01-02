import json
import os
import random
import datetime
import time

# --- 这里是你的工作区，请在这里填写要补录的内容 ---
# 格式: ( "YYYY-MM-DD HH:MM", "YYYY-MM-DD HH:MM", "日志内容" )
# 脚本会自动在 Start 和 End 之间生成一个随机时间

ENTRIES_TO_ADD = [
    # 示例 1: 补录上周五读的论文
    (
        "2026-01-01 11:00", "2026-01-01 12:00", 
        ["## 工作\n @量子计算\n “终于把中文宣传稿，arxiv， 代码开源都搞完了，烦”",
         "## 想法\n“arxiv-latex-cleaner 真好用啊，节省了不少时间……要是没有大模型好像都不知道怎么做事情了”"]
    ),
    (
        "2026-01-01 12:00", "2026-01-01 16:00", 
        ["## 生活\n ### 睡觉\n “躺下睡大觉，真开心！”",
         "## 生活\n ### 做饭\n “清水涮肉涮菜+油泼辣子调蘸碟，居然非常好吃，以后可以常做”",
         "## 学习 工作\n ### 写代码\n @和计算机打交道 \n “尝试制作我的 Happy Fruit 工具。\n wzy 说如果大模型写代码反复出错，他会去自己阅读、找相应包的使用文档，而不是坚持和大模型聊天。\n很有道理。我本来也是这么想的，但是不够坚决，好像总把大模型放在导师的位置上，把自己认为是学生。\n但实际上，我才是项目经理和负责人，大模型只是我手底下一个提建议的。用大模型工作我需要更加明确自己的主体性。”"]
    )
    # 可以在这里继续添加...
]

# --------------------------------------------------------
# 下面是执行逻辑，不需要修改
# --------------------------------------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")
LOG_FILE = os.path.join(DATA_DIR, "daily_log.jsonl")

def random_timestamp(start_str, end_str):
    """在两个时间字符串范围内生成随机时间戳"""
    fmt = "%Y-%m-%d %H:%M"
    try:
        start_dt = datetime.datetime.strptime(start_str, fmt)
        end_dt = datetime.datetime.strptime(end_str, fmt)
    except ValueError:
        # 尝试只写日期的情况
        fmt_date = "%Y-%m-%d"
        start_dt = datetime.datetime.strptime(start_str, fmt_date)
        # 如果只写日期，结束时间默认是当天的最后一秒
        end_dt = datetime.datetime.strptime(end_str, fmt_date) + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

    # 计算总秒数差
    delta = end_dt - start_dt
    int_delta = int(delta.total_seconds())
    
    if int_delta <= 0:
        return start_str + ":00"

    random_second = random.randint(0, int_delta)
    random_dt = start_dt + datetime.timedelta(seconds=random_second)
    
    return random_dt.strftime("%Y-%m-%d %H:%M:%S")

def run_batch_add():
    if not ENTRIES_TO_ADD:
        print("没有要添加的条目。请编辑脚本中的 ENTRIES_TO_ADD 列表。")
        return

    print(f"准备添加 {len(ENTRIES_TO_ADD)} 条记录...")
    
    success_count = 0
    
    # 确保数据目录存在
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for start_t, end_t, contents in ENTRIES_TO_ADD:
            for content in contents:
                # 生成随机时间
                final_ts = random_timestamp(start_t, end_t)
                
                # 构建 JSON
                entry = {
                    "timestamp": final_ts,
                    "raw_content": content.strip()
                }
                
                # 写入
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[新增] {final_ts} | {content[:30]}...")
                success_count += 1

    print("-" * 30)
    print(f"成功补录 {success_count} 条记录！")

if __name__ == "__main__":
    run_batch_add()