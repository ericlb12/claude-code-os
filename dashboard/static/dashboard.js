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
  drawChart((ch.ok && ch.actividad_por_dia) ? [...ch.actividad_por_dia].reverse() : []);

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

  const pl=await get("/api/plugins");
  const cp=document.getElementById("p-plugins"); clear(cp);
  if(pl.ok && (pl.plugins||[]).length){
    pl.plugins.forEach(p=>{
      const box=el("div","plugin");
      box.appendChild(el("div","plugin-nom", p.nombre));
      box.appendChild(el("div","muted", p.para_que));
      box.appendChild(el("div","plugin-uso", "Cómo usar: "+p.como_usar));
      cp.appendChild(box);
    });
  } else { cp.appendChild(el("div","bad","no disponible")); }
}
const SVGNS="http://www.w3.org/2000/svg";
let _chartSerie=[];   // [{dia, acum}] para el tooltip
function _diaCorto(d){ return (d||"").slice(5); }   // MM-DD

function drawChart(serie){
  const svg=document.getElementById("chart"); clear(svg);
  const empty=document.getElementById("chart-empty");
  const datesEl=document.getElementById("chart-dates"); clear(datesEl);
  if(!serie || serie.length<1){ empty.textContent="sin actividad registrada"; _chartSerie=[]; return; }
  empty.textContent="";
  let cum=0; const pts=serie.map((d,i)=>{ cum+=(d.eventos||0); return {x:i,y:cum,dia:d.dia}; });
  _chartSerie=pts.map(p=>({dia:p.dia, acum:p.y}));
  const n=pts.length, maxY=pts[n-1].y||1;
  const X=i=> n<=1?0:(i/(n-1))*600;
  const Y=y=> 118-(y/maxY)*108;
  const line=pts.map(p=>X(p.x)+","+Y(p.y)).join(" ");
  const area=document.createElementNS(SVGNS,"polygon");
  area.setAttribute("points","0,120 "+line+" 600,120");
  area.setAttribute("fill","rgba(210,80,42,0.14)"); area.setAttribute("stroke","none");
  const poly=document.createElementNS(SVGNS,"polyline");
  poly.setAttribute("points",line); poly.setAttribute("fill","none");
  poly.setAttribute("stroke","#d2502a"); poly.setAttribute("stroke-width","2.5");
  poly.setAttribute("vector-effect","non-scaling-stroke");
  svg.appendChild(area); svg.appendChild(poly);
  // etiquetas de fecha (máx 6, repartidas)
  const maxLbl=Math.min(6,n), step=n<=1?1:(n-1)/(maxLbl-1||1);
  for(let k=0;k<maxLbl;k++){
    const idx=Math.round(k*step);
    datesEl.appendChild(el("span",null,_diaCorto(pts[idx].dia)));
  }
}

// Tooltip: al pasar el cursor, muestra fecha + acumulado del punto más cercano.
(function(){
  const svg=document.getElementById("chart");
  const tip=document.getElementById("chart-tip");
  if(!svg||!tip) return;
  svg.addEventListener("mousemove", e=>{
    if(!_chartSerie.length){ tip.style.display="none"; return; }
    const rect=svg.getBoundingClientRect();
    const frac=Math.min(1,Math.max(0,(e.clientX-rect.left)/rect.width));
    const idx=Math.round(frac*(_chartSerie.length-1));
    const p=_chartSerie[idx];
    tip.textContent=p.dia+" · "+p.acum.toLocaleString()+" acum.";
    tip.style.display="block";
    tip.style.left=(e.clientX-rect.left+12)+"px";
    tip.style.top="6px";
  });
  svg.addEventListener("mouseleave", ()=>{ tip.style.display="none"; });
})();

refresh(); setInterval(refresh, 30000);

async function post(p, body){ try{ const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); return await r.json(); }catch(e){ return {ok:false,error:String(e)}; } }
function setOutput(text){ document.getElementById("run-output").textContent = text; }
function setRunState(text){ document.getElementById("run-state").textContent = text; }

async function runPrompt(){
  const texto=document.getElementById("run-prompt").value.trim();
  if(!texto){ setRunState("escribe algo primero"); return; }
  setRunState("ejecutando…"); setOutput("");
  const res=await post("/api/run",{prompt:texto});
  setRunState(res.ok?"ok":"error");
  setOutput(res.ok ? (res.output||"(sin salida)") : ("ERROR: "+(res.error||"")));
}

async function runScript(id){
  if(id==="ver_cron_log"){ const r=await get("/api/cron-log"); setOutput(r.ok ? (r.texto||"(vacío)") : ("ERROR: "+(r.error||""))); setRunState("cron.log"); return; }
  if(id==="ver_informe"){ const r=await get("/api/report"); setOutput(r.ok ? (r.contenido||"(vacío)") : ("ERROR: "+(r.error||""))); setRunState(r.ok&&r.fecha?("informe "+r.fecha):"informe"); return; }
  setRunState("ejecutando "+id+"…"); setOutput("");
  const res=await post("/api/run-script",{id});
  setRunState(res.ok?"ok":"error");
  setOutput(res.ok ? (res.output||"(sin salida)") : ("ERROR: "+(res.error||"")));
}

document.getElementById("run-btn").addEventListener("click", runPrompt);
document.querySelectorAll(".run-actions .btn").forEach(b=>{
  b.addEventListener("click", ()=>runScript(b.getAttribute("data-script")));
});
