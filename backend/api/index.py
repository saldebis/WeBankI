# Vercel entry point: exposes the FastAPI app from ../main.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app  # noqa: E402,F401