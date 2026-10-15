
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "note_matching_results.csv"

PIPELINE = [
    "src/detect_anomalies.py",
    "src/match_notes.py",
    "src/validate_output.py",
]


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run_pipeline():
    for script in PIPELINE:
        subprocess.run(
            [sys.executable, str(ROOT / script)],
            cwd=ROOT,
            check=True,
        )


def main():
    hashes = []

    for run_number in range(1, 4):
        print(f"\n===== RUN {run_number} =====")
        run_pipeline()

        if not OUTPUT_FILE.exists():
            raise FileNotFoundError(
                f"Expected output was not created: {OUTPUT_FILE}"
            )

        file_hash = sha256_file(OUTPUT_FILE)
        hashes.append(file_hash)
        print(f"SHA-256: {file_hash}")

    if len(set(hashes)) == 1:
        print("\nPASS: All three runs produced identical output files.")
    else:
        print("\nFAIL: Output changed between runs.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
