"""OpenAI Images API compatible TeamoRouter adapter."""
from __future__ import annotations
import base64, json, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from image_output_layout import resolve_layout, ImageOutputLayoutError

BASE_URL = "https://api.teamorouter.com/v1/images/generations"
MODELS = ("gpt-image-2.5-flare", "gpt-image-2.5-sunburst")

def run(args):
    key = os.environ.get("TEAMOROUTER_API_KEY", "").strip()
    if not key:
        path = Path.home()/".config/teamorouter/api_key"
        if path.is_file(): key = path.read_text().strip()
    if not key: raise RuntimeError("TeamoRouter API key is missing (TEAMOROUTER_API_KEY or ~/.config/teamorouter/api_key).")
    if args.reference: raise RuntimeError("TeamoRouter image editing is not yet supported by this CLI; omit --reference.")
    model = args.model if args.model in MODELS else "gpt-image-2.5-flare"
    payload={"model":model,"prompt":args.prompt,"n":1}
    if args.size and args.size != "16:9": payload["size"] = args.size
    if args.quality: payload["quality"] = args.quality
    req=Request(BASE_URL,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=args.timeout) as res: body=json.loads(res.read())
    except (HTTPError,URLError) as exc: raise RuntimeError(f"TeamoRouter request failed: {exc}") from exc
    data=body.get("data") or []
    if not data: raise RuntimeError("TeamoRouter returned no image data.")
    layout=resolve_layout(args.output_dir,task_namespace="teamorouter",provider="teamorouter",model=model); layout.prepare()
    files=[]
    for item in data[:1]:
        if item.get("b64_json"): content=base64.b64decode(item["b64_json"]); suffix=".png"
        elif item.get("url"):
            with urlopen(Request(item["url"],headers={"Accept":"image/*"}),timeout=args.timeout) as res: content=res.read(); suffix=".png"
        else: raise RuntimeError("TeamoRouter returned an unsupported image item.")
        path=layout.save_image(content,suffix,args.filename or args.prompt,{"provider":"TeamoRouter","model":model,"size":payload.get("size", ""),"quality":payload.get("quality", ""),"operation":"generation"},original_prompt=args.prompt); files.append(str(path))
    return {"status":"completed","requested":1,"completed":1,"failed":0,"files":files,"tasks":[]}
