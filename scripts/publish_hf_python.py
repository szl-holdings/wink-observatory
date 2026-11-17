"""Single-path HF Space publication. Exact SHA compare-and-swap, no deletion.

Invoked ONLY from the manual owner-admitted GitHub Actions workflow. Never
reads or logs the token value; does not request GPU hardware or training.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from runpy import run_path

from huggingface_hub import HfApi

# -I intentionally excludes local source roots from sys.path. Load only the
# reviewed sibling source by an absolute, fixed path, not a token or PYTHONPATH.
observed_sdk=run_path(str(Path(__file__).resolve().with_name("hf_sdk_card_gate.py")),
                      run_name="_hf_sdk_card_gate")["observed_sdk"]

SPACE="SZLHOLDINGS/wink-observatory"
SHA=re.compile(r"[a-f0-9]{40}\Z")

def require(ok, code):
    if not ok:
        raise SystemExit("HOLD: "+code)

def main():
    source=os.getenv("GITHUB_SHA","")
    expected_source=os.getenv("EXPECTED_MAIN_SHA","")
    expected_hf=os.getenv("EXPECTED_HF_SHA","")
    require(bool(SHA.fullmatch(source)) and source==expected_source, "SOURCE_SHA_NOT_EXACT_MAIN")
    require(bool(SHA.fullmatch(expected_hf)), "HF_ROLLBACK_SHA_UNAVAILABLE")
    require(os.getenv("APPROVED_WINDOW")=="true", "WINDOW_NOT_OPEN")
    require(os.getenv("SDK_MIGRATION_APPROVED")=="true", "SDK_MIGRATION_HOLD")
    require(os.getenv("ROLLBACK_READY")=="true", "ROLLBACK_NOT_READY")
    token=os.getenv("HF_TOKEN")
    require(bool(token), "HF_TOKEN_NOT_CONFIGURED")
    directory=Path("dist/hf-space")
    require(directory.is_dir() and (directory/"Dockerfile").is_file()
            and (directory/"SOURCE_REVISION").read_text().strip()==source,
            "SOURCE_BUNDLE_UNAVAILABLE")
    main=subprocess.run(["git","ls-remote","origin","refs/heads/main"],
                        capture_output=True,timeout=15,check=False)
    require(main.returncode==0 and len(main.stdout)<180
            and main.stdout.decode("ascii","strict").strip()==source+"\trefs/heads/main",
            "PROTECTED_MAIN_MOVED_OR_UNAVAILABLE")
    api=HfApi(token=token)
    info=api.space_info(SPACE)
    require(info.sha==expected_hf and info.private is False, "HF_REVISION_MOVED_OR_PRIVATE")
    sdk=observed_sdk(info.card_data)
    require(sdk in ("static","docker"), "HF_SPACE_SDK_UNEXPECTED")
    # No delete_patterns. Existing Space root HTML/CSS stays in its git history,
    # and rollback must be performed through the owner publisher, not by this script.
    # No owner-publication identity movement is permissible, even after HF metadata read.
    main_final=subprocess.run(["git","ls-remote","origin","refs/heads/main"],
                              capture_output=True,timeout=15,check=False)
    require(main_final.returncode==0 and len(main_final.stdout)<180
            and main_final.stdout.decode("ascii","strict").strip()==source+"\trefs/heads/main",
            "MAIN_MOVED_BEFORE_PROVIDER_COMMIT")
    result=api.upload_folder(
        folder_path=str(directory), path_in_repo="",
        repo_id=SPACE, repo_type="space", revision="main",
        parent_commit=expected_hf,
        commit_message="feat(wink): publish exact GitHub Python observatory "+source[:12])
    revision=getattr(result,"oid",None)
    require(isinstance(revision,str) and SHA.fullmatch(revision), "PUBLISH_RESULT_UNVERIFIED")
    checked=api.space_info(SPACE)
    require(checked.sha==revision, "HF_COMMIT_READBACK_MISMATCH")
    print(json.dumps({"state":"PUBLISHED_UNVERIFIED_RUNTIME",
                      "source_revision":source,"prior_hf_revision":expected_hf,
                      "new_hf_revision":revision,"module_parity_verified":False,
                      "independent_runtime_verified":False,"training_started":False,
                      "gpu_hardware_changed":False},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
