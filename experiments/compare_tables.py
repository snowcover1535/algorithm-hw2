"""Compare separate chaining and linear probing on identical key sets."""

import csv
from math import ceil
import random
from pathlib import Path
from time import perf_counter

from experiments.probe_experiment import CAPACITY, MISS_COUNT, average_probes, log_progress, random_urls
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


TRIALS = 5
REPOSITORY_URL = "https://github.com/snowcover1535/algorithm-hw2"
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
FIELDS = (
    "load_factor",
    "chaining_success_measured",
    "chaining_success_theory",
    "chaining_failure_measured",
    "chaining_failure_theory",
    "linear_success_measured",
    "linear_success_theory",
    "linear_failure_measured",
    "linear_failure_theory",
)


def measure_key_set(keys: list[str], capacity: int, missing: list[str]) -> tuple[float, float, float, float]:
    chaining = HashTable(capacity=capacity, max_load=None)
    linear = LinearProbingHashTable(capacity=capacity)
    for index, key in enumerate(keys):
        chaining.set(key, index)
        linear.set(key, index)

    return (
        average_probes(chaining, keys),
        average_probes(chaining, missing),
        average_probes(linear, keys),
        average_probes(linear, missing),
    )


def experiment_rows(
    capacity: int = CAPACITY, seed: int = 2026, *, trials: int = TRIALS, on_progress=None
) -> list[dict[str, float]]:
    if capacity < 10:
        raise ValueError("capacity must be at least 10")
    if trials < 1:
        raise ValueError("trials must be positive")
    totals = [[] for _ in LOAD_FACTORS]
    generator = random.Random(seed)
    max_count = round(capacity * LOAD_FACTORS[-1])
    for trial in range(1, trials + 1):
        started = perf_counter()
        keys = random_urls(generator, max_count, "hit")
        missing = random_urls(generator, MISS_COUNT, "miss")
        for load_factor, results in zip(LOAD_FACTORS, totals):
            count = round(capacity * load_factor)
            results.append(measure_key_set(keys[:count], capacity, missing))
        if on_progress is not None:
            on_progress(trial, trials + 1, f"Measured comparison trial {trial}/{trials}", started)

    rows = []
    for load_factor, results in zip(LOAD_FACTORS, totals):
        actual_load = round(capacity * load_factor) / capacity
        chain_hit, chain_miss, linear_hit, linear_miss = (
            sum(column) / trials for column in zip(*results)
        )
        rows.append(
            {
                "load_factor": load_factor,
                "chaining_success_measured": chain_hit,
                "chaining_success_theory": 1 + actual_load / 2,
                "chaining_failure_measured": chain_miss,
                "chaining_failure_theory": actual_load,
                "linear_success_measured": linear_hit,
                "linear_success_theory": 0.5 * (1 + 1 / (1 - actual_load)),
                "linear_failure_measured": linear_miss,
                "linear_failure_theory": 0.5 * (1 + 1 / (1 - actual_load) ** 2),
            }
        )
    return rows


def write_csv(rows: list[dict[str, float]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: f"{row[field]:.4f}" for field in FIELDS} for row in rows
        )


def chart_limits(rows: list[dict[str, float]]) -> tuple[int, int]:
    success = max(max(row["linear_success_measured"], row["linear_success_theory"]) for row in rows)
    failure = max(max(row["linear_failure_measured"], row["linear_failure_theory"]) for row in rows)
    return ceil(success), 10 * ceil(failure / 10)


def write_svg(rows: list[dict[str, float]], path: Path) -> None:
    width, height = 820, 690
    left, right = 75, 30
    chart_width = width - left - right
    success_top, failure_top = chart_limits(rows)
    panels = (
        (55, 265, "Successful search", success_top, "success"),
        (385, 265, "Unsuccessful search", failure_top, "failure"),
    )
    colors = {"chaining": "#1769aa", "linear": "#d1495b"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font:12px sans-serif}.grid{stroke:#ddd}.axis{stroke:#333}</style>',
        '<text x="410" y="24" text-anchor="middle" font-size="16">Hash table probe comparison</text>',
    ]

    for panel_y, panel_height, title, max_probes, metric in panels:
        plot_top = panel_y
        plot_bottom = panel_y + panel_height
        lines.append(
            f'<text x="{left + chart_width/2:.1f}" y="{plot_top-12}" text-anchor="middle">{title}</text>'
        )
        lines.append(
            f'<text transform="translate(16 {plot_top+panel_height/2:.1f}) rotate(-90)" '
            'text-anchor="middle">Average nodes / slots inspected</text>'
        )

        def point(load: float, probes: float) -> tuple[float, float]:
            x = left + (load - 0.1) / 0.8 * chart_width
            y = plot_bottom - probes / max_probes * panel_height
            return x, y

        tick_step = 1 if metric == "success" else 10
        for tick in range(0, int(max_probes) + 1, tick_step):
            y = point(0.1, tick)[1]
            lines.append(
                f'<line class="grid" x1="{left}" y1="{y:.1f}" '
                f'x2="{width-right}" y2="{y:.1f}"/>'
            )
            lines.append(
                f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end">{tick}</text>'
            )
        for tick in range(1, 10):
            load = tick / 10
            x = point(load, 0)[0]
            lines.append(
                f'<line class="grid" x1="{x:.1f}" y1="{plot_top}" '
                f'x2="{x:.1f}" y2="{plot_bottom}"/>'
            )
            lines.append(
                f'<text x="{x:.1f}" y="{plot_bottom+18}" text-anchor="middle">{load:.1f}</text>'
            )
        lines.append(
            f'<line class="axis" x1="{left}" y1="{plot_top}" x2="{left}" y2="{plot_bottom}"/>'
        )
        lines.append(
            f'<line class="axis" x1="{left}" y1="{plot_bottom}" '
            f'x2="{width-right}" y2="{plot_bottom}"/>'
        )
        lines.append(
            f'<text x="{left + chart_width/2:.1f}" y="{plot_bottom+38}" text-anchor="middle">Load factor</text>'
        )

        series = (
            ("chaining", f"chaining_{metric}_measured", "Chaining measured", False),
            ("chaining", f"chaining_{metric}_theory", "Chaining theory", True),
            ("linear", f"linear_{metric}_measured", "Linear measured", False),
            ("linear", f"linear_{metric}_theory", "Linear theory", True),
        )
        for series_index, (method, field, label, dashed) in enumerate(series):
            points = [point(row["load_factor"], row[field]) for row in rows]
            point_list = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            dash = ' stroke-dasharray="5 4"' if dashed else ""
            lines.append(
                f'<polyline fill="none" stroke="{colors[method]}" stroke-width="2"{dash} '
                f'points="{point_list}"/>'
            )
            legend_x = left + (series_index % 2) * 235
            legend_y = plot_top + 15 + (series_index // 2) * 17
            lines.append(
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+22}" y2="{legend_y}" '
                f'stroke="{colors[method]}" stroke-width="2"{dash}/>'
            )
            lines.append(f'<text x="{legend_x+28}" y="{legend_y+4}">{label}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class _PDFPage:
    def __init__(self):
        self.operations = []

    def text(self, x: float, y: float, value: str, size: int = 8) -> None:
        encoded = value.encode("ascii", "replace").decode("ascii")
        encoded = encoded.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.operations.append(
            f"BT /F1 {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({encoded}) Tj ET"
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: tuple[float, float, float] = (0, 0, 0),
        dashed: bool = False,
        width: float = 0.7,
    ) -> None:
        dash = "[4 3] 0 d" if dashed else "[] 0 d"
        self.operations.append(
            f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG "
            f"{width:.2f} w {dash} {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"
        )

    def chart(
        self,
        rows: list[dict[str, float]],
        x: float,
        y: float,
        width: float,
        height: float,
        metric: str,
        max_probes: float,
    ) -> None:
        left, right, top, bottom = 25, 5, 15, 20
        plot_x = x + left
        plot_y = y + bottom
        plot_width = width - left - right
        plot_height = height - top - bottom

        def point(load: float, probes: float) -> tuple[float, float]:
            return (
                plot_x + (load - 0.1) / 0.8 * plot_width,
                plot_y + probes / max_probes * plot_height,
            )

        ticks = range(0, int(max_probes) + 1, 1 if metric == "success" else 10)
        for tick in ticks:
            px, py = point(0.1, tick)
            self.line(plot_x, py, plot_x + plot_width, py, (0.82, 0.82, 0.82), width=0.35)
            self.text(plot_x - 17, py - 2, str(tick), 6)
        for tick in range(1, 10):
            load = tick / 10
            px, py = point(load, 0)
            self.line(px, plot_y, px, plot_y + plot_height, (0.88, 0.88, 0.88), width=0.35)
            self.text(px - 6, plot_y - 10, f"{load:.1f}", 6)
        self.line(plot_x, plot_y, plot_x, plot_y + plot_height, width=0.8)
        self.line(plot_x, plot_y, plot_x + plot_width, plot_y, width=0.8)

        series = (
            ("chaining", f"chaining_{metric}_measured", (0.09, 0.41, 0.67), False),
            ("chaining", f"chaining_{metric}_theory", (0.09, 0.41, 0.67), True),
            ("linear", f"linear_{metric}_measured", (0.82, 0.29, 0.35), False),
            ("linear", f"linear_{metric}_theory", (0.82, 0.29, 0.35), True),
        )
        for _method, field, color, dashed in series:
            points = [point(row["load_factor"], row[field]) for row in rows]
            for first, second in zip(points, points[1:]):
                self.line(*first, *second, color=color, dashed=dashed, width=1.2)


def write_pdf(
    rows: list[dict[str, float]], path: Path, *, capacity: int = CAPACITY, trials: int = TRIALS
) -> None:
    page = _PDFPage()
    page.text(42, 823, REPOSITORY_URL, 9)
    page.text(42, 806, "Hash table comparison figures", 15)
    page.text(42, 788, f"M={capacity}; {trials} trials; {MISS_COUNT} missing URLs per trial; seed=2026.", 8)
    page.text(42, 774, "Both implementations receive the same inputs at load factors 0.1 to 0.9.", 8)

    last = rows[-1]
    page.text(42, 750, "At alpha=0.9 (measured / theory):", 9)
    page.text(
        52,
        736,
        f"Chaining success {last['chaining_success_measured']:.2f}/{last['chaining_success_theory']:.2f}; "
        f"failure {last['chaining_failure_measured']:.2f}/{last['chaining_failure_theory']:.2f}.",
        8,
    )
    page.text(
        52,
        722,
        f"Linear success {last['linear_success_measured']:.2f}/{last['linear_success_theory']:.2f}; "
        f"failure {last['linear_failure_measured']:.2f}/{last['linear_failure_theory']:.2f}.",
        8,
    )

    page.text(42, 699, "alpha  chain hit  chain miss  linear hit  linear miss", 7)
    for index, row in enumerate(rows):
        page.text(
            42,
            687 - index * 10,
            f"{row['load_factor']:.1f}    "
            f"{row['chaining_success_measured']:.2f}       "
            f"{row['chaining_failure_measured']:.2f}       "
            f"{row['linear_success_measured']:.2f}       "
            f"{row['linear_failure_measured']:.2f}",
            7,
        )

    page.text(48, 575, "Successful search (solid = measured, dashed = theory)", 8)
    success_top, failure_top = chart_limits(rows)
    page.chart(rows, 42, 390, 250, 175, "success", success_top)
    page.text(325, 575, "Unsuccessful search (solid = measured, dashed = theory)", 8)
    page.chart(rows, 315, 390, 250, 175, "failure", failure_top)
    page.text(42, 365, "Blue: chaining; red: linear probing. Both methods use identical keys per load factor.", 8)
    page.text(42, 347, "Units: nodes compared for chaining; slots inspected for linear probing.", 8)
    page.text(42, 333, "Successful searches cover every inserted key. Misses use a separate URL pool.", 8)
    page.text(42, 296, "Full measurements: experiments/table_comparison.csv; graph: table_comparison.svg.", 7)

    stream = ("\n".join(page.operations) + "\n").encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"endstream",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{index} 0 obj\n".encode("ascii"))
        document.extend(body)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(document)


def main() -> None:
    output_dir = Path(__file__).parent
    log_progress(0, TRIALS + 1, f"Starting comparison (M={CAPACITY}, {TRIALS} trials)", perf_counter())
    rows = experiment_rows(on_progress=log_progress)
    started = perf_counter()
    csv_path = output_dir / "table_comparison.csv"
    svg_path = output_dir / "table_comparison.svg"
    pdf_path = output_dir / "table_comparison.pdf"
    write_csv(rows, csv_path)
    write_svg(rows, svg_path)
    write_pdf(rows, pdf_path)
    print("alpha  chain hit/miss  linear hit/miss")
    for row in rows:
        print(
            f'{row["load_factor"]:.1f}    '
            f'{row["chaining_success_measured"]:.3f}/{row["chaining_failure_measured"]:.3f}    '
            f'{row["linear_success_measured"]:.3f}/{row["linear_failure_measured"]:.3f}'
        )
    log_progress(TRIALS + 1, TRIALS + 1, f"Wrote {csv_path.name}, {svg_path.name}, and {pdf_path.name}", started)


if __name__ == "__main__":
    main()
