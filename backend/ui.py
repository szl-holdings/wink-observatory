"""Python Gradio dashboard, including interactive 3D visual metaphor.

This is a stylized representation of public fleet metadata, not a biological
measurement or a claim about a real C. elegans nervous system.
"""
from __future__ import annotations
from html import escape
import math

import gradio as gr
import plotly.graph_objects as go

from backend.live_data import snapshot, research, summary
from backend.admission import training_decision, compute_status
from backend.live_sources import status as public_space_status
from backend.ena_catalog import sample as ena_sample
from backend.falsifiability import public_audit

CSS = """
.gradio-container{max-width:1460px!important}
.hero{background:linear-gradient(115deg,#101d37,#11455e,#192445);
border:1px solid #2c6b80;border-radius:16px;padding:25px;color:#edfbff}
.hero h1{font-size:2.4rem;margin:0}.hero p{color:#b3dfe7}
"""
COLOR = {"running":"#2de4be","parked":"#b6a5f5","degraded":"#ffbf60",
         "stopped":"#fa7283","complete":"#61ceff"}

def worm_figure(groups: list[dict]):
    """Non-anatomical 3D compute metaphor generated entirely from Python."""
    n = max(len(groups), 1)
    xs = [i / 20 for i in range(121)]
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=xs, y=[.35*math.sin(x*2.4) for x in xs],
        z=[.18*math.cos(x*2) for x in xs], mode="lines",
        line=dict(color="#6bc3ef",width=13), showlegend=False, hoverinfo="skip"))
    for i, row in enumerate(groups):
        x = 6*(i+1)/(n+1)
        state = row.get("status","unknown")
        fig.add_trace(go.Scatter3d(
            x=[x],y=[.35*math.sin(x*2.4)],z=[.18*math.cos(x*2)],
            mode="markers", showlegend=False,
            marker=dict(size=10,color=COLOR.get(state,"#999999")),
            text=[str(row.get("name","?"))[:60]+" · "+str(state)],
            hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(scene=dict(xaxis=dict(visible=False),yaxis=dict(visible=False),
                                 zaxis=dict(visible=False),bgcolor="#0b172a"),
                      paper_bgcolor="#0b172a",font=dict(color="#d5eafb"),
                      margin=dict(l=0,r=0,b=0,t=0),height=405,
                      annotations=[dict(text="STYLIZED COMPUTE STATUS - NOT ANIMAL DATA",
                                        x=.5,y=.02,xref="paper",yref="paper",
                                        showarrow=False,font=dict(color="#b9c8db",size=11))])
    return fig

def dashboard():
    s = snapshot()
    ev = summary(s)
    docs = s.get("docs") or {}
    fleet = docs.get("fleet") or {}
    groups = fleet.get("groups") or []
    held = docs.get("heldout") or {}
    train = training_decision(s)
    host = compute_status()
    arithmetic_audit = public_audit(s)
    banner = ("### Feed: **"+escape(ev["source_state"])+"** · Dataset revision: "+
              escape(ev["dataset_revision"] or "UNKNOWN")+"\n"+
              "**Readback UTC:** "+escape(ev["readback_at"] or "UNAVAILABLE")+
              " · **Provider snapshot UTC:** "+escape(ev["source_snapshot_at"] or "UNKNOWN")+
              " · **Producer telemetry:** "+escape(ev["producer_telemetry_state"])+
              " ("+str(ev["producer_snapshot_age_seconds"])+" s old)"+
              "\n\n**Instrument stream:** NOT CONNECTED · **Lab signature:** NOT VERIFIED. "+
              "Current public dataset metadata is distinct from current experiments.")
    overview = ("### Methods and evidence\n"+
                "**Provider-reported groups:** "+str(ev["provider_reported_groups"])+
                " · **Provider-reported active:** "+str(ev["provider_reported_active"])+
                " · **Itemized with operator status:** "+str(ev["operator_itemized"])+
                "\n\n**Part D records:** "+str(ev["witness_records"])+
                " · **Protocol frozen:** "+str(ev["protocol_frozen"])+
                " · **Held-out assessment:** "+escape(str(ev["heldout_verdict"]))+
                "\n\nThese counts have distinct denominators. A9 trippability and A10 "+
                "neutral-accuracy findings remain open; recorded passes are not scientific qualification.")
    group_rows = [[str(g.get(k,""))[:160] for k in ("name","lane","status","detail")]
                  for g in groups]
    criteria = []
    for row in held.get("criteria") or []:
        audit = row.get("trippability_audit") or {}
        criteria.append([str(row.get("id",""))[:80],
                         str(row.get("recorded_pass","UNKNOWN")),
                         str(audit.get("can_trip","UNKNOWN")),
                         str(row.get("a10_status",audit.get("finding","UNKNOWN")))[:180]])
    gates = [[g["id"],g["state"],g["scope"]] for g in train["gates"]]
    return (banner,worm_figure(groups),group_rows,overview,criteria,gates,
            {"evidence":ev,"training":train,"compute":host,"public_space":public_space_status()}, arithmetic_audit)

def publications():
    r=research()
    label="### Europe PMC public literature: **"+r["state"]+"** (not lab instrument data)"
    table=[[row[k] for k in ("title","pubYear","authorString","doi")]
           for row in r["papers"]]
    return label,table

def sequencing():
    """Live public ENA accession catalog, never private biological assay results."""
    result = ena_sample()  # Public button must respect ten-minute cache/rate budget.
    scope = ("### EMBL-EBI ENA: **"+result["state"]+"**\n"+
             "Fixed NCBI taxonomy: 6239 (*C. elegans*). At most six catalog records. "+
             "Bounded sample, **not a census**, not a live experiment, "+
             "not labeled material authorized for model training.\n\n"+
             "Source: [official ENA taxonomy-search documentation]"+
             "(https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-based-search.html)")
    rows=[[str(record.get(k) or "")[:140] for k in
           ("run_accession","study_accession","sample_accession","instrument_platform","first_public")]
          for record in result.get("records", [])]
    return scope, rows


def build_ui():
    with gr.Blocks(title="WINK Observatory | SZL Holdings",css=CSS) as ui:
        gr.HTML('<div class="hero"><h1>WINK / WET-LAB OBSERVATORY</h1>'+
                '<p>Live public evidence · Python-first science infrastructure · Computation with receipts</p>'+
                '<strong>DRAFT PROTOCOL · NO DIRECT LAB INSTRUMENT STREAM · SCIENTIFIC ADMISSION ON HOLD</strong></div>')
        with gr.Tab("Live observatory"):
            banner=gr.Markdown()
            plot=gr.Plot(label="3D compute status metaphor, not anatomy")
            fleet=gr.Dataframe(headers=["Group","Lane","Status","Evidence note"],
                               datatype=["str"]*4,interactive=False,wrap=True)
            refresh=gr.Button("Refresh public dataset",variant="primary")
        with gr.Tab("Scientific integrity"):
            overview=gr.Markdown()
            criteria=gr.Dataframe(headers=["Criterion","Recorded pass","Can fail?","A10/finding"],
                                  datatype=["str"]*4,interactive=False,wrap=True)
            gr.Markdown("Unknown, missing, low-power or uninterpretable results are never displayed as PROVED.")
            acceptance_arithmetic=gr.JSON(label="Recomputed A9/A10 failure witnesses — mathematical audit only")
        with gr.Tab("Public experimental archive"):
            archive_state=gr.Markdown(
                "ENA data are public sequencing accession metadata; no lab instrumentation is connected.")
            archive_rows=gr.Dataframe(
                headers=["Run accession","Study","Sample","Platform","First public"],
                datatype=["str"]*5,interactive=False,wrap=True)
            gr.Button("Inspect public C. elegans ENA catalog").click(
                sequencing,outputs=[archive_state,archive_rows])
        with gr.Tab("Training + HPC"):
            gates=gr.Dataframe(headers=["Admissibility","State","Required evidence"],
                               datatype=["str"]*3,interactive=False,wrap=True)
            gr.Markdown("**Supercomputer evidence:** public signed-queue receipt readback is "+
                        "available without credentials when enabled; it is NOT a live GPU process witness. "+
                        "No GPU job, inference or laboratory training is launched from this interface.")
        with gr.Tab("Public scientific literature"):
            paper_state=gr.Markdown("Europe PMC is a literature catalog, not live assay evidence.")
            papers=gr.Dataframe(headers=["Title","Year","Authors","DOI"],
                                datatype=["str"]*4,interactive=False,wrap=True)
            gr.Button("Fetch current Europe PMC metadata").click(publications,outputs=[paper_state,papers])
        with gr.Tab("Developer + investor evidence"):
            data=gr.JSON(label="Evidence lineage and decision structure")
            gr.Markdown("Developer HTTP GET routes: /api/v1/observatory, /api/v1/research, "+
                        "/api/v1/training, /api/v1/compute, /api/v1/public-space, /api/v1/sequence-catalog, /api/v1/acceptance-audit, /api/v1/build-info, /healthz, "+
                        "/readyz, /docs. No write or execution endpoints.")
            gr.Markdown("[Source repository](https://github.com/szl-holdings/wink-observatory)"+
                        " · [Pinned public feed](https://huggingface.co/datasets/SZLHOLDINGS/wink-observatory-data)"+
                        " · [Vidal-Gadea Lab](https://agvg75.github.io/lab/)"+
                        " · [Europe PMC](https://europepmc.org/)")
        outputs=[banner,plot,fleet,overview,criteria,gates,data,acceptance_arithmetic]
        ui.load(fn=dashboard,outputs=outputs)
        refresh.click(fn=dashboard,outputs=outputs)
        gr.Timer(value=60).tick(fn=dashboard,outputs=outputs)
    return ui
