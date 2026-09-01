from pathlib import Path
import shutil
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description="Initialize/check the project's DVC repository.")
    parser.add_argument("--check", action="store_true", help="Only check DVC status; do not run the DVC pipeline.")
    args = parser.parse_args()

    if shutil.which("dvc") is None:
        raise SystemExit("DVC is not installed. Run: pip install -r requirements.txt")
    if not (ROOT / ".git").exists() and shutil.which("git"):
        run(["git", "init"])
    if not (ROOT / ".dvc").exists():
        run(["dvc", "init"])
    else:
        print("DVC repository already initialized.")

    if args.check:
        run(["dvc", "status"])
        return

    # First-time setup: run the declared DVC stage once to create dvc.lock.
    # The stage invokes the pipeline with --skip-dvc, so it cannot recurse.
    if not (ROOT / "dvc.lock").exists():
        run(["dvc", "repro", "pipeline_outputs"])
    else:
        run(["dvc", "status"])

    print("DVC is initialized. Raw, cleaned and curated Parquet outputs are declared in dvc.yaml.")
    print("No remote is configured; add one with: dvc remote add -d storage <path>")

if __name__ == "__main__":
    main()
