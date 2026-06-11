# Setup Instructions
1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows).
4. Install: `pip install -r requirements.txt`
5. Run: `uvicorn app.main:app --reload --port 8200`
6. Reinstall: `pip freeze > requirements.txt`