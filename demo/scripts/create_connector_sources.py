"""One fictional Harbor release in three native formats. Rerun to reset these fixtures."""
import argparse
import json
from pathlib import Path
import sqlite3
from openpyxl import Workbook
from reportlab.pdfgen.canvas import Canvas


def create(root):
    root.mkdir(parents=True,exist_ok=True)
    path=root/"operations.sqlite"
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE event_revisions(ticket TEXT, revision INTEGER, code TEXT, minutes INTEGER, withdrawn INTEGER, period TEXT, PRIMARY KEY(ticket,revision))")
        db.executemany("INSERT INTO event_revisions VALUES(?,?,?,?,?,?)",[
            ("N-17",1,"I",6600,0,"2026-10"),("N-17",2,"I",6000,0,"2026-10"),
            ("N-21",1,"I",5160,0,"2026-10"),("S-09",1,"I",6900,0,"2026-10"),
            ("S-12",1,"I",4260,0,"2026-10"),("N-88",1,"M",1800,0,"2026-10"),
            ("S-89",1,"I",1200,0,"2026-10"),("S-89",2,"I",1200,1,"2026-10")])
        db.execute("""CREATE VIEW current_events AS SELECT ticket,code,minutes,period FROM event_revisions e
            WHERE NOT withdrawn AND revision=(SELECT MAX(revision) FROM event_revisions WHERE ticket=e.ticket)""")
    wb=Workbook(); ws=wb.active;ws.title="Assignments"
    ws.append(["Work reference","Terminal","Berth","Equipment"])
    for row in [("N-17","North","N1","C01"),("N-21","North","N2","C01"),
                ("S-09","South","S1","C02"),("S-12","South","S2","C02"),("N-88","North","N2","C01")]:
        ws.append(row)
    wb.save(root/"allocation.xlsx")
    pdf=Canvas(str(root/"operations_note.pdf"),invariant=1);t=pdf.beginText(45,790)
    for line in [
        "Harbor | October 2026 operations release | reviewed 1 November 2026",
        "This release covers all berths at North and South for the full calendar month.",
        "Use the current_events view: corrections replace earlier revisions; withdrawals are excluded.",
        "Code I counts as idle time; code M is maintenance and is excluded. Units are minutes.",
        "A ticket is one posted total at a single berth. ticket and Work reference identify the same posting.",
        "Allocation must contain exactly one assignment per counted ticket. Equipment names alone are not keys.",
        "If any counted ticket has no assignment, the berth ranking is incomplete. Do not rank.",
        "Berths in scope: N1, N2, S1 and S2. This note contains no ranking."]:
        t.textLine(line)
    pdf.drawText(t);pdf.save()
    grants=[dict(company="harbor",scopes=["harbor_north","harbor_south"],file=f)
            for f in ["operations.sqlite","allocation.xlsx","operations_note.pdf"]]
    (root/"connections.json").write_text(json.dumps(grants,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path(__file__).resolve().parents[1]/"connector/fixtures")
    create(parser.parse_args().out)
