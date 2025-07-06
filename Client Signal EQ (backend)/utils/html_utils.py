import re
import html

def strip_html(raw_html: str) -> str:
    clean_text = re.sub('<[^<]+?>', '', raw_html or '')
    return html.unescape(clean_text)
