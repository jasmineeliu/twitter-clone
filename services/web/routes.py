from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Cookie
import sqlalchemy
import os

# Define the router before using it
router = APIRouter()
templates = Jinja2Templates(directory="templates")

_DATABASE_URL = "postgresql://postgres:pass@db:5432/postgres_dev"
_engine = sqlalchemy.create_engine(_DATABASE_URL) if _DATABASE_URL else None

def fetch_tweets(limit: int = 50):
    """
    Returns latest tweets as a list of dict-like rows.

    Uses plain SQL (via SQLAlchemy) so it matches your schema.sql table names.
    """
    if _engine is None:
        return []

    stmt = sqlalchemy.text(
        """
        SELECT
            id_tweets,
            id_users,
            tweets.created_at,
            text,
            place_name,
            name,
            screen_name
        FROM tweets JOIN users
        USING (id_users)
        ORDER BY created_at DESC NULLS LAST, id_tweets DESC
        LIMIT :limit
        """
    )

    with _engine.connect() as conn:
        return conn.execute(stmt, {"limit": limit}).mappings().all()

def check_credentials(username: str, password: str) -> str:
    """
    Checks if the provided username and password are valid.

    Args:
    - username (str): The username to check.
    - password (str): The password to check.

    Returns:
    - str: The username if the credentials are valid, otherwise None.
    """
    # FIXME: Add database code to check credentials
    # For now, this is a mock with hardcoded valid credentials
    if username == "Trump" and password == "12345":
        return username
    else:
        return None

def logged_in_user(request: Request) -> str:
    """
    Checks if the user is logged in by checking the cookies.

    Args:
    - request (Request): The current request.

    Returns:
    - str: The username if the user is logged in, otherwise None.
    """
    username = request.cookies.get("username")
    password = request.cookies.get("password")
    # Treat missing/empty cookies as logged out.
    if username and password:
        valid_username = check_credentials(username, password)
        if valid_username is not None:
            return valid_username
    return None

@router.get("/")
async def read_root(request: Request):
    """Returns the HTML content for the home page"""
    username = logged_in_user(request)
    tweets = fetch_tweets(limit=50)
    # print(tweets)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "username": username, "tweets": tweets},
    )

@router.get("/login")
def read_login(request: Request):
    """Returns the HTML content for the login page"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "login.html", {"request": request, "username": username})

@router.post("/login")
def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Returns the HTML content after a login attempt"""
    # Print the username and password to the logs
    print(f"Username: {username}, Password: {password}")
    # Check the credentials
    valid_username = check_credentials(username, password)
    if valid_username is not None:
        # Credentials are valid, set cookies and return the success page
        response = templates.TemplateResponse(request, "login_successful.html", {"request": request, "username": valid_username})
        response.set_cookie("username", username)
        response.set_cookie("password", password)
        return response
    else:
        # Credentials are invalid, return an error page
        return templates.TemplateResponse(request, "login.html", {"request": request, "username": None, "error": "Invalid username or password"})

@router.get("/logout")
def read_logout(request: Request):
    """Returns the HTML content for the logout page and deletes cookies"""
    username = logged_in_user(request)
    response = templates.TemplateResponse(request, "logout.html", {"request": request, "username": None})
    response.delete_cookie("username")
    response.delete_cookie("password")
    return response

@router.get("/create_account")
def read_create_account(request: Request):
    """Returns the HTML content for the create account page"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "create_account.html", {"request": request, "username": username})

@router.post("/create_account")
def post_create_account(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    """Returns the HTML content after a successful account creation"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "account_created.html", {"request": request, "username": username})

@router.get("/create_message")
def read_create_message(request: Request):
    """Returns the HTML content for the create message page"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "create_message.html", {"request": request, "username": username})

@router.post("/create_message")
def post_create_message(request: Request, message: str = Form(...)):
    """Returns the HTML content after a successful message creation"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "message_posted.html", {"request": request, "username": username})

@router.get("/search")
def read_search(request: Request):
    """Returns the HTML content for the search page"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "search.html", {"request": request, "username": username})

@router.post("/search")
def post_search(request: Request, query: str = Form(...)):
    """Returns the HTML content for the search results page"""
    username = logged_in_user(request)
    return templates.TemplateResponse(request, "search_results.html", {"request": request, "username": username})
