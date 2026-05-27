async function get(p){ try{ const r=await fetch(p); return await r.json(); }catch(e){ return {ok:false,error:String(e)}; } }
function el(tag, cls, text){ const e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
function clear(node){ while(node.firstChild) node.removeChild(node.firstChild); }
function rowEl(left, right, rightCls){
  const r=el("div","row"); r.appendChild(el("span",null,left)); r.appendChild(el("span",rightCls,right)); return r;
}
function fill(id, ok, items, makeRow){
  const c=document.getElementById(id); clear(c);
  if(!ok){ c.appendChild(el("div","bad","no disponible")); return; }
  if(!items.length){ c.appendChild(el("div","muted","sin datos")); return; }
  items.forEach(it=>c.appendChild(makeRow(it)));
}
function setText(id, v){ document.getElementById(id).textContent = v; }

async function refresh(){
  setText("reloj", new Date().toLocaleString());

  const ch=await get("/api/claude-health");
  setText("m-tokens", ch.ok ? (ch.tokens_in+ch.tokens_out).toLocaleString() : "n/d");

  const inter=await get("/api/interactions");
  setText("m-inter", inter.ok ? inter.total : "n/d");
  fill("p-inter", inter.ok, inter.ok?inter.recientes:[],
       i=>rowEl(i.input||"—", i.error?"error":"ok", i.error?"bad":"muted"));

  const err=await get("/api/errors");
  setText("m-err", err.ok ? err.grupos.reduce((a,g)=>a+g.count,0) : "n/d");
  fill("p-errors", err.ok, err.ok?err.grupos:[],
       g=>rowEl(g.error_type+" · "+g.signal, "x"+g.count, "bad"));

  const runs=await get("/api/runs");
  fill("p-runs", runs.ok, runs.ok?runs.runs:[],
       r=>rowEl(r.ts, r.status, r.status==="ok"?"ok":"bad"));

  const fr=await get("/api/freshness");
  fill("p-fresh", fr.ok, fr.ok?fr.tablas:[],
       t=>rowEl(t.tabla, (t.al_dia?"al día":"desfasado")+" ("+(t.dias==null?"?":t.dias)+"d)", t.al_dia?"ok":"bad"));

  const etl=await get("/api/etl");
  setText("m-etl", (etl.ok&&etl.ultima)?etl.ultima.status:"n/d");
  const ce=document.getElementById("p-etl"); clear(ce);
  if(etl.ok&&etl.ultima){
    ce.appendChild(rowEl("última: "+etl.ultima.run_at, etl.ultima.status, etl.ultima.status==="success"?"ok":"bad"));
    ce.appendChild(rowEl("productos / alertas", etl.ultima.products_found+" / "+etl.ultima.alerts_generated, "muted"));
  } else { ce.appendChild(el("div","bad","no disponible")); }
}
refresh(); setInterval(refresh, 30000);
