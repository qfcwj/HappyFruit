# data_manager.py
import json
import os
from datetime import datetime

# 获取 data 文件夹的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "daily_log.jsonl")

# 确保 data 文件夹存在
os.makedirs(DATA_DIR, exist_ok=True)

def save_record(raw_text):
    """
    接收原始文本，打上时间戳，直接存入文件。
    不进行解析，解析逻辑留给后续的展示端。
    """
    if not raw_text or not raw_text.strip():
        return

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_content": raw_text.strip(),
        # 预留字段，以后可以在这里扩展解析结果
        "parsed": None 
    }
    
    # encoding='utf-8' 防止中文乱码
    # mode='a' 表示 append (追加模式)
    try:
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        # 如果出错（极少情况），记录到错误日志
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - Error saving: {e}\n")