"""Handle native source tables without assigning meaning to a client's column names."""
import json
from hashlib import sha256
import pandas as pd
from utils.connector_client import sources
from bridge.predictor_output import PredictorOutput


def execute_connected(request, read, catalogue, run_read):
    scopes=read.scope_ids or request.permitted_scope_ids
    if not set(scopes).issubset(request.permitted_scope_ids):
        raise PermissionError("Requested scope is not permitted.")
    if read.member_ids:
        raise ValueError("Select members using the actual source fields in the dataframe expression.")
    snapshots=[]
    def fetch(item_id):
        item=catalogue["connected"].get(item_id)
        if not item or not set(item["scope_ids"]).issubset(scopes):
            raise PermissionError("Connected item is not permitted for this scope.")
        result=sources(request.company_id,scopes,"read",item_id)
        current=result.items[0]
        if current.version!=item["version"]:
            raise ValueError("Connected source changed; read the current catalogue.")
        snapshots.append(dict(item=item_id,source=current.location,version=current.version,
                              references=result.references,rows=result.rows,document=result.document))
        return pd.DataFrame(result.rows,columns=current.fields)
    frame=fetch(read.source)
    if read.link:
        other=fetch(read.link.source)
        left,right=read.link.left_field,read.link.right_field
        if left not in frame or right not in other or frame[left].isna().any() or other[right].isna().any():
            raise ValueError("The proposed link has missing fields or keys.")
        if other[right].duplicated().any() or set(frame[left]) != set(other[right]):
            raise ValueError("The proposed link is ambiguous or leaves source records unmatched.")
        frame=frame.merge(other,left_on=left,right_on=right,validate="many_to_one",suffixes=("","_linked"))
    rows=run_read(read.expression,frame.to_dict("records"),list(frame.columns))
    if not rows:
        raise ValueError("No result for the requested connected read.")
    return PredictorOutput(status="ready",company_id=request.company_id,question=request.question,read=read,
        source="; ".join(s["source"] for s in snapshots),data_version=sha256(json.dumps(
            [s["version"] for s in snapshots]).encode()).hexdigest(),rows=rows,
        period="Verify dates against the original source fields or document.",source_evidence=snapshots,
        record_ids=[ref for s in snapshots for ref in s["references"]])
