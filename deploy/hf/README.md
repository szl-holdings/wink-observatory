---
title: WINK Observatory | SZL Holdings
emoji: "🔬"
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
license: apache-2.0
short_description: Python-first research observability with evidence honesty
tags:
- scientific-reproducibility
- python
- gradio
- fastapi
- governed-ai
- c-elegans
datasets:
- SZLHOLDINGS/wink-observatory-data
pinned: true
---

# WINK Observatory — Python research evidence

This deployment candidate serves the *public* WINK data repository and Europe
PMC literature metadata with explicit source revisions, A9/A10 open scientific
findings, a 3D stylized fleet dashboard, a read-only developer API and an
HPC-training HOLD boundary. It does **not** read real wet-lab instruments or
declare a protocol freeze, biological model quality, lab countersignature or
a running supercomputer training job.

Source: https://github.com/szl-holdings/wink-observatory
Data: https://huggingface.co/datasets/SZLHOLDINGS/wink-observatory-data
Lab: https://agvg75.github.io/lab/
Readiness: /readyz (HTTP 503 if public source is unavailable)
Methods: /docs

The deployed public Space already declares Apache-2.0; preserve that public
card identity until the source owner separately resolves source/HF licensing.

Publication must be via the single source-owned, revision-gated manual workflow.
This candidate may require an HF org plan change for Docker SDK; the existing
static Space is preserved until owner review and explicit deployment admission.
