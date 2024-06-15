@echo off
cd /d "%~dp0"  # Change to the directory where the batch file is located
call .\.venv\Scripts\activate  # Activate your virtual environment
docker-compose up -d  # Start Docker containers in detached mode
python -m celery -A djangoProject worker --pool=eventlet --loglevel=INFO
pause  # Keeps the window open after execution
