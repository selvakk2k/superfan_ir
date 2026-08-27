import json
import os
import re

INTEGRATION_DIR = os.path.join(os.path.dirname(__file__), "../custom_components/superfan_ir")
STRINGS_PATH = os.path.join(INTEGRATION_DIR, "strings.json")
TRANSLATIONS_PATH = os.path.join(INTEGRATION_DIR, "translations/en.json")


def _get_leaf_keys(d, prefix=""):
    keys = set()
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_get_leaf_keys(v, full))
        else:
            keys.add(full)
    return keys


def test_strings_json_and_en_json_parity():
    """Verify strings.json and translations/en.json have identical keys."""
    with open(STRINGS_PATH, "r", encoding="utf-8") as f:
        strings = json.load(f)
    with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
        translations = json.load(f)

    strings_keys = _get_leaf_keys(strings)
    translations_keys = _get_leaf_keys(translations)

    assert strings_keys == translations_keys, (
        f"Key mismatch: {strings_keys ^ translations_keys}"
    )


def test_no_common_spelling_typos():
    """Scan all Python and JSON files for common typos."""
    common_typos = ["temparature", "celcius", "horisontal", "unsuccesful", "recieve", "untill"]
    typos_found = []
    for root, _, files in os.walk(INTEGRATION_DIR):
        for file in files:
            if file.endswith((".py", ".json")):
                with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    for typo in common_typos:
                        if re.search(rf"{typo}", content, re.IGNORECASE):
                            typos_found.append((file, typo))
    assert not typos_found, f"Typos found: {typos_found}"


def test_strings_capitalization():
    """Verify strings in strings.json begin with uppercase character or placeholder."""
    with open(STRINGS_PATH, "r", encoding="utf-8") as f:
        strings = json.load(f)

    def verify_cap(d, path=""):
        for k, v in d.items():
            curr_path = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                verify_cap(v, curr_path)
            elif isinstance(v, str) and v.strip():
                stripped = v.strip()
                if not (stripped.startswith(("[%key", "{", "**{"))):
                    first_alpha = next((c for c in stripped if c.isalpha()), None)
                    if first_alpha:
                        assert first_alpha.isupper(), f"String at {curr_path} not capitalized: '{v}'"

    verify_cap(strings)
