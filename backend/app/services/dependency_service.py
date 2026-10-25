"""
DataPulse AI - Pipeline Dependency & Blast Radius Service
Queries pipeline graph from Exasol, calculates downstream impact propagation,
and evaluates organizational blast radius when a data pipeline degrades or fails.
"""

from typing import Any, Dict, List, Set
from collections import deque

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import BlastRadiusReport, DependencyGraphResponse, GraphEdge, GraphNode


# Mapping of pipelines to downstream business reporting and consumer applications
PIPELINE_BUSINESS_IMPACT = {
    "PIPE_CUST_MASTER": ["Customer 360 BI Portal", "CRM Sync Service", "Sales Commission Calculator"],
    "PIPE_CUST_ORDER": ["Executive Revenue Dashboard", "Order Fulfillment Dispatch", "Customer Invoicing Portal"],
    "PIPE_PAY_RECON": ["Daily Financial Closing System", "General Ledger Audit Feed", "Treasury Liquidity Monitor"],
    "PIPE_INV_SYNC": ["Automated Warehouse Dispatch", "Real-Time Stock Availability API", "Supplier Reorder Trigger"],
    "PIPE_FIN_DAILY": ["CFO Daily Flash Report", "Regulatory Capital Adequacy Model", "SEC Compliance Archive"],
    "PIPE_SALES_ANL": ["Regional Sales Scorecard", "Territory Quota Tracker", "Customer Churn Predictor"],
    "PIPE_SUPPLIER_IMP": ["Procurement Vendor Scorecards", "PO Automation Queue", "Contract Compliance Monitor"],
    "PIPE_BI_REFRESH": ["Enterprise PowerBI Gateway", "Executive Tableau Server", "Ad-Hoc SQL Data Warehouse"],
    "PIPE_LOGIST_TRK": ["Fleet Dispatch Console", "Carrier Performance Matrix", "Delivery SLA Tracker"],
    "PIPE_BILLING_TX": ["Automated Payment Gateway", "Accounts Receivable Ledger", "Tax Calculation Engine"],
    "PIPE_USER_ACT": ["Product Analytics Mixpanel Feed", "Recommendation ML Engine", "Fraud Scoring Service"],
    "PIPE_MRKT_ATTRIB": ["Marketing Campaign ROI Dashboard", "Ad Spend Allocation Engine", "Channel Conversion Model"]
}


class DependencyService:
    def get_dependency_graph(self) -> DependencyGraphResponse:
        """
        Fetch all pipelines and directed dependencies from Exasol to construct graph.
        """
        # Fetch nodes
        nodes_query = f"""
            SELECT 
                p.pipeline_id,
                p.pipeline_name,
                p.pipeline_type,
                p.criticality,
                p.owner_team,
                COALESCE(r.status, 'HEALTHY') as latest_status,
                r.error_count
            FROM {settings.EXASOL_SCHEMA}.PIPELINES p
            LEFT JOIN (
                SELECT pipeline_id, status, error_count,
                       ROW_NUMBER() OVER (PARTITION BY pipeline_id ORDER BY start_time DESC) as rn
                FROM {settings.EXASOL_SCHEMA}.PIPELINE_RUNS
            ) r ON p.pipeline_id = r.pipeline_id AND r.rn = 1
            ORDER BY p.pipeline_name ASC
        """
        node_rows = exasol_client.execute_query(nodes_query)

        # Fetch edges
        edges_query = f"""
            SELECT upstream_pipeline_id, downstream_pipeline_id, dependency_type
            FROM {settings.EXASOL_SCHEMA}.PIPELINE_DEPENDENCIES
        """
        edge_rows = exasol_client.execute_query(edges_query)

        nodes: List[GraphNode] = []
        for row in node_rows:
            raw_status = row.get("LATEST_STATUS") or "HEALTHY"
            status = "HEALTHY"
            if raw_status == "FAILED" or int(row.get("ERROR_COUNT") or 0) > 0:
                status = "FAILED"
            elif raw_status == "DEGRADED":
                status = "WARNING"

            nodes.append(GraphNode(
                id=row.get("PIPELINE_ID"),
                name=row.get("PIPELINE_NAME"),
                type=row.get("PIPELINE_TYPE"),
                criticality=row.get("CRITICALITY"),
                status=status,
                owner=row.get("OWNER_TEAM")
            ))

        edges: List[GraphEdge] = []
        for row in edge_rows:
            edges.append(GraphEdge(
                source=row.get("UPSTREAM_PIPELINE_ID"),
                target=row.get("DOWNSTREAM_PIPELINE_ID"),
                type=row.get("DEPENDENCY_TYPE") or "HARD_BLOCKING"
            ))

        return DependencyGraphResponse(nodes=nodes, edges=edges)

    def calculate_blast_radius(self, pipeline_id: str) -> BlastRadiusReport:
        """
        Perform BFS downstream traversal from the specified pipeline to identify
        all cascading dependencies, compute impact score, and aggregate impacted business reports.
        """
        # 1. Fetch pipeline details
        p_query = f"""
            SELECT pipeline_id, pipeline_name, criticality 
            FROM {settings.EXASOL_SCHEMA}.PIPELINES 
            WHERE pipeline_id = '{pipeline_id}'
        """
        p_rows = exasol_client.execute_query(p_query)
        p_name = p_rows[0].get("PIPELINE_NAME") if p_rows else pipeline_id
        criticality = p_rows[0].get("CRITICALITY") if p_rows else "MEDIUM"

        # 2. Fetch all edges
        edges_query = f"""
            SELECT d.upstream_pipeline_id, d.downstream_pipeline_id, d.dependency_type,
                   p.pipeline_name as downstream_name, p.criticality as downstream_criticality,
                   p.owner_team as downstream_owner
            FROM {settings.EXASOL_SCHEMA}.PIPELINE_DEPENDENCIES d
            JOIN {settings.EXASOL_SCHEMA}.PIPELINES p ON d.downstream_pipeline_id = p.pipeline_id
        """
        edges = exasol_client.execute_query(edges_query)

        # Build adjacency list: upstream -> list of downstreams
        adj: Dict[str, List[Dict[str, Any]]] = {}
        for e in edges:
            u = e.get("UPSTREAM_PIPELINE_ID")
            if u not in adj:
                adj[u] = []
            adj[u].append({
                "pipeline_id": e.get("DOWNSTREAM_PIPELINE_ID"),
                "pipeline_name": e.get("DOWNSTREAM_NAME"),
                "criticality": e.get("DOWNSTREAM_CRITICALITY"),
                "owner_team": e.get("DOWNSTREAM_OWNER"),
                "dependency_type": e.get("DEPENDENCY_TYPE")
            })

        # BFS downstream
        visited: Set[str] = set()
        queue = deque([pipeline_id])
        affected_downstream = []
        depth_map = {pipeline_id: 0}

        while queue:
            curr = queue.popleft()
            curr_depth = depth_map[curr]
            for child in adj.get(curr, []):
                cid = child["pipeline_id"]
                if cid not in visited:
                    visited.add(cid)
                    depth_map[cid] = curr_depth + 1
                    affected_downstream.append({
                        "pipeline_id": cid,
                        "pipeline_name": child["pipeline_name"],
                        "criticality": child["criticality"],
                        "owner_team": child["owner_team"],
                        "dependency_type": child["dependency_type"],
                        "hop_distance": curr_depth + 1
                    })
                    queue.append(cid)

        # Aggregate affected business reports
        impacted_reports: Set[str] = set()
        for r in PIPELINE_BUSINESS_IMPACT.get(pipeline_id, []):
            impacted_reports.add(f"{r} (Direct System)")
        for node in affected_downstream:
            nid = node["pipeline_id"]
            for r in PIPELINE_BUSINESS_IMPACT.get(nid, []):
                impacted_reports.add(f"{r} (via {node['pipeline_name']})")

        # Compute total blast radius impact score (0.0 - 100.0)
        # Base on pipeline criticality + downstream count + downstream criticalities
        crit_weights = {"CRITICAL": 30.0, "HIGH": 20.0, "MEDIUM": 10.0, "LOW": 5.0}
        score = crit_weights.get(criticality.upper(), 15.0)

        for node in affected_downstream:
            w = crit_weights.get(node["criticality"].upper(), 10.0)
            dist = node["hop_distance"]
            # Decay with distance
            score += w / (dist * 1.2)

        score = min(100.0, round(score, 1))

        return BlastRadiusReport(
            incident_pipeline_id=pipeline_id,
            incident_pipeline_name=p_name,
            severity=criticality,
            affected_downstream_pipelines=affected_downstream,
            affected_business_reports=sorted(list(impacted_reports)),
            total_impact_score=score
        )


dependency_service = DependencyService()
