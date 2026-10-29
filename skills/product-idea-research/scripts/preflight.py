#!/usr/bin/env python3
"""Read-only capability inventory. Does not grant permissions or read credentials."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys


def check():
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'python_ok': sys.version_info >= (3,10), 'agent_reach': 'not_configured', 'channels': {}, 'permission_note': 'CLI existence and doctor status do not prove host network/browser permission, target access, or account login.'}
    cli = shutil.which('agent-reach')
    if cli:
        try:
            p = subprocess.run([cli,'doctor'],capture_output=True,text=True,timeout=55)
            if p.returncode == 0:
                doctor = json.loads(p.stdout)
                payload = doctor.get('result', doctor)
                channels = payload.get('channels', [])
                if isinstance(channels, list):
                    result['channels'] = {v['channel']:{field:v.get(field) for field in ('status','level')} for v in channels if isinstance(v,dict) and isinstance(v.get('channel'),str)}
                else:
                    result['channels'] = {k:{field:v.get(field) for field in ('status','active_backend','message')} for k,v in payload.items() if isinstance(v,dict)}
                result['agent_reach'] = 'available' if doctor.get('ok', True) else 'failed'
            else:
                result['agent_reach'] = 'failed'
        except (subprocess.TimeoutExpired, ValueError):
            result['agent_reach'] = 'timeout_or_invalid_response'
    result['tools'] = {k:bool(shutil.which(k)) for k in ('curl','mcporter','gh','opencli','twitter','rdt')}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    d=check();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(d,ensure_ascii=False,indent=2))
    return 0 if d['agent_reach']=='available' and d['python_ok'] else 2


if __name__=='__main__':
    raise SystemExit(main())
