"""Hard gate: LM Studio + Qwen OpenAI-compatible sequential tool calling.

No Paperclip, Drive, memory-os, or network writes other than localhost LM Studio.
"""
import json, os, sys, time, urllib.request
from pathlib import Path

BASE=os.getenv("LM_STUDIO_BASE_URL","http://127.0.0.1:1234/v1").rstrip("/")
MODEL=os.getenv("LM_STUDIO_MODEL","")
OUT=Path(__file__).parent/"artifacts"
OUT.mkdir(exist_ok=True)

def post(path,payload):
    req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer lm-studio"})
    with urllib.request.urlopen(req,timeout=180) as r: return json.load(r)

def get(path):
    req=urllib.request.Request(BASE+path,headers={"Authorization":"Bearer lm-studio"})
    with urllib.request.urlopen(req,timeout=20) as r: return json.load(r)

def tool(name,args):
    if name=="get_alpha": return {"alpha":17}
    if name=="multiply": return {"result":int(args["a"])*int(args["b"])}
    raise ValueError(name)

tools=[
 {"type":"function","function":{"name":"get_alpha","description":"Return deterministic alpha.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
 {"type":"function","function":{"name":"multiply","description":"Multiply two integers.","parameters":{"type":"object","properties":{"a":{"type":"integer"},"b":{"type":"integer"}},"required":["a","b"],"additionalProperties":False}}}
]

try:
    models=get("/models").get("data",[])
    model=MODEL or (models[0]["id"] if models else "")
    if not model: raise RuntimeError("No model exposed by LM Studio")
    messages=[{"role":"system","content":"You are a deterministic tool-use test agent. Never calculate alpha yourself. First call get_alpha. After its result, call multiply with alpha and 3. After the second tool result, answer exactly GATE_PASS=51."},{"role":"user","content":"Run the required two-step tool procedure."}]
    transcript={"base":BASE,"model":model,"turns":[]}
    calls_seen=[]
    for _ in range(6):
        resp=post("/chat/completions",{"model":model,"messages":messages,"tools":tools,"tool_choice":"auto","temperature":0})
        msg=resp["choices"][0]["message"]; transcript["turns"].append(msg); messages.append(msg)
        calls=msg.get("tool_calls") or []
        if calls:
            for c in calls:
                name=c["function"]["name"]; args=json.loads(c["function"].get("arguments") or "{}")
                result=tool(name,args); calls_seen.append(name)
                messages.append({"role":"tool","tool_call_id":c["id"],"content":json.dumps(result)})
            continue
        final=msg.get("content") or ""
        ok=calls_seen[:2]==["get_alpha","multiply"] and "GATE_PASS=51" in final
        transcript["calls_seen"]=calls_seen; transcript["final"]=final; transcript["pass"]=ok
        p=OUT/f"gate-{int(time.time())}.json"; p.write_text(json.dumps(transcript,indent=2),encoding="utf-8")
        print(json.dumps({"pass":ok,"model":model,"calls_seen":calls_seen,"final":final,"artifact":str(p)},ensure_ascii=False))
        sys.exit(0 if ok else 2)
    raise RuntimeError("No terminal answer after tool loop")
except Exception as e:
    print(json.dumps({"pass":False,"error":repr(e)},ensure_ascii=False))
    sys.exit(1)
