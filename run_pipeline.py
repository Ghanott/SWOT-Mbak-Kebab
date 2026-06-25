import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

scripts = [
    "scripts/merge_data.py",
    "scripts/generate_zone_summary.py",
    "scripts/generate_zone_scoring.py",
    "scripts/generate_swot.py",
    "scripts/export_landing_json.py"
]

print("=== STARTING DATA PIPELINE ===")
for script in scripts:
    script_path = BASE_DIR / script
    print(f"\nRunning {script}...")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print("Error encountered:")
        print(result.stderr.strip())
        sys.exit(1)

print("\n=== PIPELINE COMPLETED SUCCESSFULLY! ===")
