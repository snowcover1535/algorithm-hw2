"""Measure separate-chaining probes across a range of load factors."""

import csv
import random
import sys
from pathlib import Path


CAPACITY = 2048
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))


def polynomial_hash(key: str, capacity: int) -> int:
    value = 0
    for character in key:
        value = (value * 31 + ord(character)) % capacity
    return value


def measure_probes(capacity: int, item_count: int, seed: int = 2026) -> tuple[float, float]:
    if capacity < 1:
        raise ValueError("capacity must be positive")
    if item_count < 0:
        raise ValueError("item_count must be non-negative")

    generator = random.Random(seed)
    buckets: list[list[str]] = [[] for _ in range(capacity)]
    keys = []
    seen = set()
    while len(keys) < item_count:
        key = f"url-{generator.getrandbits(64):016x}"
        if key not in seen:
            seen.add(key)
            keys.append(key)

    successful_probes = 0
    for key in keys:
        bucket = buckets[polynomial_hash(key, capacity)]
        successful_probes += len(bucket) + 1
        bucket.append(key)

    average_success = successful_probes / item_count if item_count else 0.0
    average_failure = sum(map(len, buckets)) / capacity
    return average_success, average_failure


def experiment_rows(capacity: int = CAPACITY) -> list[dict[str, float]]:
    rows = []
    for load_factor in LOAD_FACTORS:
        item_count = round(capacity * load_factor)
        successful, unsuccessful = measure_probes(
            capacity, item_count, seed=2026 + item_count
        )
        rows.append(
            {
                "load_factor": load_factor,
                "successful_measured": successful,
                "successful_theory": 1 + load_factor / 2,
                "unsuccessful_measured": unsuccessful,
                "unsuccessful_theory": load_factor,
            }
        )
    return rows


def write_csv(rows: list[dict[str, float]], path: Path) -> None:
    fields = (
        "load_factor",
        "successful_measured",
        "successful_theory",
        "unsuccessful_measured",
        "unsuccessful_theory",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {key: f"{row[key]:.4f}" for key in fields} for row in rows
        )


def write_svg(rows: list[dict[str, float]], path: Path) -> None:
    width, height = 760, 460
    left, right, top, bottom = 65, 25, 30, 55
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_load, max_probes = 4.0, 5.0

    def point(load: float, probes: float) -> tuple[float, float]:
        x = left + load / max_load * plot_width
        y = top + (max_probes - probes) / max_probes * plot_height
        return x, y

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font:12px sans-serif}.axis{stroke:#333}.grid{stroke:#ddd}</style>',
        '<text x="380" y="20" text-anchor="middle">Separate chaining probe counts</text>',
    ]
    for tick in range(6):
        y = point(0, tick)[1]
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}"/>')
        lines.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end">{tick}</text>')
    for tick in range(5):
        x = point(tick, 0)[0]
        lines.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}"/>')
        lines.append(f'<text x="{x:.1f}" y="{height-bottom+20}" text-anchor="middle">{tick}</text>')
    lines.extend(
        [
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}"/>',
            f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-10}" text-anchor="middle">Load factor (alpha)</text>',
            f'<text transform="translate(16 {top + plot_height/2:.1f}) rotate(-90)" text-anchor="middle">Average nodes examined</text>',
        ]
    )

    series = (
        ("successful_measured", "#1769aa", "Successful measured"),
        ("successful_theory", "#1769aa", "Successful theory"),
        ("unsuccessful_measured", "#d1495b", "Unsuccessful measured"),
        ("unsuccessful_theory", "#d1495b", "Unsuccessful theory"),
    )
    for series_index, (field, color, label) in enumerate(series):
        points = [
            point(row["load_factor"], row[field])
            for row in rows
        ]
        point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dash = ' stroke-dasharray="5 4"' if series_index in (1, 3) else ""
        lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2"{dash} '
            f'points="{point_text}"/>'
        )
        legend_x = left + (series_index % 2) * 220
        legend_y = top + 16 + (series_index // 2) * 18
        lines.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+24}" y2="{legend_y}" stroke="{color}" stroke-width="2"{dash}/>')
        lines.append(f'<text x="{legend_x+30}" y="{legend_y+4}">{label}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    output_dir = Path(__file__).parent
    rows = experiment_rows()
    csv_path = output_dir / "probe_results.csv"
    svg_path = output_dir / "probe_results.svg"
    write_csv(rows, csv_path)
    write_svg(rows, svg_path)
    print("alpha  successful (measured/theory)  unsuccessful (measured/theory)")
    for row in rows:
        print(
            f'{row["load_factor"]:4.2f}   '
            f'{row["successful_measured"]:6.3f}/{row["successful_theory"]:6.3f}   '
            f'{row["unsuccessful_measured"]:6.3f}/{row["unsuccessful_theory"]:6.3f}'
        )
    print(f"Wrote {csv_path} and {svg_path}")


if __name__ == "__main__":
    main()
