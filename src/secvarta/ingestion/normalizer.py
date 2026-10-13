def normalize_entry(entry):
    """
    Convert a feedparser entry into standard article format.

    Args:
        entry: A single entry returned by feedparser.

    Returns:
        A dictionary containing normalized article fields.
    """
    return {
        "title": entry.get("title", ""),
        "url": entry.get("link", ""),
        "summary": entry.get("summary", ""),
        "published_at": entry.get("published", ""),
    }
