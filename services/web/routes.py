from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Cookie

# Define the router before using it
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def read_root(request: Request):
    """Returns the HTML content for the home page"""
    return {"hello": "world"}