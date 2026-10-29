#!/usr/bin/env python3
"""Read US Apple public metadata/reviews. Never purchase, log in or infer revenue."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import ssl
import subprocess
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch(url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'ProductIdeaResearch/0.1 (public research)'}),timeout=25) as response:
            return dict(status='available',url=url,accessed_at=datetime.now(timezone.utc).isoformat(),transport='python',data=json.load(response))
    except URLError as e:
        # Some macOS Python installs do not share the system trust store.
        # System curl keeps TLS verification enabled; never use --insecure.
        if isinstance(e.reason, ssl.SSLCertVerificationError) and shutil.which('curl'):
            try:
                p=subprocess.run(['curl','--fail','--silent','--show-error','--proto','=https','--max-time','25',url],capture_output=True,text=True,timeout=30)
                if p.returncode==0:
                    return dict(status='available',url=url,accessed_at=datetime.now(timezone.utc).isoformat(),transport='system-curl',data=json.loads(p.stdout))
                reason='TLSFallbackHTTPOrNetworkError'
            except (subprocess.TimeoutExpired, ValueError):
                reason='TLSFallbackTimeoutOrInvalidJSON'
        else:
            reason=type(e.reason).__name__
        return dict(status='unavailable',url=url,accessed_at=datetime.now(timezone.utc).isoformat(),reason=reason)
    except Exception as e:
        return dict(status='unavailable',url=url,accessed_at=datetime.now(timezone.utc).isoformat(),reason=type(e).__name__)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['search','lookup','reviews']);p.add_argument('--term');p.add_argument('--id');p.add_argument('--pages',type=int,default=1);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.action=='search':
        if not a.term:p.error('--term required')
        urls=['https://itunes.apple.com/search?'+urlencode(dict(term=a.term,country='us',entity='software',limit=50))]
    else:
        if not a.id or not a.id.isdigit():p.error('numeric --id required')
        if not 1<=a.pages<=10:p.error('--pages must be 1..10')
        urls=['https://itunes.apple.com/lookup?'+urlencode(dict(id=a.id,country='us'))] if a.action=='lookup' else [f'https://itunes.apple.com/us/rss/customerreviews/page={n}/id={a.id}/sortby=mostrecent/json' for n in range(1,a.pages+1)]
    results=[fetch(u) for u in urls]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(dict(country='us',action=a.action,results=results),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(output=str(a.out),statuses=[r['status'] for r in results]),ensure_ascii=False))


if __name__=='__main__':main()
