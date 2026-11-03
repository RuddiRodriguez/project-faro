from hashlib import sha256
import json
from pathlib import Path
import os

from api_objects.faro.connector.output.connector_output import SourceItem
from connector.source_reader_output import SourceReaderOutput
from connector.readers import READERS


class SourceReader:
    def __init__(self, root: Path):
        self.root=root

    def read(self, request):
        items=[]
        grants=json.loads((self.root/"connections.json").read_text())
        for grant in grants:
            allowed = sorted(set(grant["scopes"]).intersection(request.permitted_scope_ids))
            if grant["company"]!=request.company_id or not allowed or (not grant.get("scope_field") and not set(grant["scopes"]).issubset(request.permitted_scope_ids)):
                continue
            path=self.root/grant["file"]
            reader=READERS[path.suffix](path)
            version=sha256(path.read_bytes()).hexdigest()
            for name,fields in reader.items().items():
                item=SourceItem(id=f"{path.stem}/{name}",kind=path.suffix[1:],location=f"{path.name}#{name}",
                                fields=fields,scope_ids=allowed,version=version)
                if request.action=="discover":
                    items.append(item)
                elif item.id==request.item:
                    if request.action=="inspect":
                        return SourceReaderOutput(items=[item])
                    columns=request.fields or fields
                    if not set(columns).issubset(fields):
                        raise ValueError("Unknown source fields.")
                    rows,refs=reader.read(name,fields if grant.get("scope_field") else columns)
                    if grant.get("scope_field"):
                        selected = [(row,ref) for row,ref in zip(rows,refs) if row[grant["scope_field"]] in allowed]
                        rows = [{field:row[field] for field in columns} for row,ref in selected]
                        refs = [ref for row,ref in selected]
                    if sha256(path.read_bytes()).hexdigest()!=version:
                        raise ValueError("Source changed during the read.")
                    content=path.read_bytes()
                    if sha256(content).hexdigest()!=version:
                        raise ValueError("Source changed before saving its document.")
                    folder=Path(os.getenv("FARO_DOCUMENT_PATH", Path(__file__).resolve().parents[5]/"local_data/source_documents"))
                    document_name = path.name
                    document_version = version
                    if grant.get("scope_field"):
                        content = json.dumps({name:rows},ensure_ascii=False,indent=2).encode()
                        document_version = sha256(content).hexdigest()
                        document_name = f"{path.stem}-{name}-permitted.json"
                    saved=folder/request.company_id/document_version/document_name
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    saved.write_bytes(content)
                    return SourceReaderOutput(items=[item],rows=rows,references=[f"{path.name}#{r}" for r in refs],
                        document=dict(name=document_name,uri=saved.resolve().as_uri(),version=document_version))
        if request.action!="discover":
            raise PermissionError("Item is not available in this scope.")
        return SourceReaderOutput(items=items)
