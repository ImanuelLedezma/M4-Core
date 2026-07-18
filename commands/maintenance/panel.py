import asyncio
import datetime
import hashlib
import hmac
import html
import json
import os
import sys
import pathlib

from aiohttp import web
from discord.ext import commands

PANEL_PORT     = int(os.getenv("PANEL_PORT", "8765"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "changeme-panel-secret")
ENV_FILE       = ".env"
HOSTNAME       = os.getenv("PANEL_HOSTNAME", "m4-core")
BOTUSER        = os.getenv("PANEL_USER", "root")

def _make_token(pin: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), pin.encode(), hashlib.sha256).hexdigest()

def _check_token(request: web.Request) -> bool:
    token = request.cookies.get("panel_token")
    if not token:
        return False
    pin = os.getenv("PANEL_PIN", "")
    return bool(pin) and hmac.compare_digest(token, _make_token(pin))

def _read_env() -> dict:
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env

def _write_env(env: dict):
    with open(ENV_FILE, "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")

def _mask(v: str) -> str:
    if len(v) <= 6:
        return "***"
    return v[:3] + "***" + v[-3:]

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>panel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0a0a0a;--term:#0e0e0e;--border:#1c1c1c;--green:#39ff6e;--red:#ff4444;--yellow:#f0c040;--cyan:#00d4ff;--muted:#444;--text:#c8c8c8;}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.06) 2px,rgba(0,0,0,.06) 4px);pointer-events:none;z-index:9999}
#app{display:flex;flex-direction:column;height:100vh;max-width:920px;margin:0 auto;padding:12px}
.titlebar{display:flex;align-items:center;gap:8px;padding:7px 14px;background:var(--term);border:1px solid var(--border);border-bottom:none;border-radius:8px 8px 0 0}
.dot{width:11px;height:11px;border-radius:50%}
.dot-r{background:#ff5f57}.dot-y{background:#febc2e}.dot-g{background:#28c840}
.tlabel{flex:1;text-align:center;color:var(--muted);font-size:11px;letter-spacing:.1em}
#terminal{flex:1;overflow-y:auto;background:var(--term);border:1px solid var(--border);padding:14px 16px;scroll-behavior:smooth}
#terminal::-webkit-scrollbar{width:3px}
#terminal::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.ln{line-height:1.75;white-space:pre-wrap;word-break:break-all}
.g{color:var(--green)}.r{color:var(--red)}.y{color:var(--yellow)}.c{color:var(--cyan)}.m{color:var(--muted)}.t{color:var(--text)}
.input-row{display:flex;align-items:center;background:var(--term);border:1px solid var(--border);border-top:1px solid #151515;border-radius:0 0 8px 8px;padding:9px 16px}
#prompt{white-space:nowrap;user-select:none;margin-right:6px}
#cmd{flex:1;background:transparent;border:none;outline:none;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;caret-color:var(--green)}
#login{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;gap:6px}
.logo{color:var(--green);font-size:10.5px;line-height:1.4;letter-spacing:.05em;text-align:center;margin-bottom:18px;opacity:.9}
#login-status{color:var(--muted);font-size:12px}
.lrow{display:flex;align-items:center;gap:8px;margin-top:6px}
.lrow span{color:var(--green)}
#pin{background:transparent;border:none;outline:none;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;caret-color:var(--green);width:220px}
.blink{animation:bl 1s step-end infinite}
@keyframes bl{50%{opacity:0}}
.hidden{display:none!important}
</style>
</head>
<body>

<div id="login">
  <div class="logo">
&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9556;  &#9608;&#9608;&#9608;&#9608;&#9608;&#9556; &#9608;&#9608;&#9608;&#9608;&#9488;  &#9608;&#9608;&#9488;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9488;&#9608;&#9608;&#9488;<br>
&#9608;&#9608;&#9554;&#9552;&#9552;&#9608;&#9608;&#9554;&#9552;&#9488;&#9608;&#9608;&#9554;&#9552;&#9552;&#9608;&#9608;&#9556;&#9608;&#9608;&#9608;&#9608;&#9488; &#9608;&#9608;&#9553;&#9608;&#9608;&#9554;&#9552;&#9552;&#9552;&#9552;&#9588;&#9608;&#9608;&#9553;<br>
&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9554;&#9552;&#9588; &#9608;&#9608;&#9553;  &#9608;&#9608;&#9553;&#9608;&#9608;&#9554;&#9608;&#9608;&#9488;&#9608;&#9608;&#9553;&#9608;&#9608;&#9608;&#9608;&#9608;&#9556;  &#9608;&#9608;&#9553;<br>
&#9608;&#9608;&#9554;&#9552;&#9552;&#9552;&#9552;&#9588; &#9608;&#9608;&#9553;  &#9608;&#9608;&#9553;&#9608;&#9608;&#9553; &#9608;&#9608;&#9608;&#9608;&#9553;&#9608;&#9608;&#9554;&#9552;&#9552;&#9588;  &#9608;&#9608;&#9553;<br>
&#9608;&#9608;&#9553;     &#9568;&#9608;&#9608;&#9608;&#9608;&#9608;&#9554;&#9552;&#9588;&#9608;&#9608;&#9553; &#9568;&#9608;&#9608;&#9608;&#9553;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9556;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9608;&#9556;<br>
&#9568;&#9552;&#9588;     &#9568;&#9552;&#9552;&#9552;&#9552;&#9588; &#9568;&#9552;&#9588;&#9568;&#9552;&#9588;  &#9568;&#9552;&#9552;&#9588;&#9568;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9588;&#9568;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9588;
  </div>
  <div id="login-status">enter PIN to authenticate</div>
  <div class="lrow">
    <span>PIN &gt;</span>
    <input id="pin" type="password" autocomplete="off" spellcheck="false">
    <span class="blink">_</span>
  </div>
</div>

<div id="app" class="hidden">
  <div class="titlebar">
    <div class="dot dot-r"></div>
    <div class="dot dot-y"></div>
    <div class="dot dot-g"></div>
    <div class="tlabel" id="tlabel">panel</div>
  </div>
  <div id="terminal"></div>
  <div class="input-row">
    <div id="prompt"></div>
    <input id="cmd" autocomplete="off" spellcheck="false">
  </div>
</div>

<script>
const HOSTNAME = __HOSTNAME__;
const BOTUSER  = __BOTUSER__;

let cwd = '/';
let hist = [], hidx = -1;

const $login  = document.getElementById('login');
const $app    = document.getElementById('app');
const $term   = document.getElementById('terminal');
const $cmd    = document.getElementById('cmd');
const $pin    = document.getElementById('pin');
const $prompt = document.getElementById('prompt');
const $tlabel = document.getElementById('tlabel');
const $lstatus= document.getElementById('login-status');

function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

function setPrompt(){
  $prompt.innerHTML=`<span class="g">${esc(BOTUSER)}</span><span class="m">@</span><span class="c">${esc(HOSTNAME)}</span><span class="m">:</span><span class="y">${esc(cwd)}</span><span class="g">$ </span>`;
  $tlabel.textContent=`${BOTUSER}@${HOSTNAME}:${cwd}`;
}

function p(text,cls='t'){
  const d=document.createElement('div');
  d.className='ln '+cls;
  d.textContent=text;
  $term.appendChild(d);
  $term.scrollTop=$term.scrollHeight;
}
function ph(html,cls='t'){
  const d=document.createElement('div');
  d.className='ln '+cls;
  d.innerHTML=html;
  $term.appendChild(d);
  $term.scrollTop=$term.scrollHeight;
}
function echoPrompt(cmd){
  ph(`<span class="g">${esc(BOTUSER)}</span><span class="m">@</span><span class="c">${esc(HOSTNAME)}</span><span class="m">:</span><span class="y">${esc(cwd)}</span><span class="g">$ </span><span class="t">${esc(cmd)}</span>`);
}

$pin.focus();
$pin.addEventListener('keydown', async e=>{
  if(e.key!=='Enter')return;
  const pin=$pin.value; $pin.value='';
  $lstatus.textContent='authenticating...';$lstatus.className='';
  const r=await api('/api/login',{pin});
  if(r.ok){
    $login.classList.add('hidden');$app.classList.remove('hidden');
    $cmd.focus(); setPrompt(); boot();
  } else {
    $lstatus.textContent='✖ wrong PIN';
    $lstatus.style.color='var(--red)';
  }
});

function boot(){
  p(`panel  |  ${BOTUSER}@${HOSTNAME}  |  type help for commands`,'g');
  p('');
}

$cmd.addEventListener('keydown', async e=>{
  if(e.key==='Enter'){
    const raw=$cmd.value.trim(); $cmd.value='';
    if(!raw)return;
    hist.unshift(raw); hidx=-1;
    echoPrompt(raw);
    await dispatch(raw);
    p('');
  } else if(e.key==='ArrowUp'){
    e.preventDefault();
    if(hidx<hist.length-1){hidx++;$cmd.value=hist[hidx];}
  } else if(e.key==='ArrowDown'){
    e.preventDefault();
    if(hidx>0){hidx--;$cmd.value=hist[hidx];}else{hidx=-1;$cmd.value='';}
  } else if(e.key==='l'&&e.ctrlKey){
    e.preventDefault(); $term.innerHTML='';
  }
});
document.addEventListener('click',()=>$cmd.focus());

async function dispatch(raw){
  const parts=raw.trim().split(/\s+/);
  const cmd=parts[0].toLowerCase();
  const args=parts.slice(1);
  switch(cmd){
    case 'help':    return cmdHelp();
    case 'clear':
    case 'cls':     $term.innerHTML=''; return;
    case 'logout':
    case 'exit':    return cmdLogout();
    case 'uptime':  return cmdUptime();
    case 'restart': return cmdRestart();
    case 'reload':  return cmdReload();
    case 'env':     return cmdEnv(args);
    case 'pull':    return cmdPull(args[0]||'main');
    case 'pwd':     p(cwd); return;
    case 'cd':      return cmdCd(args[0]);
    default:        return cmdShell(raw);
  }
}

function cmdHelp(){
  p('commands:','c');
  const cmds=[
    ['uptime','bot uptime'],
    ['env','list .env vars (masked)'],
    ['env get <KEY>','reveal value of KEY'],
    ['env set <KEY> <VAL>','set env var'],
    ['env del <KEY>','delete env var'],
    ['pull [main|canary]','git pull + reload cogs'],
    ['reload','reload all cogs'],
    ['restart','restart bot process'],
    ['cd <path>','change directory'],
    ['clear','clear screen'],
    ['logout','end session'],
    ['<any shell cmd>','run on machine'],
  ];
  cmds.forEach(([c,d])=>{
    ph(`  <span class="c">${esc(c.padEnd(22))}</span><span class="m">${esc(d)}</span>`);
  });
}

async function cmdUptime(){
  const r=await api('/api/uptime');
  p(r.uptime||'error','g');
}
async function cmdRestart(){
  p('restarting bot...','y');
  await api('/api/restart',{});
  p('signal sent.','m');
}
async function cmdReload(){
  p('reloading cogs...','c');
  const r=await api('/api/reload',{});
  (r.results||[]).forEach(l=>p(l,l.startsWith('✖')?'r':'g'));
}
async function cmdEnv(args){
  const sub=(args[0]||'').toLowerCase();
  if(!sub){
    const r=await api('/api/env');
    const env=r.env||{};
    if(!Object.keys(env).length){p('(empty)','m');return;}
    Object.entries(env).forEach(([k,v])=>{
      ph(`  <span class="c">${esc(k)}</span><span class="m">=</span><span class="y">${esc(v)}</span>`);
    });
    return;
  }
  if(sub==='get'){
    if(!args[1]){p('usage: env get <KEY>','r');return;}
    const r=await api('/api/env/get',{key:args[1]});
    if(r.value!==undefined) ph(`<span class="c">${esc(args[1])}</span><span class="m">=</span><span class="y">${esc(r.value)}</span>`);
    else p(`"${args[1]}" not found`,'r');
    return;
  }
  if(sub==='set'){
    if(!args[1]||!args[2]){p('usage: env set <KEY> <VALUE>','r');return;}
    const val=args.slice(2).join(' ');
    const r=await api('/api/env/set',{key:args[1],value:val});
    p(r.ok?`✓ ${args[1]} updated`:'failed',r.ok?'g':'r');
    return;
  }
  if(sub==='del'||sub==='delete'){
    if(!args[1]){p('usage: env del <KEY>','r');return;}
    const r=await api('/api/env/del',{key:args[1]});
    p(r.ok?`✓ ${args[1]} deleted`:'not found',r.ok?'g':'r');
    return;
  }
  p(`unknown subcommand: ${sub}`,'r');
}
async function cmdPull(branch){
  if(!['main','canary'].includes(branch)){p('usage: pull [main|canary]','r');return;}
  p(`pulling from ${branch}...`,'c');
  const r=await api('/api/git/pull',{branch});
  if(r.ok){
    p(r.output||'already up to date.','g');
    p('reloading cogs...','c');
    (r.reloads||[]).forEach(l=>p(l,l.startsWith('✖')?'r':'g'));
  } else p('✖ '+(r.error||'pull failed'),'r');
}
async function cmdCd(path){
  if(!path){cwd='/';setPrompt();return;}
  const r=await api('/api/cd',{path,cwd});
  if(r.ok){cwd=r.cwd;setPrompt();}
  else p(`cd: ${r.error}`,'r');
}
async function cmdShell(cmd){
  const r=await api('/api/shell',{cmd,cwd});
  const out=(r.output||'').trimEnd();
  if(out) p(out,r.code===0?'t':'r');
  if(r.new_cwd){cwd=r.new_cwd;setPrompt();}
}

async function api(path,body){
  try{
    const opts=body!==undefined
      ?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}
      :{method:'GET'};
    const r=await fetch(path,opts);
    if(r.status===401){cmdLogout();return{};}
    return await r.json();
  }catch(e){return{error:String(e)};}
}

function cmdLogout(){
  fetch('/api/logout',{method:'POST'}).finally(()=>{
    $app.classList.add('hidden');
    $login.classList.remove('hidden');
    $lstatus.textContent='enter PIN to authenticate';
    $lstatus.style.color='';
    $pin.value='';$pin.focus();
    $term.innerHTML='';
    cwd='/';
  });
}
</script>
</body>
</html>
"""

async def handle_index(request: web.Request):
    page = PAGE \
        .replace("__HOSTNAME__", f'"{html.escape(HOSTNAME)}"') \
        .replace("__BOTUSER__",  f'"{html.escape(BOTUSER)}"')
    return web.Response(content_type="text/html", text=page)

def _json(data: dict, status: int = 200) -> web.Response:
    return web.Response(content_type="application/json", text=json.dumps(data), status=status)

def _text(data: str, status: int = 200) -> web.Response:
    return web.Response(content_type="text/plain", text=data, status=status)

def _auth(request: web.Request):
    if not _check_token(request):
        raise web.HTTPUnauthorized()

async def route_login(request: web.Request):
    body = await request.json()
    pin  = body.get("pin", "").strip()
    correct = os.getenv("PANEL_PIN", "")
    if not correct or pin != correct:
        return _json({"ok": False})
    resp = _json({"ok": True})
    resp.set_cookie("panel_token", _make_token(pin), httponly=True, samesite="Strict", max_age=86400*7)
    return resp

async def route_logout(request: web.Request):
    resp = _json({"ok": True})
    resp.del_cookie("panel_token")
    return resp

async def route_uptime(request: web.Request):
    _auth(request)
    cog: "Panel" = request.app["cog"]
    d = datetime.datetime.now(datetime.timezone.utc) - cog.start_time
    h, rem  = divmod(int(d.total_seconds()), 3600)
    m, s    = divmod(rem, 60)
    days, h = divmod(h, 24)
    parts = []
    if days: parts.append(f"{days}d")
    if h:    parts.append(f"{h}h")
    if m:    parts.append(f"{m}m")
    parts.append(f"{s}s")
    return _json({"uptime": "  ".join(parts)})

def _resolve_cwd(cwd: str) -> str:
    base = pathlib.Path(".").resolve()
    if cwd in ("/", ""):
        return str(base)
    target = (base / cwd.lstrip("/")).resolve()
    try:
        target.relative_to(base)
        return str(target) if target.is_dir() else str(base)
    except ValueError:
        return str(base)

async def route_neofetch(request: web.Request):
    neofetch = """
      _____
     /     \\        root@m4-core
    |  o o  |       -----------------
    |   ^   |       OS: Windows
    |  \\___/ |
     \\_____/        Shell: powershell
    /|  |  |\\       Resolution: 0x0 (assumed headless)
   /_|__|__|_\\      DE: null
      |  |          WM: null
      |  |          Terminal: web-panel-stdin
     /____\\         Terminal Font: JetBrains Mono

     GPU: integrated
     Locale: C.UTF-8, EN.US
"""

    return _text(neofetch)

async def route_shell(request: web.Request):
    _auth(request)
    body    = await request.json()
    cmd     = body.get("cmd", "").strip()
    real_cwd= _resolve_cwd(body.get("cwd", "/"))
    if not cmd:
        return _json({"output": "", "code": 0})
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=real_cwd,
        )
        so, se = await asyncio.wait_for(proc.communicate(), timeout=60)
        return _json({"output": (so.decode()+se.decode()).rstrip(), "code": proc.returncode})
    except asyncio.TimeoutError:
        return _json({"output": "timed out after 60s", "code": 1})
    except Exception as e:
        return _json({"output": str(e), "code": 1})

async def route_cd(request: web.Request):
    _auth(request)
    body = await request.json()
    base = pathlib.Path(".").resolve()
    cur  = pathlib.Path(_resolve_cwd(body.get("cwd","/")))
    target = (cur / body.get("path","")).resolve()
    try:
        target.relative_to(base)
        if not target.is_dir():
            return _json({"ok": False, "error": "not a directory"})
        rel = "/" + str(target.relative_to(base))
        return _json({"ok": True, "cwd": rel if rel != "/." else "/"})
    except Exception as e:
        return _json({"ok": False, "error": str(e)})

async def route_env_list(request: web.Request):
    _auth(request)
    env = _read_env()
    return _json({"env": {k: _mask(v) for k, v in env.items()}})

async def route_env_get(request: web.Request):
    _auth(request)
    body = await request.json()
    key  = body.get("key","").strip()
    env  = _read_env()
    val  = env.get(key) or os.getenv(key)
    return _json({"value": val} if val is not None else {"error": "not found"})

async def route_env_set(request: web.Request):
    _auth(request)
    body  = await request.json()
    key   = body.get("key","").strip()
    value = body.get("value","")
    if not key:
        return _json({"ok": False})
    env = _read_env(); env[key] = value; _write_env(env)
    os.environ[key] = value
    return _json({"ok": True})

async def route_env_del(request: web.Request):
    _auth(request)
    body = await request.json()
    key  = body.get("key","").strip()
    env  = _read_env()
    if key not in env:
        return _json({"ok": False})
    del env[key]; _write_env(env)
    return _json({"ok": True})

async def route_restart(request: web.Request):
    _auth(request)
    cog: "Panel" = request.app["cog"]
    asyncio.ensure_future(_do_restart(cog.bot))
    return _json({"ok": True})

async def _do_restart(bot):
    await asyncio.sleep(0.3)
    await asyncio.create_subprocess_exec(
        sys.executable, "main.py",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await bot.close()

async def route_reload(request: web.Request):
    _auth(request)
    cog: "Panel" = request.app["cog"]
    return _json({"ok": True, "results": await _do_reload(cog.bot)})

async def _do_reload(bot) -> list:
    results = []
    for root, _, files in os.walk("./commands"):
        for f in files:
            if not f.endswith(".py") or f.startswith("__"):
                continue
            path = os.path.relpath(os.path.join(root, f), ".").replace(os.sep, ".").removesuffix(".py")
            try:
                await bot.reload_extension(path); results.append(f"√ {path}")
            except commands.ExtensionNotLoaded:
                try:   await bot.load_extension(path); results.append(f"√ {path} (new)")
                except Exception as e: results.append(f"✖ {path}: {e}")
            except Exception as e:
                results.append(f"✖ {path}: {e}")
    return results

async def route_git_pull(request: web.Request):
    _auth(request)
    body   = await request.json()
    branch = body.get("branch","main")
    if branch not in ("main","canary"):
        return _json({"ok": False, "error": "invalid branch"})
    try:
        proc = await asyncio.create_subprocess_shell(
            f"git fetch origin && git reset --hard origin/{branch}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        so, se = await proc.communicate()
        if proc.returncode != 0:
            return _json({"ok": False, "error": se.decode().strip()})
        cog: "Panel" = request.app["cog"]
        reloads = await _do_reload(cog.bot)
        return _json({"ok": True, "output": so.decode().strip(), "reloads": reloads})
    except Exception as e:
        return _json({"ok": False, "error": str(e)})

class Panel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot       = bot
        self.start_time= datetime.datetime.now(datetime.timezone.utc)
        self._runner   = None
        self._task     = None

    async def cog_load(self) -> None:
        self._task = asyncio.create_task(self._start())

    async def cog_unload(self):
        if self._task:    self._task.cancel()
        if self._runner:  await self._runner.cleanup()

    async def _start(self):
        try:
            app = web.Application()
            app["cog"] = self
            app.router.add_get ("/",             handle_index)
            app.router.add_post("/api/login",    route_login)
            app.router.add_post("/api/logout",   route_logout)
            app.router.add_get ("/api/uptime",   route_uptime)
            app.router.add_post("/api/shell",    route_shell)
            app.router.add_post("/api/cd",       route_cd)
            app.router.add_get ("/api/env",      route_env_list)
            app.router.add_post("/api/env/get",  route_env_get)
            app.router.add_post("/api/env/set",  route_env_set)
            app.router.add_post("/api/env/del",  route_env_del)
            app.router.add_post("/api/restart",  route_restart)
            app.router.add_post("/api/reload",   route_reload)
            app.router.add_post("/api/git/pull", route_git_pull)
            self._runner = web.AppRunner(app)
            await self._runner.setup()
            await web.TCPSite(self._runner, "0.0.0.0", PANEL_PORT).start()
            import logging; logging.getLogger("panel").info("http://0.0.0.0:%s", PANEL_PORT)
        except Exception:
            import logging; logging.getLogger("panel").exception("failed to start panel")

async def setup(bot: commands.Bot):
    await bot.add_cog(Panel(bot))
