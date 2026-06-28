import sys
from pathlib import Path
import os
import json

src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from constants import (
    DOWNLOADS_DIR,
    RFQ_EXCEL_MARKER,
    RFQ_INFO_MARKER,
)
from sevenrights.api.post_rfq import post_rfq


def create_rfqs(
    download_dir: str = DOWNLOADS_DIR,
    exclude: tuple = ("junk",),
    subfolder: str = None,
    dry_run: bool = False,
    test_run: bool = False,
    timeout: int = 30,
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
        info_marker_path = os.path.join(folder_path, RFQ_INFO_MARKER)

        # Check RFQ_EXCEL_MARKER existence
        if not os.path.exists(excel_marker_path):
            print(
                f"  -> Skipping (no {RFQ_EXCEL_MARKER}): {os.path.basename(folder_path)}"
            )
            skipped += 1
            continue

        # Read RFQ_EXCEL_MARKER directly (no JSON error handling)
        with open(excel_marker_path, "r", encoding="utf-8") as f:
            rfq_data = json.load(f)

        # Check if RFQ_EXCEL_MARKER has non-empty error - pass downstream conditionally
        # TODO: consider better ways of error propagation
        if rfq_data.get("error"):
            if (not test_run and not os.path.exists(info_marker_path)) or test_run:
                with open(info_marker_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"error": rfq_data["error"], "rfq_id": None},
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
                print(
                    f"  -> Propagated error from {RFQ_EXCEL_MARKER} to {RFQ_INFO_MARKER}: {os.path.basename(folder_path)}"
                )
            print(
                f"  -> Skipping ({RFQ_EXCEL_MARKER} has error): {os.path.basename(folder_path)}"
            )
            skipped += 1
            continue

        # Check RFQ_INFO_MARKER existence (unless test_run bypasses it)
        if not test_run and os.path.exists(info_marker_path):
            print(
                f"  -> Skipping ({RFQ_INFO_MARKER} exists): {os.path.basename(folder_path)}"
            )
            skipped += 1
            continue

        if dry_run:
            mode = "test-run" if test_run else "dry-run"
            print(f"  [{mode}] would create RFQ for {os.path.basename(folder_path)}")
            processed += 1
            continue

        result = post_rfq(data=rfq_data, timeout=timeout)

        with open(info_marker_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if result.get("error") is None:
            print(
                f"  ✓ created RFQ {result.get('rfq_id')} for {os.path.basename(folder_path)}"
            )
        else:
            print(
                f"  ✗ failed to create RFQ for {os.path.basename(folder_path)}: {result.get('error')}"
            )

        processed += 1

    print(f"\nTotal RFQs processed: {processed}")
    print(f"Total RFQs skipped: {skipped}")
    return processed


if __name__ == "__main__":
    create_rfqs()
