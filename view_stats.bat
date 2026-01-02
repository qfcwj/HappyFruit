@echo off
echo [1/3] Activating Virtual Environment...
call .venv\Scripts\activate

echo [2/3] Processing Logs (Updating Data)...
.venv\Scripts\python.exe src\process_logs.py

echo [3/3] Launching Streamlit Dashboard...
.venv\Scripts\python.exe -m streamlit run src\app_stats.py

pause