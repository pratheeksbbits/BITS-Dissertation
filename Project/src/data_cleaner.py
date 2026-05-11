import re
import math
from collections import Counter
from typing import List, Dict

# Calculates the Shannon entropy of a string
def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    entropy = 0.0
    for count in Counter(s).values():
        p = count / len(s)
        entropy -= p * math.log2(p)
    return entropy

# Detects if a selector has dynamic patterns using improved logic
def has_dynamic_pattern_new(selector: str) -> int:
    tokens = re.split(r'[-_]', selector)
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if re.match(r'^[a-z0-9]{5,}$', token, re.IGNORECASE):
            return 1
        if calculate_entropy(token) > 3.5:
            return 1
        if re.match(r'^default-ltr-.*', token) or re.match(r'^e[0-9a-z]{6,}$', token, re.IGNORECASE):
            return 1
    return 0

# Computes a stability label for a dataset row based on features
def new_label(row) -> int:
    features = row['features']
    match_count = features.get('match_count', 0)
    has_dynamic = features.get('has_dynamic_pattern', 0)
    sel_len = features.get('selector_length', 0)
    sel_type = row['selector_type']

    label = 1 if (
        match_count == 1
        and has_dynamic == 0
        and sel_len < 50
        and sel_type not in ['xpath']
    ) else 0

    if sel_type == 'xpath':
        label = 0
    if sel_type == 'class' and has_dynamic == 1:
        label = 0

    return label

# Adds additional features to a dataset row for better ML input
def add_new_features(row) -> dict:
    features = row['features'].copy()
    selector = row['selector']
    text = row['text']

    features['is_probably_generated_class'] = (
        1 if row['selector_type'] == 'class' and (len(selector) > 10 or bool(re.search(r'\d', selector))) else 0
    )

    tokens = [t for t in re.split(r'[.\s#]', selector) if t]
    features['selector_token_count'] = len(tokens)

    token_lengths = [len(t) for t in tokens]
    features['avg_token_length'] = sum(token_lengths) / len(token_lengths) if token_lengths else 0

    features['has_numeric_token'] = 1 if any(re.search(r'\d', t) for t in tokens) else 0

    features['text_length'] = len(text)
    features['is_text_short'] = 1 if len(text) < 20 else 0
    features['is_xpath_absolute'] = 1 if row['selector_type'] == 'xpath' and selector.startswith('/') else 0

    return features

# Cleans and balances the dataset for ML training
def clean_dataset(data: List[Dict]) -> List[Dict]:
    import pandas as pd

    df = pd.DataFrame(data)

    df['features'] = df.apply(
        lambda row: {**row['features'], 'has_dynamic_pattern': has_dynamic_pattern_new(row['selector'])},
        axis=1
    )

    df = df[~((df['features'].apply(lambda x: x.get('match_count', 0) == 0) & (df['selector_type'] != 'text')))]
    df = df[~df['selector'].str.contains(r'#.*:.*:')]
    df = df[df['selector'].str.strip() != '']
    df = df.drop_duplicates(subset=['selector', 'url', 'tag', 'text'])

    df['label'] = df.apply(new_label, axis=1)

    df['text'] = df['text'].str.replace(r'\n', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    text_mask = df['selector_type'] == 'text'
    df.loc[text_mask, 'selector'] = 'text="' + df.loc[text_mask, 'text'] + '"'

    df['features'] = df.apply(add_new_features, axis=1)

    df = df[~((df['text'] == '') & (df['selector_type'] == 'text'))]
    df = df[df['features'].apply(lambda x: x.get('match_count', 0) <= 5)]
    df = df[df['features'].apply(lambda x: x.get('selector_length', 0) <= 100)]

    pos = df[df['label'] == 1]
    neg = df[df['label'] == 0]

    if len(neg) > len(pos):
        neg_balanced = neg.sample(len(pos), random_state=42)
        df = pd.concat([pos, neg_balanced])
    elif len(pos) > len(neg):
        pos_balanced = pos.sample(len(neg), random_state=42)
        df = pd.concat([pos_balanced, neg])

    return df[['selector', 'selector_type', 'features', 'label']].to_dict('records')