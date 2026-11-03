"""Readers return native fields and original row/page locations. No business rules."""
from contextlib import closing
import sqlite3

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from pypdf import PdfReader

LIMIT = 500


def quote(name):
    return '"' + name.replace('"', '""') + '"'


class SQLite:
    def __init__(self, path):
        self.path = path

    def connect(self):
        return closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True))

    def items(self):
        with self.connect() as db:
            names = db.execute("SELECT name FROM sqlite_schema WHERE type IN ('table','view') AND name NOT GLOB 'sqlite_*' ORDER BY name")
            return {name: [r[1] for r in db.execute("SELECT * FROM pragma_table_info(?)",(name,))] for name, in names}

    def read(self, name, fields):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = list(db.execute(f"SELECT * FROM {quote(name)} LIMIT ?", (LIMIT+1,)))
            keys = [r[1] for r in db.execute("SELECT * FROM pragma_table_info(?) ORDER BY pk",(name,)) if r[5]]
        refs = [f"{name}:" + (",".join(f"{k}={r[k]}" for k in keys) if keys else f"result row {i}") for i,r in enumerate(rows,1)]
        return [{k:r[k] for k in fields} for r in rows],refs


class Excel:
    def __init__(self, path):
        self.path = path

    def book(self):
        return closing(load_workbook(self.path,read_only=True,data_only=True))

    def items(self):
        with self.book() as book:
            return {s.title:list(next(s.values)) for s in book if s.sheet_state=="visible" and s.max_row}

    def read(self, name, fields):
        with self.book() as book:
            sheet=book[name]
            values=iter(sheet.values)
            header=list(next(values))
            rows,refs=[],[]
            for i,values_row in enumerate(values,2):
                if all(v is None for v in values_row):
                    continue
                rows.append({k:values_row[header.index(k)] for k in fields})
                refs.append(f"{name}!A{i}:{get_column_letter(len(header))}{i}")
                if len(rows)>LIMIT:
                    break
        return rows,refs


class PDF:
    def __init__(self, path):
        self.path = path

    def items(self):
        return {"pages":["page","text"]}

    def read(self, name, fields):
        doc=PdfReader(self.path)
        rows=[];refs=[]
        for i,page in enumerate(doc.pages[:LIMIT+1],1):
            record={"page":i,"text":page.extract_text() or ""}
            if not record["text"].strip():
                raise ValueError(f"Page {i} has no readable text; OCR is not configured.")
            rows.append({k:record[k] for k in fields})
            refs.append(f"page {i}")
        return rows,refs


READERS = {".sqlite": SQLite, ".xlsx": Excel, ".pdf": PDF}
