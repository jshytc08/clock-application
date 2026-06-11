from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import endpoints  # 1. Import your endpoints module

app = FastAPI()

# 2. Include the router
app.include_router(endpoints.router, prefix="/api")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Using the corrected syntax from the previous step
    return templates.TemplateResponse(request=request, name="index.html", context={})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8200, reload=True)