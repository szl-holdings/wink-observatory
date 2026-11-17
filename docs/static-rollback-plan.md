# Static HTML rollback review plan

The four-file backup alone is not a tested restore. Before reviewing an index-only
rollback, validate the retained archive and current provider state:

```sh
python -m scripts.wink_static_rollback_plan --archive /path/to/four-file-backup \
  --manifest-sha256 REVIEWED_MANIFEST_SHA256 --expected-current CURRENT_HF_SHA
```

This **read-only** command validates all four backup file digests and sizes against
an externally pinned manifest digest, compares the bytes to the immutable public
HF archive revision, and checks that the current public static Space still has
exactly the four files. README, style.css and .gitattributes must be unchanged.
A changed SDK, private repository, extra files, moved head, tampered backup or
redirect refuses the plan. It never uploads or uses credentials.

The result names only index.html and binds `parent_commit` to the reviewed current
HF revision. It is not an approval or reservation: a subsequent authorized writer
must recheck provider identity and use server-enforced `parent_commit`, within the
existing serialized writer group and protected owner-reviewed environment.
Following an authorized restore, verify all four immutable file bytes and the
public browser runtime separately. No automatic rollback or live-restoration
success is implemented or claimed by this change. The full four-file archive is
still retained; this plan refuses broader SDK/config restoration.
