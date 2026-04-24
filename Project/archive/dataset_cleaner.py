import pandas as pd
import json
import re
import math
from collections import Counter

def calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    entropy = 0.0
    for count in Counter(s).values():
        p = count / len(s)
        entropy -= p * math.log2(p)
    return entropy

def has_dynamic_pattern_new(selector: str) -> int:
    """
    Improved dynamic pattern detection using tokenization, regex, entropy, and CSS-in-JS patterns.
    """
    # Tokenization on -, _
    tokens = re.split(r'[-_]', selector)

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Regex for [a-z0-9]{5,}
        if re.match(r'^[a-z0-9]{5,}$', token, re.IGNORECASE):
            return 1

        # Entropy calculation (high entropy indicates randomness)
        if calculate_entropy(token) > 3.5:
            return 1

        # CSS-in-JS patterns
        if re.match(r'^default-ltr-.*', token) or re.match(r'^e[0-9a-z]{6,}$', token, re.IGNORECASE):
            return 1

    return 0

def new_label(row) -> int:
    """Compute new label based on improved criteria."""
    features = row['features']
    match_count = features.get('match_count', 0)
    has_dynamic = features.get('has_dynamic_pattern', 0)
    sel_len = features.get('selector_length', 0)
    sel_type = row['selector_type']

    # Base condition
    label = 1 if (
        match_count == 1
        and has_dynamic == 0
        and sel_len < 50
        and sel_type not in ['xpath']
    ) else 0

    # Additional penalties
    if sel_type == 'xpath':
        label = 0
    if sel_type == 'class' and has_dynamic == 1:
        label = 0

    return label

def add_new_features(row) -> dict:
    """Add new features to the features dict."""
    features = row['features'].copy()
    selector = row['selector']
    text = row['text']

    # is_probably_generated_class
    features['is_probably_generated_class'] = (
        1 if row['selector_type'] == 'class' and (len(selector) > 10 or bool(re.search(r'\d', selector))) else 0
    )

    # selector_token_count
    tokens = [t for t in re.split(r'[.\s#]', selector) if t]
    features['selector_token_count'] = len(tokens)

    # avg_token_length
    token_lengths = [len(t) for t in tokens]
    features['avg_token_length'] = sum(token_lengths) / len(token_lengths) if token_lengths else 0

    # has_numeric_token
    features['has_numeric_token'] = 1 if any(re.search(r'\d', t) for t in tokens) else 0

    # text_length
    features['text_length'] = len(text)

    # is_text_short
    features['is_text_short'] = 1 if len(text) < 20 else 0

    # is_xpath_absolute
    features['is_xpath_absolute'] = 1 if row['selector_type'] == 'xpath' and selector.startswith('/') else 0

    return features

def clean_dataset(input_file: str, output_file: str):
    """Clean and transform the dataset."""
    # Load dataset
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    print("=== BEFORE CLEANING ===")
    print(f"Total rows: {len(df)}")
    print(f"Label distribution: {df['is_best'].value_counts().to_dict()}")
    print(f"Selector types: {df['selector_type'].value_counts().to_dict()}")
    print(f"Average selector length: {df['features'].apply(lambda x: x.get('selector_length', 0)).mean():.1f}")
    print(f"Unique selectors: {df['selector'].nunique()}")
    print(f"Empty text count: {(df['text'] == '').sum()}")

    # Step 1: Fix has_dynamic_pattern
    print("\n[1/8] Fixing has_dynamic_pattern...")
    df['features'] = df.apply(
        lambda row: {**row['features'], 'has_dynamic_pattern': has_dynamic_pattern_new(row['selector'])},
        axis=1
    )

    # Step 2: Remove invalid data
    print("[2/8] Removing invalid data...")
    initial_len = len(df)

    # Drop where match_count == 0 and selector_type != "text"
    df = df[~((df['features'].apply(lambda x: x.get('match_count', 0) == 0) & (df['selector_type'] != 'text')))]

    # Drop invalid patterns
    df = df[~df['selector'].str.contains(r'#.*:.*:')]  # Invalid CSS patterns
    df = df[df['selector'].str.strip() != '']  # Empty selectors

    # Drop duplicates (same selector + same element: url, tag, text)
    df = df.drop_duplicates(subset=['selector', 'url', 'tag', 'text'])

    print(f"   Removed {initial_len - len(df)} invalid/duplicate rows")

    # Step 3: Fix label
    print("[3/8] Computing new labels...")
    df['label'] = df.apply(new_label, axis=1)

    # Step 4: Normalize text
    print("[4/8] Normalizing text...")
    df['text'] = df['text'].str.replace(r'\n', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()

    # Recompute text selectors (optional, for consistency)
    text_mask = df['selector_type'] == 'text'
    df.loc[text_mask, 'selector'] = 'text="' + df.loc[text_mask, 'text'] + '"'

    # Step 5: Add new features
    print("[5/8] Adding new features...")
    df['features'] = df.apply(add_new_features, axis=1)

    # Step 6: Remove low-signal data
    print("[6/8] Removing low-signal data...")
    initial_len = len(df)

    # Drop where text is empty and selector_type == text
    df = df[~((df['text'] == '') & (df['selector_type'] == 'text'))]

    # Drop where match_count > 5
    df = df[df['features'].apply(lambda x: x.get('match_count', 0) <= 5)]

    # Drop where selector_length > 100
    df = df[df['features'].apply(lambda x: x.get('selector_length', 0) <= 100)]

    print(f"   Removed {initial_len - len(df)} low-signal rows")

    # Step 7: Balance dataset
    print("[7/8] Balancing dataset...")
    pos = df[df['label'] == 1]
    neg = df[df['label'] == 0]

    print(f"   Positive labels: {len(pos)}, Negative labels: {len(neg)}")

    if len(neg) > len(pos):
        neg_balanced = neg.sample(len(pos), random_state=42)
        df = pd.concat([pos, neg_balanced])
        print(f"   Downsampled negatives to {len(neg_balanced)}")
    elif len(pos) > len(neg):
        pos_balanced = pos.sample(len(neg), random_state=42)
        df = pd.concat([pos_balanced, neg])
        print(f"   Downsampled positives to {len(pos_balanced)}")

    # Step 8: Final output
    print("[8/8] Preparing final output...")
    output_data = df[['selector', 'selector_type', 'features', 'label']].to_dict('records')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n=== AFTER CLEANING ===")
    print(f"Total rows: {len(df)}")
    print(f"Label distribution: {df['label'].value_counts().to_dict()}")
    print(f"Selector types: {df['selector_type'].value_counts().to_dict()}")
    print(f"Average selector length: {df['features'].apply(lambda x: x.get('selector_length', 0)).mean():.1f}")
    print(f"Unique selectors: {df['selector'].nunique()}")
    print(f"Empty text count: {(df['text'] == '').sum()}")
    print(f"\nCleaned dataset saved to: {output_file}")

if __name__ == "__main__":
    input_file = 'training_dataset_20260424_140222.json'
    output_file = 'cleaned_training_dataset.json'
    clean_dataset(input_file, output_file)