import json
import os
import sys

# 确保能导入同级目录的 parser
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from parser import LogParser

# 定义路径
BASE_DIR = os.path.dirname(current_dir) # HappyFruit 根目录
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "daily_log.jsonl")
OUTPUT_FILE = os.path.join(DATA_DIR, "parsed_logs.jsonl")

def process_all_logs():
    print(f"开始处理日志...")
    print(f"读取: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print("错误：找不到原始日志文件。请先去记录几条数据！")
        return

    parser = LogParser()
    processed_count = 0
    
    # 读取所有原始数据
    raw_entries = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    raw_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"警告：跳过一行无法解析的 JSON: {line}")

    # 解析并覆盖写入
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for entry in raw_entries:
            timestamp = entry.get("timestamp", "")
            raw_content = entry.get("raw_content", "")
            
            # 这里的 parsed_entries 是一个列表！
            parsed_entries = parser.parse(raw_content, timestamp)
            
            # 遍历列表，写入多行
            for item in parsed_entries:
                f_out.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
                processed_count += 1

    print(f"处理完成！")
    print(f"共解析 {processed_count} 条记录。")
    print(f"结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_all_logs()