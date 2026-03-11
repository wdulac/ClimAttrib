from app_platform.shared.config import URL_PREFIX, URL_PREFIX_DASH

def asset_url(path: str) -> str:
    return f"{URL_PREFIX}/assets/{path.lstrip('/')}"

def page_url(path: str) -> str:
    return f"{URL_PREFIX}/{path.lstrip('/')}"