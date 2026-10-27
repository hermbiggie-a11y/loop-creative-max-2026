@echo off
set UV_CACHE_DIR=%~dp0.uv-cache
set UV_PYTHON_INSTALL_DIR=%~dp0.uv-python
cd /d "%~dp0"
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv\Scripts\python.exe chatterbox-tts
