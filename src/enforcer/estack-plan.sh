#!/usr/bin/env bash
# estack-plan.sh — Execution plan lifecycle manager
#
# Creates and manages .ai/execution-plan.json for E:Stack Enforcer.
# Ensures Intent→Architecture→Manifestation order with gate conditions.
#
# Usage:
#   estack-plan.sh init "task summary" [S|M|L|XL] [#issue]
#   estack-plan.sh advance          # Next phase
#   estack-plan.sh set-impact       # Mark impact analysis done
#   estack-plan.sh set-dag          # Mark DAG generated
#   estack-plan.sh add-file "path"  # Register analyzed file
#   estack-plan.sh add-decision "d" # Record design decision
#   estack-plan.sh status           # Show current state
#   estack-plan.sh complete         # Mark done
#   estack-plan.sh clean            # Remove plan
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLAN_FILE="$PROJECT_ROOT/.ai/execution-plan.json"
CMD="${1:?Usage: estack-plan.sh <init|advance|set-impact|set-dag|add-file|add-decision|status|complete|clean>}"
shift

case "$CMD" in
  init)
    SUMMARY="${1:?Usage: estack-plan.sh init \"summary\" [S|M|L|XL] [#issue]}"
    COMPLEXITY="${2:-M}"; ISSUE="${3:-}"
    mkdir -p "$(dirname "$PLAN_FILE")"
    python3 -c "
import json; from datetime import datetime, timezone
plan = {'version':'1.0','created_at':datetime.now(timezone.utc).isoformat(),'updated_at':datetime.now(timezone.utc).isoformat(),'current_phase':'intent','intent':{'status':'completed','summary':'$SUMMARY','issue_ref':'$ISSUE','complexity':'$COMPLEXITY'},'architecture':{'status':'pending','files_analyzed':[],'impact_checked':False,'dag_generated':False,'design_decisions':[]},'manifestation':{'status':'pending','files_modified':[],'tests_passed':False}}
with open('$PLAN_FILE','w') as f: json.dump(plan,f,ensure_ascii=False,indent=2)
print(json.dumps(plan,ensure_ascii=False,indent=2))
"
    echo ""; echo "✓ Plan created (phase=intent, complexity=$COMPLEXITY)" ;;
  advance)
    python3 -c "
import json,sys; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: plan=json.load(f)
phase=plan['current_phase']
t={'intent':'architecture','architecture':'manifestation','manifestation':'completed'}
if phase not in t: print(f'Cannot advance from {phase}'); sys.exit(1)
if phase=='architecture' and not plan['architecture'].get('files_analyzed'): print('No files analyzed'); sys.exit(1)
if phase=='architecture': plan['architecture']['status']='completed'
if phase=='manifestation': plan['manifestation']['status']='completed'
plan['current_phase']=t[phase]; plan['updated_at']=datetime.now(timezone.utc).isoformat()
if t[phase]=='manifestation': plan['manifestation']['status']='in_progress'
with open('$PLAN_FILE','w') as f: json.dump(plan,f,ensure_ascii=False,indent=2)
print(f'✓ {phase} → {t[phase]}')
" ;;
  set-impact)
    python3 -c "
import json; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: p=json.load(f)
p['architecture']['impact_checked']=True; p['updated_at']=datetime.now(timezone.utc).isoformat()
with open('$PLAN_FILE','w') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print('✓ impact_checked=true')
" ;;
  set-dag)
    python3 -c "
import json; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: p=json.load(f)
p['architecture']['dag_generated']=True; p['updated_at']=datetime.now(timezone.utc).isoformat()
with open('$PLAN_FILE','w') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print('✓ dag_generated=true')
" ;;
  add-file)
    FILE="${1:?Usage: estack-plan.sh add-file \"path\"}"
    python3 -c "
import json; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: p=json.load(f)
if '$FILE' not in p['architecture']['files_analyzed']: p['architecture']['files_analyzed'].append('$FILE')
p['updated_at']=datetime.now(timezone.utc).isoformat()
with open('$PLAN_FILE','w') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print(f'✓ Added: $FILE')
" ;;
  add-decision)
    D="${1:?Usage: estack-plan.sh add-decision \"decision\"}"
    python3 -c "
import json; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: p=json.load(f)
p['architecture']['design_decisions'].append('$D'); p['updated_at']=datetime.now(timezone.utc).isoformat()
with open('$PLAN_FILE','w') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print('✓ Decision added')
" ;;
  status)
    [ ! -f "$PLAN_FILE" ] && echo "No plan." && exit 0
    python3 -c "
import json
with open('$PLAN_FILE') as f: p=json.load(f)
ph=p['current_phase']; i=p.get('intent',{}); a=p.get('architecture',{}); m=p.get('manifestation',{})
icons={'intent':'🎯','architecture':'📐','manifestation':'🔨','completed':'✅'}
print(f'{icons.get(ph,\"?\")} Phase: {ph}')
print(f'  Intent: {i.get(\"status\")} — {i.get(\"summary\",\"?\")[:60]}')
print(f'  Architecture: {a.get(\"status\")} (impact={a.get(\"impact_checked\",False)}, files={len(a.get(\"files_analyzed\",[]))})')
print(f'  Manifestation: {m.get(\"status\")} (tests={m.get(\"tests_passed\",False)})')
" ;;
  complete)
    python3 -c "
import json; from datetime import datetime,timezone
with open('$PLAN_FILE') as f: p=json.load(f)
p['current_phase']='completed'; p['manifestation']['status']='completed'; p['updated_at']=datetime.now(timezone.utc).isoformat()
with open('$PLAN_FILE','w') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print('✅ Completed')
" ;;
  clean) rm -f "$PLAN_FILE"; echo "✓ Removed" ;;
  *) echo "Unknown: $CMD"; exit 1 ;;
esac
