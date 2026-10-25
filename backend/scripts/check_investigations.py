import httpx

incs = httpx.get('http://127.0.0.1:8000/api/incidents').json()
print(f"Total incidents: {len(incs)}")
for i in incs:
    inv = httpx.get(f"http://127.0.0.1:8000/api/investigation/{i['incident_id']}").json()
    print(f"Incident: {i['incident_id']} ({i.get('pipeline_name')})")
    print(f"  Probable Cause: {inv.get('probable_cause')}")
    print(f"  Evidence Points ({len(inv.get('evidence_points', []))}):")
    for ev in inv.get('evidence_points', []):
        print(f"    - [{ev.get('category')}] {ev.get('finding')} (Metric: {ev.get('metric_value')}, Baseline: {ev.get('baseline_value')})")
    print(f"  Suggested Actions ({len(inv.get('suggested_actions', []))}):")
    for act in inv.get('suggested_actions', []):
        print(f"    * {act}")
    print(f"  LLM Analysis: {inv.get('llm_analysis')[:80]}...")
    print("-" * 50)
