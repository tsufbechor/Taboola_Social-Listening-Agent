import csv
import json
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
DATA_SOURCE_DIRECTORIES: List[Path] = [
    Path("output/REDDIT_DATA"),
    Path("output/AI_GENERATED_DATA"),
    Path("output/HACKER_NEWS_DATA"),
]


def load_summary(summary_path: Path) -> Dict[str, Any]:
    if not summary_path.is_file():
        raise FileNotFoundError(f"Missing summary report: {summary_path}")
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_trends(trends_path: Path) -> List[Dict[str, str]]:
    if not trends_path.is_file():
        return []
    with trends_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return [{key: value for key, value in row.items()} for row in reader]


def build_aggregates(summary_data: Dict[str, Any], trends: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "summary": summary_data.get("summary", ""),
        "overall_sentiment_distribution": summary_data.get("overall_sentiment_distribution", {}),
        "field_distributions": summary_data.get("field_distributions", {}),
        "top_themes_by_field": summary_data.get("top_themes_by_field", []),
        "trends_over_time": trends,
        "edge_cases": summary_data.get("edge_cases", []),
        "language_distribution": summary_data.get("language_distribution", {}),
    }


def process_directory(relative_path: Path) -> None:
    data_dir = BASE_DIR / relative_path
    if not data_dir.is_dir():
        raise NotADirectoryError(f"Data directory does not exist: {data_dir}")

    summary_path = data_dir / "summary_report.json"
    trends_path = data_dir / "sentiment_trends.csv"
    aggregates_path = data_dir / "aggregates.json"

    summary_data = load_summary(summary_path)
    trends = load_trends(trends_path)
    aggregates = build_aggregates(summary_data, trends)

    serialized = json.dumps(aggregates, ensure_ascii=False, indent=2)
    aggregates_path.write_text(serialized + "\n", encoding="utf-8")

    try:
        relative_output = aggregates_path.relative_to(BASE_DIR)
    except ValueError:
        relative_output = aggregates_path
    print(f"Wrote {relative_output.as_posix()}")


def main() -> None:
    for directory in DATA_SOURCE_DIRECTORIES:
        process_directory(directory)


if __name__ == "__main__":
    main()
