import csv
import re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WORKSPACE = Path(__file__).resolve().parent
INPUT_FILE = WORKSPACE / "table1_ukb_demographics.csv"
OUTPUT_FILE = WORKSPACE / "apoe_3d_plot.png"


def extract_value(value: str, mode: str) -> float:
    if value is None:
        return float("nan")
    text = value.strip()
    if not text:
        return float("nan")

    if mode == "mean":
        match = re.search(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", text)
        return float(match.group(0).replace(",", "")) if match else float("nan")

    if mode == "percent":
        # Prefer the value inside the last parentheses, such as "725 (94.16)"
        match = re.search(r"\(([-+]?\d+(?:,\d{3})*(?:\.\d+)?)\)", text)
        if match:
            return float(match.group(1).replace(",", ""))
        match = re.search(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", text)
        return float(match.group(0).replace(",", "")) if match else float("nan")

    return float("nan")


with INPUT_FILE.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# Select the exact rows we want to plot
age_row = next(row for row in rows if row["Characteristic"] == "Age at baseline" and row["Subcategory"] == "mean (sd)")
smoking_row = next(row for row in rows if row["Characteristic"] == "Smoking status" and row["Subcategory"] == "Current smoking")

# The genotype columns are the ones after the first two header fields
labels = []
ages = []
smoking = []

for key, value in age_row.items():
    if key in {"Characteristic", "Subcategory"}:
        continue
    if value is None or value == "":
        continue
    labels.append(key)
    ages.append(extract_value(age_row[key], "mean"))
    smoking.append(extract_value(smoking_row[key], "percent"))

# Keep the order consistent and avoid NaN values
points = [
    (label, age, smoke)
    for label, age, smoke in zip(labels, ages, smoking)
    if not (isinstance(age, float) and age != age)
]

labels = [p[0] for p in points]
ages = [p[1] for p in points]
smoking = [p[2] for p in points]

fig, ax = plt.subplots(figsize=(10, 8))

color_cycle = plt.cm.tab10.colors if len(labels) <= 10 else plt.cm.tab20.colors
colors = color_cycle[: len(labels)]
ax.scatter(ages, smoking, s=140, c=colors)

for label, x, y in zip(labels, ages, smoking):
    ax.text(x, y, label, fontsize=9, ha="left", va="bottom")

ax.set_xlabel("Mean age at baseline")
ax.set_ylabel("% current smoking")
ax.set_title("Scatter plot of APOE genotype groups")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
plt.close(fig)

print(f"Saved scatter plot to {OUTPUT_FILE}")
