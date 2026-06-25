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
    REPLY_SENT_MARKER,
    RFQ_INFO_MARKER,
)
from sevenrights.api.post_rfq import create_rfq


def create_rfqs(
    download_dir: str = DOWNLOADS_DIR,
    exclude: tuple = ("junk",),
    subfolder: str = None,
    dry_run: bool = False,
    test_run: bool = True,
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
        sent_marker_path = os.path.join(folder_path, REPLY_SENT_MARKER)
        info_marker_path = os.path.join(folder_path, RFQ_INFO_MARKER)

        if not test_run:
            if not os.path.exists(excel_marker_path):
                print(
                    f"  -> Skipping (no {RFQ_EXCEL_MARKER}): {os.path.basename(folder_path)}"
                )
                skipped += 1
                continue

            if os.path.exists(sent_marker_path):
                print(
                    f"  -> Skipping (reply already sent): {os.path.basename(folder_path)}"
                )
                skipped += 1
                continue

        rfq_data = None
        if not test_run and os.path.exists(excel_marker_path):
            try:
                with open(excel_marker_path, "r", encoding="utf-8") as f:
                    rfq_data = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                with open(info_marker_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"error": str(e), "rfq_id": None},
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
                print(
                    f"  ✗ invalid JSON in {RFQ_EXCEL_MARKER} for {os.path.basename(folder_path)}: {e}"
                )
                skipped += 1
                continue

        if dry_run:
            mode = "test-run" if test_run else "dry-run"
            print(f"  [{mode}] would create RFQ for {os.path.basename(folder_path)}")
            processed += 1
            continue

        result = create_rfq(data=rfq_data)

        # TODO: Revisit this — currently writes rfq_info.json even in test_run.
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
