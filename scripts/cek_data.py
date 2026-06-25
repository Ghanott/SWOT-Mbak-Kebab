import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

FILES_TO_CHECK = [
    {
        "path": "mbak_kebab_internal_baseline.csv",
        "type": "csv",
        "required_columns": ["item", "value", "source_type", "source_url", "evidence_strength", "notes"],
    },
    {
        "path": "mbak_kebab_menu.csv",
        "type": "csv",
        "required_columns": ["menu_id", "brand", "menu_name", "category", "price_type", "source", "confidence"],
    },
    {
        "path": "competitor_menu_price.csv",
        "type": "csv",
        "required_columns": ["competitor_id", "competitor_name", "zone", "category", "source", "confidence"],
    },
    {
        "path": "zone_summary.csv",
        "type": "csv",
        "required_columns": ["zone", "population", "university_count", "observed_kebab_competitor_count", "confidence"],
    },
    {
        "path": "zone_scoring.csv",
        "type": "csv",
        "required_columns": ["zone", "opportunity_score", "threat_score", "business_potential_score"],
    },
    {
        "path": "swot_evidence.csv",
        "type": "csv",
        "required_columns": ["swot_type", "factor_code", "factor_title", "evidence", "source_dataset", "confidence"],
    },
    {
        "path": "landing_page_data.json",
        "type": "json",
        "required_keys": ["project_title", "last_updated", "summary_cards", "zone_rankings", "zone_summary", "swot"],
    },
]


def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)
    return columns, rows


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def preview_rows(rows: list[dict], limit: int = 5) -> None:
    if not rows:
        print("Preview: []")
        return

    print(f"Preview {min(limit, len(rows))} row(s):")
    for index, row in enumerate(rows[:limit], start=1):
        print(f"{index}. {row}")


def preview_json(payload, limit: int = 5) -> None:
    if isinstance(payload, dict):
        print(f"Top-level keys: {list(payload.keys())}")
        for key, value in list(payload.items())[:limit]:
            if isinstance(value, list):
                print(f"- {key}: list[{len(value)}]")
            elif isinstance(value, dict):
                print(f"- {key}: dict(keys={list(value.keys())[:10]})")
            else:
                print(f"- {key}: {value}")
        return

    if isinstance(payload, list):
        print(f"Top-level list length: {len(payload)}")
        print(f"Preview {min(limit, len(payload))} item(s):")
        for index, item in enumerate(payload[:limit], start=1):
            print(f"{index}. {item}")
        return

    print(f"JSON scalar value: {payload}")


def warn_missing_columns(columns: list[str], required_columns: list[str]) -> None:
    missing = [column for column in required_columns if column not in columns]
    if missing:
        print(f"WARNING: Missing required columns: {missing}")


def warn_missing_keys(payload: dict, required_keys: list[str]) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        print(f"WARNING: Missing required keys: {missing}")


def validate_csv(config: dict) -> None:
    path = BASE_DIR / config["path"]
    print_header(f"Checking CSV: {config['path']}")

    if not path.exists():
        print("WARNING: File not found.")
        return

    columns, rows = load_csv(path)
    print(f"Rows: {len(rows)}")
    print(f"Columns ({len(columns)}): {columns}")
    warn_missing_columns(columns, config["required_columns"])
    if not rows:
        print("WARNING: CSV file is empty.")
    preview_rows(rows)


def validate_json(config: dict) -> None:
    path = BASE_DIR / config["path"]
    print_header(f"Checking JSON: {config['path']}")

    if not path.exists():
        print("WARNING: File not found.")
        return

    payload = load_json(path)
    if isinstance(payload, dict):
        print(f"Top-level type: dict")
        print(f"Top-level entries: {len(payload)}")
        warn_missing_keys(payload, config["required_keys"])
        if not payload:
            print("WARNING: JSON object is empty.")
    elif isinstance(payload, list):
        print("Top-level type: list")
        print(f"Top-level entries: {len(payload)}")
        if not payload:
            print("WARNING: JSON list is empty.")
    else:
        print(f"Top-level type: {type(payload).__name__}")

    preview_json(payload)


def main() -> None:
    print_header("VALIDASI DATA AWAL")
    print(f"Base directory: {BASE_DIR}")

    for config in FILES_TO_CHECK:
        if config["type"] == "csv":
            validate_csv(config)
        elif config["type"] == "json":
            validate_json(config)


if __name__ == "__main__":
    main()
