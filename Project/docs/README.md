# Integrated Playwright Selector Ranking Framework

## Single Entry Point for ML Training Data Generation

This framework provides an end-to-end solution for generating high-quality training datasets for machine learning models that predict DOM selector stability and reliability for Playwright automation.

## Project Structure

```
project/
├── src/                    # Source code modules
│   ├── scraper.py         # Web element extraction
│   ├── ranking_engine.py  # Selector scoring and ranking
│   ├── data_cleaner.py    # Dataset cleaning and balancing
│   └── utils.py           # Utility functions
├── data/                  # Data files by processing stage
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Initial processed datasets
│   └── final/            # Clean ML-ready datasets
├── tests/                # Unit tests
│   ├── test_scraper.py
│   ├── test_ranking.py
│   └── test_cleaning.py
├── scripts/              # Alternative runners
│   └── run.py
├── docs/                 # Documentation
│   └── README.md
├── main.py               # Main entry point
├── requirements.txt      # Dependencies
└── archive/              # Old monolithic files
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Generate training dataset
python main.py <URL> [mode] [custom_selector]
```

## Usage Examples

```bash
# Default mode (all elements)
python main.py https://www.google.com

# Text elements only
python main.py https://www.wikipedia.org text

# Interactive elements only
python main.py https://www.example.com interactive

# Custom CSS selector
python main.py https://www.example.com custom .my-button

# Batch processing
python scripts/run.py batch https://site1.com https://site2.com

# Batch processing with visible browser (4 parallel workers)
python scripts/run.py batch https://site1.com https://site2.com --no-headless

# Batch processing with 2 parallel workers
python scripts/run.py batch https://site1.com https://site2.com https://site3.com --workers=2

# Single URL processing with visible browser
python scripts/run.py single https://example.com --no-headless
```

## Output

The framework generates timestamped JSON files in `data/final/`:
- `cleaned_training_dataset_DOMAIN_YYYYMMDD_HHMMSS.json` (ML-ready)

Where DOMAIN is extracted from the website URL (e.g., `example_com`, `google_com`).

### Dataset Format
```json
[
  {
    "selector": "text=\"Search\"",
    "selector_type": "text",
    "features": {
      "match_count": 1,
      "is_unique": 1,
      "selector_length": 13,
      "is_text": 1,
      "has_dynamic_pattern": 0,
      "is_probably_generated_class": 0,
      "selector_token_count": 1,
      "text_length": 6,
      "is_text_short": 1,
      // ... all features
    },
    "label": 1
  }
]
```

## Features

### Parallel Batch Processing
- **Multi-threaded execution**: Process multiple websites simultaneously
- **Configurable workers**: Set number of parallel workers (default: 4, max: 4)
- **Real-time progress**: See completion status as URLs finish processing
- **Error isolation**: Individual URL failures don't stop batch processing

### Headless/Virtual Browser Mode
- **Headless mode** (default): Run browser invisibly for faster processing
- **Visible mode**: Watch browser automation in real-time for debugging
- **Cross-platform**: Works on Windows, macOS, and Linux

### Data Quality Pipeline
1. **Element Extraction**: Uses Playwright to scrape real web pages
2. **Selector Generation**: Creates multiple selector types (CSS, XPath, text, etc.)
3. **Feature Engineering**: Extracts 20+ features for ML training
4. **Dynamic Pattern Detection**: Identifies unstable selectors using entropy and regex
5. **Data Cleaning**: Removes invalid, duplicate, and low-signal data
6. **Label Assignment**: Determines selector stability based on multiple criteria
7. **Dataset Balancing**: Ensures equal positive/negative samples

### Selector Types Supported
- `text`: Text-based selectors (`text="Button Text"`)
- `id`: ID selectors (`#element-id`)
- `css`: CSS class selectors (`.class-name`)
- `xpath`: XPath selectors (`/html/body/div[1]/button`)
- `aria-label`: ARIA label selectors (`[aria-label="Label"]`)
- `data-testid`: Test ID selectors (`[data-testid="test-id"]`)
- `name`: Name attribute selectors (`[name="field"]`)

## XGBoost Training

The output dataset is ready for XGBoost training:

```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Load dataset
df = pd.read_json('data/final/cleaned_training_dataset_example_com_20260424_145438.json')

# Extract features and labels
X = pd.DataFrame(list(df['features']))
y = df['label']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train XGBoost model
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

# Predict selector stability
predictions = model.predict(X_test)
accuracy = (predictions == y_test).mean()
print(f"Model Accuracy: {accuracy:.3f}")
```

## Architecture

The framework is organized into modular components:

- **Scraper** (`src/scraper.py`): Playwright-based web element extraction
- **Ranking Engine** (`src/ranking_engine.py`): Rule-based selector scoring and ranking
- **Data Cleaner** (`src/data_cleaner.py`): Quality filtering and balancing
- **Utils** (`src/utils.py`): Common utility functions
- **Main** (`main.py`): Primary entry point
- **Scripts** (`scripts/run.py`): Alternative runners for batch processing

## Command Line Options

- `URL`: Target webpage URL (required)
- `mode`: Extraction mode
  - `interactive`: Buttons, inputs, links
  - `text`: Headings, labels, paragraphs
  - `all`: Both interactive and text (default)
  - `custom`: Custom CSS selector (requires third argument)
- `custom_selector`: CSS selector string (required for custom mode)- `--headless`: Run browser in headless mode (default)
- `--no-headless`: Run browser in visible mode
- `--workers=N`: Number of parallel workers for batch processing (default: 4)
## Testing

Run unit tests:
```bash
python -m unittest discover tests/
```

## Error Handling

- URL validation
- Timeout handling for slow pages
- Invalid selector detection
- Unicode encoding support
- Graceful failure with informative messages

## Requirements

- Python 3.8+
- Playwright
- Pandas
- XGBoost (for training)
- scikit-learn (for evaluation)

## Output Statistics

Each run provides:
- Elements extracted
- Initial samples generated
- Final clean samples
- Label distribution
- Selector type breakdown
- Dataset balance confirmation

## Data Flow

1. **Input**: URL + mode
2. **Scraping**: Extract elements from webpage
3. **Ranking**: Score and rank all possible selectors
4. **Building**: Create initial dataset with features
5. **Cleaning**: Filter, label, and balance data
6. **Output**: ML-ready dataset in `data/final/`