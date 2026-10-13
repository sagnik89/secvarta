import httpx


def get_url(url):
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.text
