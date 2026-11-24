"""Measure separate-chaining probes across a range of load factors."""

import csv
import random
from datetime import datetime
from pathlib import Path
from time import perf_counter

from src.hash_table import HashTable


CAPACITY = 4093
MISS_COUNT = 2000
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))


def random_urls(generator: random.Random, count: int, kind: str) -> list[str]:
    tokens = generator.sample(range(2**62), count)
    return [f"https://example.com/{kind}/{token:x}" for token in tokens]


def average_probes(table, keys: list[str]) -> float:
    return sum(len(table.lookup_trace(key)) for key in keys) / len(keys) if keys else 0.0


def log_progress(completed: int, total: int, message: str, started: float) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(
        f"[{timestamp}] [{100 * completed / total:3.0f}%] "
        f"{message} ({perf_counter() - started:.2f}s)",
        flush=True,
    )


def measure_probes(capacity: int, item_count: int, seed: int = 2026) -> tuple[float, float]:
    if capacity < 1:
        raise ValueError("capacity must be positive")
    if item_count < 0:
        raise ValueError("item_count must be non-negative")

    generator = random.Random(seed)
    keys = random_urls(generator, item_count, "hit")
    missing = random_urls(generator, MISS_COUNT, "miss")
    table = HashTable(capacity=capacity, max_load=None)
    for index, key in enumerate(keys):
        table.set(key, index)
    return average_probes(table, keys), average_probes(table, missing)


def experiment_rows(capacity: int = CAPACITY, *, on_progress=None) -> list[dict[str, float]]:
    rows = []
    for index, load_factor in enumerate(LOAD_FACTORS, start=1):
        started = perf_counter()
        item_count = round(capacity * load_factor)
        successful, unsuccessful = measure_probes(capacity, item_count, seed=2026 + item_count)
        actual_load = item_count / capacity
        rows.append(
            {
                "load_factor": load_factor,
                "successful_measured": successful,
                "successful_theory": 1 + actual_load / 2,
                "unsuccessful_measured": unsuccessful,
                "unsuccessful_theory": actual_load,
            }
        )
        if on_progress is not None:
            on_progress(index, len(LOAD_FACTORS) + 1, f"Measured chaining at alpha={load_factor:.2f}", started)
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
    total = len(LOAD_FACTORS) + 1
    log_progress(0, total, f"Starting fixed-capacity chaining experiment (M={CAPACITY})", perf_counter())
    rows = experiment_rows(on_progress=log_progress)
    started = perf_counter()
    csv_path = output_dir / "results.csv"
    svg_path = output_dir / "results.svg"
    write_csv(rows, csv_path)
    write_svg(rows, svg_path)
    print("alpha  successful (measured/theory)  unsuccessful (measured/theory)")
    for row in rows:
        print(
            f'{row["load_factor"]:4.2f}   '
            f'{row["successful_measured"]:6.3f}/{row["successful_theory"]:6.3f}   '
            f'{row["unsuccessful_measured"]:6.3f}/{row["unsuccessful_theory"]:6.3f}'
        )
    log_progress(total, total, f"Wrote {csv_path.name} and {svg_path.name}", started)


if __name__ == "__main__":
    main()
