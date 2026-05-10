from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Cookie
from datetime import datetime
from typing import Any, Literal, Mapping, Sequence
from urllib.parse import urlencode
import sqlalchemy
import os


# Define the router before using it
router = APIRouter()
templates = Jinja2Templates(directory="templates")

_PAGE_SIZE = 20

_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pass@db:5432/postgres_dev")
_engine = sqlalchemy.create_engine(_DATABASE_URL) if _DATABASE_URL else None


def _parse_created_at_iso(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    s = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _peek_has_older_than(cursor_created_at: datetime | None, cursor_id_tweets: int) -> bool:
    if _engine is None:
        return False
    stmt = sqlalchemy.text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM tweets AS t
            WHERE (t.created_at, t.id_tweets) < (:cursor_created_at, :cursor_id_tweets)
        ) AS e
        """
    )
    with _engine.connect() as conn:
        row = conn.execute(
            stmt,
            {"cursor_created_at": cursor_created_at, "cursor_id_tweets": cursor_id_tweets},
        ).one()
        return bool(row["e"])


def fetch_tweets_first_page(*, limit_plus_one: int) -> Sequence[Mapping[str, Any]]:
    if _engine is None:
        return []

    stmt = sqlalchemy.text(
        """
        SELECT
            t.id_tweets AS id_tweets,
            t.id_users AS id_users,
            t.created_at AS created_at,
            t.text AS text,
            u.name AS name,
            u.screen_name AS screen_name
        FROM tweets AS t
        JOIN users AS u USING (id_users)
        ORDER BY t.created_at DESC NULLS LAST, t.id_tweets DESC
        LIMIT :limit_plus_one
        """
    )

    with _engine.connect() as conn:
        return conn.execute(stmt, {"limit_plus_one": limit_plus_one}).mappings().all()


def fetch_tweets_older_than(
    *,
    cursor_created_at: datetime | None,
    cursor_id_tweets: int,
    limit_plus_one: int,
) -> Sequence[Mapping[str, Any]]:
    if _engine is None:
        return []

    stmt = sqlalchemy.text(
        """
        SELECT
            t.id_tweets AS id_tweets,
            t.id_users AS id_users,
            t.created_at AS created_at,
            t.text AS text,
            u.name AS name,
            u.screen_name AS screen_name
        FROM tweets AS t
        JOIN users AS u USING (id_users)
        WHERE (t.created_at, t.id_tweets) < (:cursor_created_at, :cursor_id_tweets)
        ORDER BY t.created_at DESC NULLS LAST, t.id_tweets DESC
        LIMIT :limit_plus_one
        """
    )

    with _engine.connect() as conn:
        return conn.execute(
            stmt,
            {
                "cursor_created_at": cursor_created_at,
                "cursor_id_tweets": cursor_id_tweets,
                "limit_plus_one": limit_plus_one,
            },
        ).mappings().all()


def fetch_tweets_newer_than(
    *,
    cursor_created_at: datetime | None,
    cursor_id_tweets: int,
    limit_plus_one: int,
) -> Sequence[Mapping[str, Any]]:
    """
    Rows strictly newer than the cursor, returned oldest→newest, then reversed
    so the template renders newest-first.
    """
    if _engine is None:
        return []

    stmt = sqlalchemy.text(
        """
        SELECT
            t.id_tweets AS id_tweets,
            t.id_users AS id_users,
            t.created_at AS created_at,
            t.text AS text,
            u.name AS name,
            u.screen_name AS screen_name
        FROM tweets AS t
        JOIN users AS u USING (id_users)
        WHERE (t.created_at, t.id_tweets) > (:cursor_created_at, :cursor_id_tweets)
        ORDER BY t.created_at ASC NULLS LAST, t.id_tweets ASC
        LIMIT :limit_plus_one
        """
    )

    with _engine.connect() as conn:
        rows = conn.execute(
            stmt,
            {
                "cursor_created_at": cursor_created_at,
                "cursor_id_tweets": cursor_id_tweets,
                "limit_plus_one": limit_plus_one,
            },
        ).mappings().all()

    return list(reversed(rows))


def build_timeline_page(
    *,
    before_created_at_param: str | None,
    before_id_param: int | None,
    after_created_at_param: str | None,
    after_id_param: int | None,
) -> tuple[list[Mapping[str, Any]], dict[str, Any] | None]:
    """
    Seek pagination keyed by (created_at, id_tweets). Avoids OFFSET; pairs with idx_tweets_timeline.
    """
    if _engine is None:
        return [], None

    limit_plus_one = _PAGE_SIZE + 1
    before_dt = _parse_created_at_iso(before_created_at_param)
    after_dt = _parse_created_at_iso(after_created_at_param)

    mode: Literal["first", "older", "newer"]
    if before_dt is not None and before_id_param is not None:
        mode = "newer"
        rows = fetch_tweets_newer_than(
            cursor_created_at=before_dt,
            cursor_id_tweets=before_id_param,
            limit_plus_one=limit_plus_one,
        )
    elif after_dt is not None and after_id_param is not None:
        mode = "older"
        rows = fetch_tweets_older_than(
            cursor_created_at=after_dt,
            cursor_id_tweets=after_id_param,
            limit_plus_one=limit_plus_one,
        )
    else:
        mode = "first"
        rows = fetch_tweets_first_page(limit_plus_one=limit_plus_one)

    has_more_this_direction = len(rows) > _PAGE_SIZE
    page_rows = list(rows[:_PAGE_SIZE])

    if not page_rows:
        return [], None

    first = page_rows[0]
    last = page_rows[-1]
    fc = first["created_at"]
    lc = last["created_at"]
    fid = int(first["id_tweets"])
    lid = int(last["id_tweets"])

    fc_iso = fc.isoformat() if isinstance(fc, datetime) else ""
    lc_iso = lc.isoformat() if isinstance(fc, datetime) else ""

    if mode in ("first", "older"):
        has_older = has_more_this_direction
    else:
        has_older = _peek_has_older_than(lc, lid)

    if mode == "first":
        has_newer = False
    elif mode == "older":
        has_newer = True
    else:
        has_newer = has_more_this_direction

    newer_href = "/?" + urlencode({"before_created_at": fc_iso, "before_id": fid})
    older_href = "/?" + urlencode({"after_created_at": lc_iso, "after_id": lid})

    pager = {
        "has_newer": has_newer and bool(fc_iso),
        "has_older": has_older and bool(lc_iso),
        "newer_href": newer_href,
        "older_href": older_href,
    }
    return page_rows, pager

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
async def read_root(
    request: Request,
    before_created_at: str | None = Query(None),
    before_id: int | None = Query(None),
    after_created_at: str | None = Query(None),
    after_id: int | None = Query(None),
):
    """Home timeline: 20 messages per page, newest first, keyset pagination."""
    username = logged_in_user(request)
    tweets, pager = build_timeline_page(
        before_created_at_param=before_created_at,
        before_id_param=before_id,
        after_created_at_param=after_created_at,
        after_id_param=after_id,
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "username": username, "tweets": tweets, "pager": pager},
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
