"""One explicitly amended E7 actor call; preparation and export are offline."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
sys.path.insert(0,str(ROOT.parent/'experiment07'))
import run_probe as e7
sys.path.insert(0,str(REPO/'scripts'))
from export_experiment04 import response, audit_private_sessions
from export_experiment07 import summarize
from public_safety_check import scan_paths

TARGET='t-b6c5207068'
BASE=REPO/'site/data/experiment-07.json'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(v):
    return hashlib.sha256(e7.compact(v).encode()).hexdigest()

def require(ok,msg):
    if not ok:
        raise RuntimeError(msg)

def write(p,v):
    p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())

def context():
    base=read(BASE)
    oldplan=read(ROOT.parent/'experiment07/plan.json')
    require(sha(oldplan)=='c7658352c573dc64bf2597a89db6f3267297f4e862f08080317e4c0b698a77b4','Original plan changed')
    require(not base['completed'] and base['counts']['saved_responses']==23,'Original partial run changed')
    pending=[t for t in base['trials'] if 'action' not in t]
    require(len(pending)==1 and pending[0]['trial_id']==TARGET,'Missing-cell selection changed')
    row=pending[0]
    trial=next(t for t in oldplan['trial_manifest'] if t['trial_id']==TARGET)
    packet=e7.actor_packet(trial)
    require(row['state']['actor_input']==packet and row['state']['actor_input_sha256']==sha(packet),'Committed actor input mismatch')
    require(set(row['forecasts'])==set(e7.VIEWS),'Missing old forecasts')
    for v in e7.VIEWS:
        c=row['forecast_commits'][v]
        require(c['forecast']==row['forecasts'][v] and c['sha256']==sha(c['forecast']),'Forecast commitment changed')
        require(c['call_number'] in (21,22,23),'Forecast timing changed')
    for name,digest in oldplan['source_sha256'].items():
        require(hashlib.sha256((ROOT.parent/'experiment07'/name).read_bytes()).hexdigest()==digest,'Original scientific source changed')
    return base,oldplan,row,trial,packet

def build_plan():
    base,old,row,trial,packet=context()
    return {'extension_id':'experiment-07-extension-01','registration_date':'2026-09-10',
        'maximum_model_calls':1,'model':'gpt-6-astra','effort':'low','trial_id':TARGET,
        'base_dataset_canonical_sha256':sha(base),'original_plan_canonical_sha256':sha(old),
        'actor_input_sha256':sha(packet),'actor_input':packet,
        'instructions':old['instructions']['action'],'schema':trial['world']['action_schema'],
        'forecast_sha256':{v:sha(row['forecasts'][v]) for v in e7.VIEWS},
        'original_source_sha256':old['source_sha256'],
        'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('extension.py','protocol.md')},
        'rule':'One delayed fresh actor; no retries. Preserve original run and forecasts. Separate supplemental and original summaries; combined analysis is exploratory.'}

def check():
    plan=read(ROOT/'plan.json')
    require(plan==build_plan(),'Extension bindings changed')
    return plan

def run(out):
    plan=check()
    pub=read(ROOT/'publication.json')
    require(pub['canonical_plan_sha256']==sha(plan) and len(pub['preregistration_commit'])==40,'Publish extension before inference')
    out=out.resolve()
    require(not out.is_relative_to(REPO),'Private runtime output must be outside public repository')
    stop=int(os.environ.get('ASTRACOTTLE_WEEKLY_STOP_PERCENT','0'))
    require(1<=stop<=100,'Configure local quota guard')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    server=None
    status={'calls_started':0,'completed':False}
    write(out/'status.json',status)
    try:
        sys.path.insert(0,str(ROOT.parent/'pilot'))
        import transport
        transport.ACTOR_DIR=out/'empty_actor'
        transport.STOP_PERCENT=stop
        server=transport.Server()
        require(server.quota()['usedPercent']<stop,'Local quota guard reached')
        start=server.start(plan['instructions'])
        write(out/'request.json',{'instructions':plan['instructions'],'input':plan['actor_input'],'schema':plan['schema'],'call_number':1})
        status['calls_started']=1
        write(out/'status.json',status)
        result=server.turn(start['thread']['id'],e7.compact(plan['actor_input']),plan['schema'])
        write(out/'result.json',{'call_number':1,'input':plan['actor_input'],**result})
        status['completed']=result['status']=='completed'
    except BaseException as exc:
        status['private_error']=type(exc).__name__+': '+str(exc)
        raise
    finally:
        write(out/'status.json',status)
        if server is not None:
            server.close()
    print(json.dumps({'calls_started':status['calls_started'],'response_completed':status['completed']}))

def export(out,original_run,destination):
    plan=check()
    require(read(out/'plan.json')==plan,'Saved extension plan differs')
    require(read(out/'request.json')=={'instructions':plan['instructions'],'input':plan['actor_input'],'schema':plan['schema'],'call_number':1},'Actual request differs')
    base,old,row,trial,packet=context()
    require(read(original_run/TARGET/'committed_state.json')==row['state'],'Original private commitment differs from audited public state')
    for v in e7.VIEWS:
        require(read(original_run/TARGET/('committed_forecast_'+v+'.json'))==row['forecast_commits'][v],'Original private forecast changed')
    require(not (original_run/TARGET/'action.json').exists(),'Original run was modified')
    paths=list(original_run.glob('*/action.json'))+[p for p in original_run.glob('*/forecast_*.json') if not p.name.endswith('.request.json')]
    require(len(paths)==23,'Original saved response count changed')
    sessions=audit_private_sessions(paths+[out/'result.json'])
    decision=response(out/'result.json',packet,plan['schema'],1,e7.e4)
    grade=e7.e4.evaluate(trial['world'],decision['parsed']) if decision['status']=='completed' and not decision['schema_errors'] else None
    combined=copy.deepcopy(base['trials'])
    target=next(t for t in combined if t['trial_id']==TARGET)
    if grade is not None:
        target['action']=decision['parsed']
        target['grade']=grade
    data={'experiment_id':'experiment-07-supplement','date':'2026-09-10','kind':'delayed_one_call_extension',
        'original_run_completed':False,'extension_response_completed':decision['status']=='completed',
        'counts':{'new_model_calls':1,'original_responses':23,'total_responses':24,'original_action_targets':5,
                  'combined_valid_action_targets':5+int(grade is not None and grade['valid'])},
        'original_data':'/data/experiment-07.json','original_dataset_canonical_sha256':sha(base),
        'plan':plan,'publication':read(ROOT/'publication.json'),'trial_id':TARGET,
        'new_action':decision['parsed'],'new_grade':grade,'saved_forecasts':row['forecasts'],
        'original_summary':base['summary'],'combined_exploratory_summary':summarize(combined),
        'runs':copy.deepcopy(base['runs'])+[{'trial_id':TARGET+'-delayed','decisions':[decision]}],
        'audit':{'distinct_application_sessions':sessions,'exact_committed_input_verified':True,'original_forecasts_unchanged':True},
        'limitations':['Delayed collection after prior outcomes were known; explicit amendment to the no-resume protocol.',
                      'Same model service identifier and effort do not guarantee identical service weights across dates.',
                      'Original stopped dataset preserved; supplemented analysis is exploratory, not independent replication.']}
    require(not destination.exists(),'Refusing export overwrite')
    destination.parent.mkdir(parents=True,exist_ok=True)
    write(destination,data)
    require(scan_paths([destination])['status']=='pass','Public privacy scan failed')
    print(json.dumps({'saved_supplemental_responses':1,'new_grade':grade,'combined_valid_targets':data['counts']['combined_valid_action_targets'],'privacy':'pass'}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','check','run','export'):
        modes.add_argument('--'+name,action='store_true')
    p.add_argument('--out',type=Path)
    p.add_argument('--original-run',type=Path)
    p.add_argument('--destination',type=Path)
    args=p.parse_args()
    if args.prepare:
        require(not (ROOT/'plan.json').exists(),'Refusing plan overwrite')
        write(ROOT/'plan.json',build_plan())
        print('Prepared one-call amendment '+sha(check()))
    elif args.check:
        print('Bindings verified '+sha(check()))
    elif args.run:
        require(args.out is not None,'Supply private output directory')
        run(args.out)
    else:
        require(all((args.out,args.original_run,args.destination)),'Supply export paths')
        export(args.out,args.original_run,args.destination)
