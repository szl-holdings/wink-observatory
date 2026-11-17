"""Read-only reproducibility gate for scientific training. Does not launch training."""
from __future__ import annotations

import json
from backend.live_data import snapshot
from backend.admission import training_decision

def main() -> int:
    report=training_decision(snapshot(force=True))
    print(json.dumps(report,sort_keys=True,indent=2))
    return 0 if report["decision"]=="ADMIT" else 3

if __name__=="__main__":
    raise SystemExit(main())
