import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse

def save_json(data: List[Dict], filename: str) -> str:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        # Replace dots and other invalid filename characters with underscores
        domain = domain.replace('.', '_').replace('-', '_')
        return domain
    except:
        return "unknown"

def generate_timestamped_filename(prefix: str = "dataset", website: str = None, extension: str = "json") -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if website:
        domain = extract_domain(website)
        return f"{prefix}_{domain}_{timestamp}.{extension}"
    else:
        return f"{prefix}_{timestamp}.{extension}"

def print_dataset_stats(data: List[Dict], title: str = "Dataset Statistics"):
    if not data:
        print(f"{title}: No data")
        return

    labels = [row.get('label', row.get('is_best', 0)) for row in data]
    pos_count = sum(labels)
    neg_count = len(labels) - pos_count

    selector_types = {}
    for row in data:
        st = row.get('selector_type', 'unknown')
        selector_types[st] = selector_types.get(st, 0) + 1

    print(f"\n{title}:")
    print(f"  • Total samples: {len(data)}")
    print(f"  • Positive labels: {pos_count}")
    print(f"  • Negative labels: {neg_count}")
    print(f"  • Selector types: {selector_types}")

    if data and 'features' in data[0]:
        avg_length = sum(row['features'].get('selector_length', 0) for row in data) / len(data)
        print(f"  • Average selector length: {avg_length:.1f}")

def validate_url(url: str) -> bool:
    if not url or len(url.strip()) == 0:
        return False
    url = url.strip()
    return url.startswith('http://') or url.startswith('https://')

def validate_css_selector(selector: str) -> bool:
    if not selector or len(selector.strip()) == 0:
        return False
    selector = selector.strip()
    dangerous_patterns = ['<', 'javascript:', 'onerror=', 'onclick=', 'onload=']
    for pattern in dangerous_patterns:
        if pattern in selector.lower():
            return False
    return True