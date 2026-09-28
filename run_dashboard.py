import sys
import os
import webbrowser
import time
import threading
import uvicorn

def open_browser():
    time.sleep(1.5)
    print("🚀 Opening Dashboard in your default browser at http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

def main():
    print("=" * 65)
    print(" GURGAON REAL ESTATE ANALYTICS & RECOMMENDATION DASHBOARD ")
    print("=" * 65)
    print("Starting FastAPI Application Server on http://127.0.0.1:8000 ...")

    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
