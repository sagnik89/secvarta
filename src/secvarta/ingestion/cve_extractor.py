import re

CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)


def extract_cves(*texts):
    """
    Extract unique CVE identifiers from one or more text strings.
    """
    cves = set()

    for text in texts:
        if not text:
            continue

        matches = CVE_PATTERN.findall(text)
        cves.update(cve.upper() for cve in matches)

    return sorted(cves)
