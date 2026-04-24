import json
from playwright.sync_api import sync_playwright
from datetime import datetime
import sys
import os

def generate_css_selector(element_handle):
    try:
        return element_handle.evaluate('''el => {
            if (el.id) return '#' + el.id;
            if (el.className) return '.' + el.className.split(' ')[0];
            return el.tagName.toLowerCase();
        }''')
    except:
        return None

def generate_xpath(element_handle):
    try:
        return element_handle.evaluate('''el => {
            let path = [];
            while (el && el.nodeType === 1) {
                let name = el.tagName.toLowerCase();
                let sib = el, pos = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.tagName.toLowerCase() === name) pos++;
                }
                path.unshift(name + (pos > 1 ? '[' + pos + ']' : ''));
                el = el.parentElement;
            }
            return '/' + path.join('/');
        }''')
    except:
        return None

def get_role_based_locator(element_handle):
    try:
        role = element_handle.get_attribute('role') or ''
        name = element_handle.get_attribute('aria-label') or element_handle.inner_text().strip()[:50] or ''
        if role and name:
            return f"getByRole('{role}', {{ name: '{name}' }})"
        return None
    except:
        return None

def get_test_id_locator(element_handle):
    test_id = element_handle.get_attribute('data-testid') or element_handle.get_attribute('data-test') or ''
    if test_id:
        return f"getByTestId('{test_id}')"
    return None

def get_text_based_locator(element_handle):
    try:
        text = element_handle.inner_text(timeout=2000).strip()[:50]
        if text:
            return f"getByText('{text}')"
    except:
        pass
    return None

def is_unique(page, locator_str):
    try:
        count = page.locator(locator_str).count()
        return count == 1
    except:
        return False

def scrape_selectors(url, output_file=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        elements = page.eval_on_selector_all('''button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"], [data-testid], p, span, div[role="article"], label''', '''els => {
            return Array.from(els).map(el => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value])),
                boundingBox: el.getBoundingClientRect().toJSON()
            }));
        }''')
        
        enriched_elements = []
        for idx, elem in enumerate(elements):
            handle = page.query_selector_all(f':nth-match(*, {idx+1})')[0] if elements else None  
            if not handle:
                continue
            
            selectors = {
                'css': generate_css_selector(handle),
                'xpath': generate_xpath(handle),
                'role_based': get_role_based_locator(handle),
                'test_id': get_test_id_locator(handle),
                'text_based': get_text_based_locator(handle),
            }

            selectors = {k: v for k, v in selectors.items() if v}
            for k, v in selectors.items():
                selectors[k] = {'selector': v, 'unique': is_unique(page, v)}
            
            enriched_elements.append({
                'element_id': f'elem_{idx:04d}',
                'tag': elem['tag'],
                'text': elem['text'],
                'attributes': elem['attributes'],
                'boundingBox': elem['boundingBox'],
                'selectors': selectors
            })
        
        browser.close()
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'selectors_{os.path.basename(url)}_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_elements, f, indent=4, ensure_ascii=False)
        
        print(f"Scraped {len(enriched_elements)} elements. Exported to {output_file}")
        return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Scraper.py <URL> [output_file]")
        print("Example: python Scraper.py https://demo.openemr.io/openemr/interface/login/login.php")
        sys.exit(1)
    
    url = sys.argv[1]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"Warning: Added https:// → navigating to: {url}")
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    scrape_selectors(url, output_file)