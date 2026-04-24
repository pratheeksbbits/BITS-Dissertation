# Import necessary libraries
# sync_playwright for browser automation (synchronous version to avoid asyncio issues in notebooks)
# BeautifulSoup for HTML parsing
# json for outputting data as JSON
# datetime for timestamping output files
# urlparse for extracting domain from URL
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urlparse
import re
import logging

# Import selector ranking engine components
from selector_ranking_engine import rank_selectors_for_elements, DatasetBuilder

# List of HTML tags that are typically interactive UI elements
IMPORTANT_TAGS = ["button", "input", "textarea", "select", "a"]

# List of HTML tags for text content extraction
TEXT_CONTENT_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "label", "span", "strong", "em", "div"]

# Selectors for different modes
MODE_SELECTORS = {
    "interactive": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"]',
    "text": 'h1, h2, h3, h4, h5, h6, label, p[role="heading"], span[role="heading"], strong, em, div[role="heading"]',
    "all": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"], h1, h2, h3, h4, h5, h6, label, p, span, strong, em, div[role="article"]'
}

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

# Function to get the fully rendered HTML content of a webpage using Playwright
# Playwright launches a headless browser, navigates to the URL, waits for network to be idle,
# then retrieves the page content (which includes dynamically loaded elements)
def get_rendered_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Changed to False to visualize the browser
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3000)  # Wait 3 seconds to allow user to see the page
        html = page.content()
        browser.close()
    return html

# Function to determine if an HTML element is interactive
# Checks if the element's tag is in the important tags list,
# or if it has a 'role' attribute set to 'button', or has an 'onclick' attribute
def is_interactive(element):
    if element.name in IMPORTANT_TAGS:
        return True
    if element.get("role") == "button":
        return True
    if element.get("onclick"):
        return True
    return False

# Function to generate various CSS selectors for a given HTML element
# Prioritizes more reliable selectors like data-testid, id, name, etc.
# Also includes text-based selector and class selector (less reliable)
def generate_selectors(el):
    selectors = {}

    # High priority selectors (more specific and reliable)
    if el.get("data-testid"):
        selectors["data-testid"] = f'[data-testid="{el["data-testid"]}"]'

    if el.get("id"):
        selectors["id"] = f'#{el["id"]}'

    if el.get("name"):
        selectors["name"] = f'[name="{el["name"]}"]'

    if el.get("aria-label"):
        selectors["aria-label"] = f'[aria-label="{el["aria-label"]}"]'

    if el.get("placeholder"):
        selectors["placeholder"] = f'[placeholder="{el["placeholder"]}"]'

    # Text selector (Playwright style) - matches visible text
    text = el.get_text(strip=True)
    if text:
        selectors["text"] = f'text="{text}"'

    # Class selector (least reliable, as classes can change)
    if el.get("class"):
        class_selector = "." + ".".join(el["class"])
        selectors["class"] = class_selector

    return selectors

# Function to extract elements from a webpage based on mode
# Mode options: "interactive", "text", "all", or custom CSS selector
# Gets rendered HTML, finds elements matching the selector,
# generates selectors for each, and collects data
def extract_elements(url, mode="all", custom_selector=None):
    """
    Extract elements from a webpage.
    
    Args:
        url: The URL to scrape
        mode: "interactive" (buttons, inputs, links), "text" (headings, labels, paragraphs), 
              "all" (both interactive and text), or provide custom_selector
        custom_selector: Custom CSS selector string (overrides mode if provided)
    """
    # Determine which selector to use
    if custom_selector:
        selector = custom_selector
        mode_name = "custom"
    elif mode not in MODE_SELECTORS:
        print(f"ERROR: Invalid mode. Choose from: {', '.join(MODE_SELECTORS.keys())}")
        return []
    else:
        selector = MODE_SELECTORS[mode]
        mode_name = mode
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                print(f"INFO: Navigating to {url}...")
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)
            except PlaywrightTimeoutError:
                print(f"ERROR: Page load timeout. The website took too long to load (>30s).")
                browser.close()
                return []
            except Exception as e:
                print(f"ERROR: Failed to navigate to {url}")
                print(f"   Details: {str(e)}")
                browser.close()
                return []

            # Get all elements matching the selector
            try:
                elements = page.eval_on_selector_all(selector, '''els => {
                    return Array.from(els).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value])),
                    }));
                }''')
            except Exception as e:
                print(f"ERROR: Invalid CSS selector or selector not found")
                print(f"   Selector: {selector}")
                print(f"   Details: {str(e)}")
                browser.close()
                return []

            elements_data = []
            for idx, elem in enumerate(elements):
                try:
                    # Get handle for the element
                    handles = page.query_selector_all(selector)
                    if idx >= len(handles):
                        continue
                    handle = handles[idx]

                    selectors = {}

                    # Generate comprehensive selectors
                    selectors['css'] = generate_css_selector(handle)
                    selectors['xpath'] = generate_xpath(handle)
                    selectors['role_based'] = get_role_based_locator(handle)
                    selectors['test_id'] = get_test_id_locator(handle)
                    selectors['text_based'] = get_text_based_locator(handle)

                    # Add attribute-based selectors
                    attrs = elem['attributes']
                    if 'data-testid' in attrs:
                        selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                    if 'id' in attrs:
                        selectors["id"] = f'#{attrs["id"]}'
                    if 'name' in attrs:
                        selectors["name"] = f'[name="{attrs["name"]}"]'
                    if 'aria-label' in attrs:
                        selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                    if 'placeholder' in attrs:
                        selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                    if 'class' in attrs:
                        class_selector = "." + ".".join(attrs['class'].split())
                        selectors["class"] = class_selector

                    text = elem['text']
                    if text:
                        selectors["text"] = f'text="{text}"'

                    # Filter out None values
                    selectors = {k: v for k, v in selectors.items() if v is not None}

                    elements_data.append({
                        "tag": elem['tag'],
                        "text": elem['text'],
                        "attributes": elem['attributes'],
                        "selectors": selectors,
                        "extraction_mode": mode_name
                    })
                except Exception as e:
                    # Skip individual elements that fail
                    print(f"WARNING: Failed to process element {idx}. Skipping...")
                    continue

            browser.close()
            return elements_data
    
    except Exception as e:
        print(f"ERROR: Critical error during extraction: {str(e)}")
        return []

# Function to display mode options and get user input
def display_modes():
    print("\n" + "="*60)
    print("SELECTOR EXTRACTION MODES")
    print("="*60)
    print("1. INTERACTIVE - Buttons, inputs, links, and interactive elements")
    print("2. TEXT - Headings, labels, paragraphs, and text content")
    print("3. ALL - Both interactive elements and text content")
    print("4. CUSTOM - Provide your own CSS selector")
    print("="*60)

# Function to validate URL format
def validate_url(url):
    """
    Validate URL format and structure.
    Returns: (is_valid, error_message)
    """
    if not url or len(url.strip()) == 0:
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    # Simple URL validation - just check for http:// or https://
    if url.startswith('http://') or url.startswith('https://'):
        # Check for basic domain structure
        remaining = url.split('://', 1)[1]
        if remaining and '.' in remaining or 'localhost' in remaining:
            return True, None
    
    return False, "Invalid URL format. URL must start with http:// or https://"

# Function to validate CSS selector
def validate_css_selector(selector):
    """
    Basic validation of CSS selector. Allows valid CSS, blocks XSS attempts.
    Returns: (is_valid, error_message)
    """
    if not selector or len(selector.strip()) == 0:
        return False, "CSS selector cannot be empty"
    
    selector = selector.strip()
    
    # Check for XSS/injection attempts - only block HTML/JS injection
    dangerous_patterns = ['<', 'javascript:', 'onerror=', 'onclick=', 'onload=']
    for pattern in dangerous_patterns:
        if pattern in selector.lower():
            return False, f"Invalid CSS selector. Contains potentially dangerous pattern: '{pattern}'"
    
    return True, None

# Function to get valid mode selection with retry logic
def get_mode_selection(max_retries=3):
    """
    Get and validate mode selection from user with retry logic.
    Returns: (mode, custom_selector) or (None, None) on exit
    """
    mode_map = {'1': 'interactive', '2': 'text', '3': 'all', '4': 'custom'}
    retries = 0
    
    while retries < max_retries:
        mode_choice = input("\nSelect mode (1-4) or enter 'q' to quit: ").strip().lower()
        
        if mode_choice == 'q':
            return None, None
        
        if mode_choice in mode_map:
            mode = mode_map[mode_choice]
            
            # If custom mode, get and validate custom selector
            if mode == 'custom':
                custom_retries = 0
                while custom_retries < 3:
                    custom_selector = input("\nEnter CSS selector: ").strip()
                    is_valid, error_msg = validate_css_selector(custom_selector)
                    
                    if is_valid:
                        return mode, custom_selector
                    else:
                        print(f"ERROR: {error_msg}")
                        custom_retries += 1
                
                print(f"ERROR: Invalid CSS selector after {custom_retries} attempts. Please select a different mode.")
                retries += 1
                continue
            
            return mode, None
        else:
            retries += 1
            remaining = max_retries - retries
            if remaining > 0:
                print(f"ERROR: Invalid choice. Please enter 1, 2, 3, or 4. ({remaining} attempts remaining)")
            else:
                print(f"ERROR: Maximum retry attempts reached. Exiting...")
    
    return None, None

# Function to get and validate URL from user
def get_valid_url(max_retries=3):
    """
    Get and validate URL from user with retry logic.
    Returns: valid URL or None on exit
    """
    retries = 0
    
    while retries < max_retries:
        url = input("\nEnter URL to scrape (default: https://www.google.com): ").strip()
        
        if not url:
            return "https://www.google.com"
        
        is_valid, error_msg = validate_url(url)
        
        if is_valid:
            # Add protocol if missing
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            return url
        else:
            retries += 1
            remaining = max_retries - retries
            print(f"ERROR: {error_msg}", end="")
            if remaining > 0:
                print(f" ({remaining} attempts remaining)")
            else:
                print(f"\nERROR: Maximum retry attempts reached. Exiting...")
    
    return None

# Main function to run the scraper
# Takes a URL, extracts elements, and saves the data as a JSON file
# Filename format: selectors_{domain}_{mode}_{timestamp}.json
def main():
    try:
        # Display mode options
        display_modes()
        
        # Get valid mode selection with retry logic
        mode, custom_selector = get_mode_selection(max_retries=3)
        
        if mode is None:
            print("\nERROR: Exiting...")
            return
        
        # Get valid URL with retry logic
        url = get_valid_url(max_retries=3)
        
        if url is None:
            print("\nERROR: Exiting...")
            return
        
        print(f"\nINFO: Scraping {url} with mode: {mode}...")
        
        # Extract elements
        elements = extract_elements(url, mode=mode, custom_selector=custom_selector)
        
        if not elements:
            print("\nERROR: No elements found. Please check:")
            print("   - The URL is accessible and loads properly")
            print("   - The selector/mode matches the page content")
            print("   - Your internet connection is working")
            return
        
        # Parse URL to get domain for filename
        try:
            domain = urlparse(url).netloc.replace(".", "_")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"selectors_{domain}_{mode}_{timestamp}.json"
        except Exception as e:
            print(f"ERROR: Failed to generate filename. Details: {str(e)}")
            return
        
        # Rank selectors using the advanced ranking engine
        print(f"\nINFO: Ranking selectors with advanced scoring engine...")
        try:
            ranked_elements = rank_selectors_for_elements(url, elements)
            if not ranked_elements:
                print(f"ERROR: Failed to rank selectors. No valid elements found.")
                return
        except Exception as e:
            print(f"ERROR: Failed to rank selectors. Details: {str(e)}")
            return
        
        # Build training dataset
        print(f"INFO: Building training dataset...")
        try:
            builder = DatasetBuilder()
            dataset = builder.build_dataset(url, ranked_elements)
            if not dataset:
                print(f"ERROR: Failed to build dataset. No training data generated.")
                return
        except Exception as e:
            print(f"ERROR: Failed to build dataset. Details: {str(e)}")
            return
        
        # Save training dataset to JSON file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            print(f"\nSUCCESS: Training dataset saved successfully!")
            print(f"   Processed {len(elements)} elements")
            print(f"   Generated {len(dataset)} training samples")
            print(f"   Dataset saved to: {filename}")
            
            # Print summary of best selectors
            best_selectors = [row for row in dataset if row['is_best'] == 1]
            print(f"   Best selectors found: {len(best_selectors)}")
            
        except IOError as e:
            print(f"ERROR: Failed to save dataset. Details: {str(e)}")
            return
    
    except KeyboardInterrupt:
        print("\n\nERROR: Operation cancelled by user.")
        return
    except Exception as e:
        print(f"\nERROR: Unexpected error: {str(e)}")
        return

# Main function removed - use as importable module