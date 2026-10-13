import feedparser


def parse_xml(xml_text):
    d = feedparser.parse(xml_text)
    return d
