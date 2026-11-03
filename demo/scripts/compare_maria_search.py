"""Run three fresh console conversations; retain answers, evidence, calls and timing."""
import json, os, subprocess, sys
from pathlib import Path
from compass.data_collection import DataCollection

root=Path(__file__).resolve().parents[2]
phase=sys.argv[1]
question='Which berths had the most crane idle hours last month?'
results=[]
for number in range(1,4):
    folder=root/'tmp/search_comparison'/phase/str(number)
    folder.mkdir(parents=True,exist_ok=False)
    run=subprocess.run([sys.executable,'console.py','--test'],cwd=root/'demo',
        input=f'maria\n{question}\n/quit\n',capture_output=True,text=True,timeout=360,
        env={**os.environ,'FARO_COLLECTION_PATH':str(folder),'FARO_REFERENCE_DATE':'2026-11-03'})
    (folder/'console.txt').write_text(run.stdout+'\n'+run.stderr)
    store=DataCollection(folder)
    turns=[turn for p in (folder/'harbor/conversations').glob('*.parquet')
           for turn in store.read_conversation('harbor',p.stem)['turns']]
    turn=turns[0] if turns else {}
    response=turn.get('response',{})
    result=dict(run=number,exit_code=run.returncode,status=turn.get('status'),elapsed_ms=turn.get('elapsed_ms'),
        answer=response.get('answer'),search=response.get('search'),evidence=response.get('evidence'),
        cache=turn.get('cache'),model_explanations=turn.get('model_explanations'),model_attempts=turn.get('model_attempts'))
    results.append(result)
    (root/'tmp/search_comparison'/f'{phase}.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({k:result[k] for k in ('run','status','elapsed_ms','answer')}),flush=True)
