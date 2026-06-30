import os
import json

from api_integration.constants import DOWNLOADS_DIR, RFQ_EXCEL_MARKER
from api_integration.excel.excel_pipeline import process_attachments


def process_attachments_wrapper(
    download_dir: str = DOWNLOADS_DIR,
    exclude: tuple = ("junk",),
    subfolder: str = None,
    dry_run: bool = False,
    test_run: bool = False,
) -> int:
    processed = 0
    skipped = 0

    if subfolder:
        folder_path = os.path.join(download_dir, subfolder)
        if not os.path.isdir(folder_path):
            print(f"✗ Subfolder not found: {folder_path}")
            return 0
        folders_to_process = [folder_path]
    else:
        if not os.path.isdir(download_dir):
            print(f"Download directory not found: {download_dir}")
            return 0
        folders_to_process = [
            os.path.join(download_dir, entry)
            for entry in sorted(os.listdir(download_dir))
            if os.path.isdir(os.path.join(download_dir, entry)) and entry not in exclude
        ]

    for folder_path in folders_to_process:
        excel_marker_path = os.path.join(folder_path, RFQ_EXCEL_MARKER)

        if os.path.exists(excel_marker_path) and not test_run:
            print(f"  -> Skipping (already processed): {os.path.basename(folder_path)}")
            skipped += 1
            continue

        if dry_run:
            print(f"  [dry-run] would process {os.path.basename(folder_path)}")
            processed += 1
            continue

        result = process_attachments(folder_path)

        with open(excel_marker_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if result.get("error") is None:
            print(f"  ✓ processed {os.path.basename(folder_path)}")
        else:
            print(f"  ✗ failed {os.path.basename(folder_path)}: {result.get('error')}")

        processed += 1

    print(f"\nTotal emails processed: {processed}")
    print(f"Total emails skipped: {skipped}")
    return processed
