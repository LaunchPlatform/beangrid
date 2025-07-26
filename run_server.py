#!/usr/bin/env python3
"""
Simple script to run the BeanGrid FastAPI server.
"""
from pathlib import Path

import uvicorn

from beangrid.main import make_app

if __name__ == "__main__":
    app = make_app()
    print("Starting BeanGrid server...")
    print(
        "Using default sample_workbook.yaml (set WORKBOOK_FILE env var to use a different file)"
    )
    print("Visit http://localhost:8000 to view the application")
    print("API documentation available at http://localhost:8000/docs")
    print("Workbook API available at http://localhost:8000/api/v1/workbook")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
