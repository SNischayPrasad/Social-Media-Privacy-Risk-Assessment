"""
SAFE Local Photo Metadata Viewer & Remover.

Shows the metadata (EXIF) stored inside an image YOU choose, and can write a
clean COPY without metadata. Use it on your own photos to learn what a file
may reveal before you share it.

Safety & privacy guarantees
    * Runs 100% locally - the image is never uploaded or sent anywhere.
    * Displays ONLY metadata that is explicitly present in the file.
      It never guesses or infers a location from image content.
    * GPS coordinates are shown only if the file itself contains GPS tags.
    * The original file is never modified; stripping writes a new copy.

Usage (from the project root):
    python tools/photo_metadata_viewer.py path/to/photo.jpg
    python tools/photo_metadata_viewer.py path/to/photo.jpg --strip path/to/clean_copy.jpg

Requires Pillow (pip install Pillow).
"""

import argparse
import os
import sys

try:
    from PIL import ExifTags, Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install Pillow")

# Tags that commonly have privacy implications, with a short explanation.
PRIVACY_NOTES = {
    "GPSInfo": "GPS location recorded by the camera - can reveal where the photo was taken.",
    "DateTimeOriginal": "Exact time the photo was taken - can reveal routines.",
    "DateTime": "Date/time the file was last changed.",
    "Make": "Camera / phone manufacturer.",
    "Model": "Camera / phone model - can help link photos from the same device.",
    "Software": "Editing software or phone OS version.",
    "Artist": "Author name, if the camera was configured with one.",
    "BodySerialNumber": "Camera serial number - can link photos to one device.",
    "CameraOwnerName": "Owner name stored by the camera.",
    "ImageDescription": "Free-text description, sometimes auto-filled.",
}

GPS_IFD_TAG = 0x8825
EXIF_IFD_TAG = 0x8769


def _dms_to_degrees(values, ref):
    """Convert GPS degrees/minutes/seconds to decimal degrees (only when present)."""
    try:
        degrees, minutes, seconds = (float(v) for v in values)
    except (TypeError, ValueError):
        return None
    decimal = degrees + minutes / 60 + seconds / 3600
    return round(-decimal if ref in ("S", "W") else decimal, 6)


def read_metadata(path):
    """Return {"basic": {...}, "exif": {tag: value}, "gps": {...} or None}."""
    with Image.open(path) as img:
        basic = {"format": img.format, "size": f"{img.width} x {img.height}", "mode": img.mode}
        exif = img.getexif()

        tags = {}
        for tag_id, value in exif.items():
            if tag_id in (GPS_IFD_TAG, EXIF_IFD_TAG):
                continue
            tags[ExifTags.TAGS.get(tag_id, f"Tag{tag_id}")] = value
        for tag_id, value in exif.get_ifd(EXIF_IFD_TAG).items():
            tags[ExifTags.TAGS.get(tag_id, f"Tag{tag_id}")] = value

        gps = None
        gps_ifd = exif.get_ifd(GPS_IFD_TAG)
        if gps_ifd:
            named = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            gps = {"raw_tags": list(named)}
            if "GPSLatitude" in named and "GPSLongitude" in named:
                gps["latitude"] = _dms_to_degrees(named["GPSLatitude"], named.get("GPSLatitudeRef"))
                gps["longitude"] = _dms_to_degrees(named["GPSLongitude"], named.get("GPSLongitudeRef"))
            tags["GPSInfo"] = "present"

    return {"basic": basic, "exif": tags, "gps": gps}


def strip_metadata(source, destination):
    """Write a copy of the image containing pixel data only (no EXIF / GPS)."""
    if os.path.abspath(source) == os.path.abspath(destination):
        raise ValueError("Destination must be different from the original file.")
    with Image.open(source) as img:
        # Rebuild the image from raw pixels only, so no metadata block is carried over.
        clean = Image.frombytes(img.mode, img.size, img.tobytes())
        if img.mode == "P":
            clean.putpalette(img.getpalette())
        clean.save(destination, format=img.format)
    return destination


def _print_report(path, meta):
    print(f"\nFile: {os.path.basename(path)}")
    for key, value in meta["basic"].items():
        print(f"  {key:<8}: {value}")

    if not meta["exif"]:
        print("\nNo EXIF metadata found in this file.")
        return

    print("\nPrivacy-relevant metadata found:")
    found_any = False
    for tag, note in PRIVACY_NOTES.items():
        if tag in meta["exif"]:
            found_any = True
            print(f"  [!] {tag}: {str(meta['exif'][tag])[:80]}")
            print(f"      -> {note}")
    if not found_any:
        print("  none of the common privacy-relevant tags are present.")

    if meta["gps"]:
        print("\nGPS data IS present in this file (explicitly stored by the device):")
        if "latitude" in meta["gps"]:
            print(f"  latitude {meta['gps']['latitude']}, longitude {meta['gps']['longitude']}")
        print("  Consider removing metadata before sharing the original file.")

    others = [t for t in meta["exif"] if t not in PRIVACY_NOTES]
    if others:
        print(f"\nOther technical tags ({len(others)}): {', '.join(sorted(map(str, others))[:20])}")


def main():
    parser = argparse.ArgumentParser(description="View / remove metadata from your own image, locally.")
    parser.add_argument("image", help="path to an image you own")
    parser.add_argument("--strip", metavar="OUTPUT", help="write a metadata-free copy to OUTPUT")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        parser.error(f"File not found: {args.image}")

    _print_report(args.image, read_metadata(args.image))
    if args.strip:
        strip_metadata(args.image, args.strip)
        print(f"\nClean copy written (original untouched): {args.strip}")


if __name__ == "__main__":
    main()
