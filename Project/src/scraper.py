import logging
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

IMPORTANT_TAGS = ["button", "input", "textarea", "select", "a"]
TEXT_CONTENT_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "label", "span", "strong", "em", "div"]

MODE_SELECTORS = {
    "interactive": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"]',
    "text": 'h1, h2, h3, h4, h5, h6, label, p[role="heading"], span[role="heading"], strong, em, div[role="heading"]',
    "all": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"], h1, h2, h3, h4, h5, h6, label, p, span, strong, em, div[role="article"]'
}

# Creates a CSS selector for a web element
def generate_css_selector(element_handle):
    try:
        return element_handle.evaluate(r'''el => {
            if (el.id) return '#' + el.id;
            if (el.className) {
                const firstClass = String(el.className).trim().split(/\s+/)[0];
                if (firstClass && /^[a-zA-Z_][a-zA-Z0-9_-]*$/.test(firstClass)) {
                    return '.' + firstClass;
                }
            }
            return el.tagName.toLowerCase();
        }''')
    except:
        return None

# Creates an XPath selector for a web element
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

# Generates a locator based on ARIA role and name
def get_role_based_locator(element_handle):
    try:
        role = element_handle.get_attribute('role') or ''
        name = element_handle.get_attribute('aria-label') or element_handle.inner_text().strip()[:50] or ''
        if role and name:
            return f"getByRole('{role}', {{ name: '{name}' }})"
        return None
    except:
        return None

# Generates a locator using test IDs
def get_test_id_locator(element_handle):
    test_id = element_handle.get_attribute('data-testid') or element_handle.get_attribute('data-test') or ''
    if test_id:
        return f"getByTestId('{test_id}')"
    return None

# Generates a locator based on visible text
def get_text_based_locator(element_handle):
    try:
        text = element_handle.inner_text(timeout=2000).strip()[:50]
        if text:
            return f"getByText('{text}')"
    except:
        pass
    return None

# Scrapes elements from a webpage using Playwright
def extract_elements(url: str, mode: str = "all", custom_selector: str = None, headless: bool = True) -> List[Dict]:
    if custom_selector:
        selector = custom_selector
        mode_to_use = "custom"
    elif mode not in MODE_SELECTORS:
        raise ValueError(f"Invalid mode. Choose from: {', '.join(MODE_SELECTORS.keys())}")
    else:
        selector = MODE_SELECTORS[mode]
        mode_to_use = mode

    try:
        with sync_playwright() as p:
            print(f"   [Browser] Launching browser (headless={headless})...")
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            page = browser.new_page()

            # Set longer timeouts for complex pages
            page.set_default_timeout(90000)  # 90 seconds
            page.set_default_navigation_timeout(90000)

            try:
                print(f"   [Browser] Navigating to {url}...")
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    print("   [Browser] Page loaded with networkidle")
                except PlaywrightTimeoutError:
                    print("   [Browser] Networkidle timeout, trying domcontentloaded...")
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    print("   [Browser] Page loaded with domcontentloaded")

                print("   [Browser] Waiting for dynamic content...")
                page.wait_for_timeout(8000)

                title = page.title()
                print(f"   [Browser] Page title: '{title}'")

                url_check = page.url
                print(f"   [Browser] Current URL: {url_check}")

            except PlaywrightTimeoutError:
                raise ValueError(f"Page load timeout after 105 seconds. The website '{url}' took too long to load or has loading issues.")
            except Exception as e:
                raise ValueError(f"Failed to navigate to {url}: {e}")

            try:
                print(f"   [Browser] Extracting elements with selector: {selector[:50]}...")

                MAX_ELEMENTS = 200

                if mode_to_use == "all":
                    interactive_selector = MODE_SELECTORS["interactive"]
                    text_selector = MODE_SELECTORS["text"]

                    print("   [Browser] Processing interactive elements...")
                    try:
                        interactive_elements = page.eval_on_selector_all(
                            interactive_selector,
                            '''els => Array.from(els).slice(0, 100).map(el => ({
                                tag: el.tagName.toLowerCase(),
                                text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                                attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                            }))'''
                        )
                        print(f"   [Browser] Found {len(interactive_elements)} interactive elements")
                    except Exception as e:
                        print(f"   [Browser] Error extracting interactive elements: {e}")
                        interactive_elements = []

                    print("   [Browser] Processing text elements...")
                    try:
                        text_elements = page.eval_on_selector_all(
                            text_selector,
                            '''els => Array.from(els).slice(0, 100).map(el => ({
                                tag: el.tagName.toLowerCase(),
                                text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                                attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                            }))'''
                        )
                        print(f"   [Browser] Found {len(text_elements)} text elements")
                    except Exception as e:
                        print(f"   [Browser] Error extracting text elements: {e}")
                        text_elements = []

                    elements = interactive_elements + text_elements
                else:
                    try:
                        elements = page.eval_on_selector_all(
                            selector,
                            f'''els => Array.from(els).slice(0, {MAX_ELEMENTS}).map(el => ({{
                                tag: el.tagName.toLowerCase(),
                                text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                                attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                            }}))'''
                        )
                        print(f"   [Browser] Found {len(elements)} elements")
                    except Exception as e:
                        print(f"   [Browser] Error extracting elements: {e}")
                        elements = []

                if len(elements) > MAX_ELEMENTS:
                    print(f"   [Browser] Limiting elements from {len(elements)} to {MAX_ELEMENTS}")
                    elements = elements[:MAX_ELEMENTS]

                print(f"   [Browser] Processing {len(elements)} elements...")

            except Exception as e:
                raise ValueError(f"Failed to extract elements from {url}: {e}")

            elements_data = []

            if mode == "all":
                print("   [Browser] Getting handles for interactive elements...")
                try:
                    interactive_handles = page.query_selector_all(interactive_selector)
                    interactive_handles = interactive_handles[:100]
                    print(f"   [Browser] Got {len(interactive_handles)} interactive handles")
                except Exception as e:
                    print(f"   [Browser] Error getting interactive handles: {e}")
                    interactive_handles = []

                print("   [Browser] Getting handles for text elements...")
                try:
                    text_handles = page.query_selector_all(text_selector)
                    text_handles = text_handles[:100]
                    print(f"   [Browser] Got {len(text_handles)} text handles")
                except Exception as e:
                    print(f"   [Browser] Error getting text handles: {e}")
                    text_handles = []

                all_handles = interactive_handles + text_handles
                all_elements = interactive_elements + text_elements

                for idx, elem in enumerate(all_elements):
                    try:
                        if idx >= len(all_handles):
                            continue
                        handle = all_handles[idx]

                        selectors = {}
                        selectors['css'] = generate_css_selector(handle)
                        selectors['xpath'] = generate_xpath(handle)
                        selectors['role_based'] = get_role_based_locator(handle)
                        selectors['test_id'] = get_test_id_locator(handle)
                        selectors['text_based'] = get_text_based_locator(handle)

                        attrs = elem['attributes']
                        if attrs.get("data-testid"):
                            selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                        if attrs.get("id"):
                            selectors["id"] = f'#{attrs["id"]}'
                        if attrs.get("name"):
                            selectors["name"] = f'[name="{attrs["name"]}"]'
                        if attrs.get("aria-label"):
                            selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                        if attrs.get("placeholder"):
                            selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                        text = elem['text']
                        if text:
                            selectors["text"] = f'text="{text}"'
                        if attrs.get("class"):
                            class_selector = "." + ".".join(attrs["class"].split())
                            selectors["class"] = class_selector

                        element_data = {
                            'tag': elem['tag'],
                            'text': elem['text'],
                            'attributes': elem['attributes'],
                            'selectors': selectors
                        }
                        elements_data.append(element_data)

                    except Exception as e:
                        logging.warning(f"Error processing element {idx}: {e}")
                        continue
            else:
                for idx, elem in enumerate(elements):
                    try:
                        handles = page.query_selector_all(selector)
                        if idx >= len(handles):
                            continue
                        handle = handles[idx]

                        selectors = {}
                        selectors['css'] = generate_css_selector(handle)
                        selectors['xpath'] = generate_xpath(handle)
                        selectors['role_based'] = get_role_based_locator(handle)
                        selectors['test_id'] = get_test_id_locator(handle)
                        selectors['text_based'] = get_text_based_locator(handle)

                        attrs = elem['attributes']
                        if attrs.get("data-testid"):
                            selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                        if attrs.get("id"):
                            selectors["id"] = f'#{attrs["id"]}'
                        if attrs.get("name"):
                            selectors["name"] = f'[name="{attrs["name"]}"]'
                        if attrs.get("aria-label"):
                            selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                        if attrs.get("placeholder"):
                            selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                        text = elem['text']
                        if text:
                            selectors["text"] = f'text="{text}"'
                        if attrs.get("class"):
                            class_selector = "." + ".".join(attrs["class"].split())
                            selectors["class"] = class_selector

                        element_data = {
                            'tag': elem['tag'],
                            'text': elem['text'],
                            'attributes': elem['attributes'],
                            'selectors': selectors
                        }
                        elements_data.append(element_data)

                    except Exception as e:
                        logging.warning(f"Error processing element {idx}: {e}")
                        continue

            browser.close()
            return elements_data

    except Exception as e:
        raise ValueError(f"Critical error during extraction: {e}")


# Scrapes elements from an existing Playwright page context without relaunching browser
def extract_elements_from_page(page, mode: str = "all", custom_selector: str = None) -> List[Dict]:
    if custom_selector:
        selector = custom_selector
        mode_to_use = "custom"
    elif mode not in MODE_SELECTORS:
        raise ValueError(f"Invalid mode. Choose from: {', '.join(MODE_SELECTORS.keys())}")
    else:
        selector = MODE_SELECTORS[mode]
        mode_to_use = mode

    try:
        print(f"   [Browser] Using existing page context: {page.url}")
        print("   [Browser] Waiting for dynamic content...")
        page.wait_for_timeout(2000)

        print(f"   [Browser] Extracting elements with selector: {selector[:50]}...")

        MAX_ELEMENTS = 200

        if mode_to_use == "all":
            interactive_selector = MODE_SELECTORS["interactive"]
            text_selector = MODE_SELECTORS["text"]

            print("   [Browser] Processing interactive elements...")
            try:
                interactive_elements = page.eval_on_selector_all(
                    interactive_selector,
                    '''els => Array.from(els).slice(0, 100).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                    }))'''
                )
                print(f"   [Browser] Found {len(interactive_elements)} interactive elements")
            except Exception as e:
                print(f"   [Browser] Error extracting interactive elements: {e}")
                interactive_elements = []

            print("   [Browser] Processing text elements...")
            try:
                text_elements = page.eval_on_selector_all(
                    text_selector,
                    '''els => Array.from(els).slice(0, 100).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                    }))'''
                )
                print(f"   [Browser] Found {len(text_elements)} text elements")
            except Exception as e:
                print(f"   [Browser] Error extracting text elements: {e}")
                text_elements = []

            elements = interactive_elements + text_elements
        else:
            try:
                elements = page.eval_on_selector_all(
                    selector,
                    f'''els => Array.from(els).slice(0, {MAX_ELEMENTS}).map(el => ({{
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))
                    }}))'''
                )
                print(f"   [Browser] Found {len(elements)} elements")
            except Exception as e:
                print(f"   [Browser] Error extracting elements: {e}")
                elements = []

        if len(elements) > MAX_ELEMENTS:
            print(f"   [Browser] Limiting elements from {len(elements)} to {MAX_ELEMENTS}")
            elements = elements[:MAX_ELEMENTS]

        print(f"   [Browser] Processing {len(elements)} elements...")

        elements_data = []

        if mode == "all":
            print("   [Browser] Getting handles for interactive elements...")
            try:
                interactive_handles = page.query_selector_all(interactive_selector)
                interactive_handles = interactive_handles[:100]
                print(f"   [Browser] Got {len(interactive_handles)} interactive handles")
            except Exception as e:
                print(f"   [Browser] Error getting interactive handles: {e}")
                interactive_handles = []

            print("   [Browser] Getting handles for text elements...")
            try:
                text_handles = page.query_selector_all(text_selector)
                text_handles = text_handles[:100]
                print(f"   [Browser] Got {len(text_handles)} text handles")
            except Exception as e:
                print(f"   [Browser] Error getting text handles: {e}")
                text_handles = []

            all_handles = interactive_handles + text_handles
            all_elements = interactive_elements + text_elements

            for idx, elem in enumerate(all_elements):
                try:
                    if idx >= len(all_handles):
                        continue
                    handle = all_handles[idx]

                    selectors = {}
                    selectors['css'] = generate_css_selector(handle)
                    selectors['xpath'] = generate_xpath(handle)
                    selectors['role_based'] = get_role_based_locator(handle)
                    selectors['test_id'] = get_test_id_locator(handle)
                    selectors['text_based'] = get_text_based_locator(handle)

                    attrs = elem['attributes']
                    if attrs.get("data-testid"):
                        selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                    if attrs.get("id"):
                        selectors["id"] = f'#{attrs["id"]}'
                    if attrs.get("name"):
                        selectors["name"] = f'[name="{attrs["name"]}"]'
                    if attrs.get("aria-label"):
                        selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                    if attrs.get("placeholder"):
                        selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                    text = elem['text']
                    if text:
                        selectors["text"] = f'text="{text}"'
                    if attrs.get("class"):
                        class_selector = "." + ".".join(attrs["class"].split())
                        selectors["class"] = class_selector

                    element_data = {
                        'tag': elem['tag'],
                        'text': elem['text'],
                        'attributes': elem['attributes'],
                        'selectors': selectors
                    }
                    elements_data.append(element_data)

                except Exception as e:
                    logging.warning(f"Error processing element {idx}: {e}")
                    continue
        else:
            handles = page.query_selector_all(selector)
            for idx, elem in enumerate(elements):
                try:
                    if idx >= len(handles):
                        continue
                    handle = handles[idx]

                    selectors = {}
                    selectors['css'] = generate_css_selector(handle)
                    selectors['xpath'] = generate_xpath(handle)
                    selectors['role_based'] = get_role_based_locator(handle)
                    selectors['test_id'] = get_test_id_locator(handle)
                    selectors['text_based'] = get_text_based_locator(handle)

                    attrs = elem['attributes']
                    if attrs.get("data-testid"):
                        selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                    if attrs.get("id"):
                        selectors["id"] = f'#{attrs["id"]}'
                    if attrs.get("name"):
                        selectors["name"] = f'[name="{attrs["name"]}"]'
                    if attrs.get("aria-label"):
                        selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                    if attrs.get("placeholder"):
                        selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                    text = elem['text']
                    if text:
                        selectors["text"] = f'text="{text}"'
                    if attrs.get("class"):
                        class_selector = "." + ".".join(attrs["class"].split())
                        selectors["class"] = class_selector

                    element_data = {
                        'tag': elem['tag'],
                        'text': elem['text'],
                        'attributes': elem['attributes'],
                        'selectors': selectors
                    }
                    elements_data.append(element_data)

                except Exception as e:
                    logging.warning(f"Error processing element {idx}: {e}")
                    continue

        return elements_data

    except Exception as e:
        raise ValueError(f"Critical error during extraction from existing page: {e}")