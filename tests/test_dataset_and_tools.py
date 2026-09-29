"""
Tests for the synthetic dataset generator and the local photo-metadata viewer.
"""

import csv
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "data"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))

import generate_dataset  # noqa: E402
import photo_metadata_viewer  # noqa: E402
from backend.services.scoring_engine import classify_risk  # noqa: E402

# Columns that would hold actual personal VALUES. Practice flags such as
# "password_reuse_reported" (YES/NO) are allowed; the values themselves are not.
PII_COLUMNS = {"name", "full_name", "first_name", "last_name", "username", "handle",
               "phone_number", "email_address", "home_address", "address", "dob", "birth_date",
               "password", "password_hash", "ip_address", "latitude", "longitude"}


def test_synthetic_dataset_generation(tmp_path):
    output = tmp_path / "synthetic.csv"
    counts = generate_dataset.generate_dataset(records=60, seed=1, output=str(output))
    assert sum(counts.values()) == 60

    with open(output, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 60
    header = rows[0].keys()
    for column in ("profile_id", "profile_visibility", "phone_public", "mfa_enabled",
                   "password_reuse_reported", "risk_score", "risk_level"):
        assert column in header
    assert not PII_COLUMNS.intersection(header)
    for row in rows:
        assert row["profile_id"].startswith("SYN-")
        # every answer column contains only fixed answer codes - never free text
        for column in generate_dataset.ANSWER_COLUMNS:
            assert re.fullmatch(r"[A-Z0-9_]{2,20}", row[column]), row[column]
        assert classify_risk(int(row["risk_score"])) == row["risk_level"]


def test_dataset_is_reproducible(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    generate_dataset.generate_dataset(records=20, seed=5, output=str(a))
    generate_dataset.generate_dataset(records=20, seed=5, output=str(b))
    assert a.read_text() == b.read_text()


def test_metadata_viewer_reads_and_strips_exif(tmp_path):
    from PIL import Image

    source = tmp_path / "fictional_photo.jpg"
    image = Image.new("RGB", (8, 8), "white")
    exif = Image.Exif()
    exif[0x010F] = "DemoCam"                      # Make
    exif[0x0110] = "Model X"                      # Model
    exif.get_ifd(0x8825).update({                 # fictional GPS block
        1: "N", 2: (10.0, 30.0, 0.0), 3: "E", 4: (20.0, 15.0, 0.0),
    })
    image.save(source, exif=exif)

    meta = photo_metadata_viewer.read_metadata(str(source))
    assert meta["exif"]["Make"] == "DemoCam"
    assert meta["gps"]["latitude"] == 10.5 and meta["gps"]["longitude"] == 20.25

    clean = tmp_path / "clean.jpg"
    photo_metadata_viewer.strip_metadata(str(source), str(clean))
    assert photo_metadata_viewer.read_metadata(str(clean))["exif"] == {}
    assert photo_metadata_viewer.read_metadata(str(source))["exif"]["Make"] == "DemoCam"  # original untouched
