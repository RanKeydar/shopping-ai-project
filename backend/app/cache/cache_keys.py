from fastapi import Request

def items_list_cache_key(request: Request) -> str:
    base = f"items:{request.url.path}"
    if request.url.query:
        return f"{base}?{request.url.query}"
    return base