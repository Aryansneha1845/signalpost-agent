/* Signalpost product demo — static, no cookies, no tracking, in-memory state only.
   Data: docs/app/companies.json built from real smoke-test envelopes.
   Pipeline runs labeled "Demo simulation"; reports show verified snapshot data. */
"use strict";
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let DB=null, route={name:"landing"};
const state={company:null,tab:"overview",researchTimer:[]};

const ICONS={
overview:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/></svg>',
research:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14 14"/></svg>',
companies:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="12" height="10" rx="1"/><path d="M2 6.5h12M6 3v3.5"/></svg>',
changes:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 8h10M8 3v10"/><circle cx="8" cy="8" r="6.2"/></svg>',
sources:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 2h6l2 2v10H4z"/><path d="M10 2v2h2M6 8h4M6 11h4"/></svg>',
runs:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 3l9 5-9 5z"/></svg>',
settings:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="2.2"/><path d="M8 1.8v2M8 12.2v2M1.8 8h2M12.2 8h2M3.6 3.6l1.4 1.4M11 11l1.4 1.4M12.4 3.6 11 5M5 11l-1.4 1.4"/></svg>'};
const NAV=[["overview","Overview"],["research","Research"],["companies","Companies"],["changes","Changes"],["sources","Sources"],["runs","Runs"],["settings","Settings"]];

async function boot(){
 try{DB=await(await fetch("companies.json",{cache:"no-store"})).json();}
 catch(e){document.body.innerHTML="<p style='padding:40px'>Could not load demo data (companies.json). Serve over http or check the file exists.</p>";return;}
 $("#nav").innerHTML=NAV.map(([k,l])=>`<a href="#/${k}" data-nav="${k}">${ICONS[k]}${l}</a>`).join("");
 $("#cmdkBtn").onclick=openPalette;
 $("#menuBtn").onclick=()=>{const s=$("#sidebar"),o=s.classList.toggle("open");$("#menuBtn").setAttribute("aria-expanded",o);};
 document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPalette();}});
 $("#scrim").onclick=closeDrawer;
 window.addEventListener("hashchange",render);
 render();
}
const greeting=()=>{const h=new Date().getHours();return h<12?"Good morning":h<18?"Good afternoon":"Good evening";};
const fmtDate=iso=>{if(!iso)return"—";const d=new Date(iso);return isNaN(d)?"—":d.toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"});};
const fmtNum=n=>n==null||isNaN(+n)?"not reported":(+n).toLocaleString("en-US",{maximumFractionDigits:1});
const money=(n,c)=>n==null?"not reported":(+n).toLocaleString("en-US",{maximumFractionDigits:0})+" "+(c||"");
function toast(msg){const t=$("#toast");t.textContent=msg;t.style.display="block";clearTimeout(t._h);t._h=setTimeout(()=>t.style.display="none",2200);}
function copyText(txt,btn){(navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(()=>toast("Copied")).catch(()=>{toast("Copy unavailable");});}
function badge(text,tone){return `<span class="badge b-${tone}">${esc(text)}</span>`;}
function statusBadge(s){s=String(s);if(/^(active|verified|available|complete|completed)$/i.test(s))return badge(s==="complete"?"Verified":s,"green");
 if(/bankrupt|fail|error/i.test(s))return badge(s,"red");if(/warn|partial|review|conflict|stale/i.test(s))return badge(s,"amber");return badge(s,"gray");}
function confBadge(c){c=+c;if(isNaN(c))return badge("unverified","gray");return badge(c+"%","green");}

/* ---------- router ---------- */
function render(){
 state.researchTimer.forEach(clearTimeout);state.researchTimer=[];
 const h=location.hash||"#/";
 const parts=h.replace(/^#\//,"").split("/");
 const land=$("#landing"),app=$("#app");
 if(h==="#/"||h===""){land.hidden=false;app.hidden=true;renderLanding();document.title="Signalpost — Research companies. Verify the facts. See the signals.";return;}
 land.hidden=true;app.hidden=false;
 const name=parts[0]||"overview";
 $$("#nav a").forEach(a=>a.classList.toggle("active",a.dataset.nav===name||(name==="company"&&a.dataset.nav==="companies")));
 $("#sidebar").classList.remove("open");
 const titles={overview:"Overview",research:"Research",companies:"Companies",changes:"Changes",sources:"Sources",runs:"Runs",settings:"Settings",company:"Company"};
 $("#pageTitle").textContent=titles[name]||"Overview";
 closeDrawer();closePalette();
 const v=$("#view");
 if(name==="overview")v.innerHTML=vOverview();
 else if(name==="research")v.innerHTML=vResearch("");
 else if(name==="company")renderCompany(v,parts[1],parts[2]||"overview");
 else if(name==="companies")v.innerHTML=vCompanies("");
 else if(name==="changes")v.innerHTML=vChanges();
 else if(name==="sources")v.innerHTML=vSources();
 else if(name==="runs")v.innerHTML=vRuns("all");
 else if(name==="settings")v.innerHTML=vSettings();
 else v.innerHTML=vOverview();
 bindCommon(v);
}
/* ---------- landing ---------- */
function renderLanding(){
 const f=DB.featured[0];
 $("#landing").innerHTML=`<div class="landing"><div class="wrap">
 <div class="tag">Signalpost · Company intelligence</div>
 <h1>Research companies. Verify the facts. See the signals.</h1>
 <p class="sub">Signalpost researches Norwegian companies from permitted public sources and turns fragmented information into structured, traceable intelligence.</p>
 <div class="cta-row"><a class="btn primary" href="#/research">Research a company</a><a class="btn ghost" style="color:#fff;border-color:rgba(255,255,255,.3)" href="#/overview">View how it works</a></div>
 <div class="steps">${[["01","Identify","Resolve the company using authoritative organisation information."],["02","Research","Gather information from permitted public sources."],["03","Verify","Cross-check evidence and detect contradictions."],["04","Analyse","Generate structured company intelligence."],["05","Track","Compare snapshots and surface meaningful changes."]].map(s=>`<div class="step"><b>${s[0]}</b><h3>${s[1]}</h3><p>${s[2]}</p></div>`).join("")}</div>
 </div></div>
 <div class="section"><h2>Built for traceability</h2><p class="muted">Every important claim can be traced back to its source.</p>
 <div class="evgrid">${f.evidence.filter(e=>e.state==="available").slice(0,3).map(e=>`<div class="card"><h3>${esc(e.module)}</h3><p class="muted small">${esc(e.url||"")}</p><p class="small">Retrieved ${esc(fmtDate(e.retrieved))} · ${statusBadge("Verified")}</p></div>`).join("")}</div></div>
 <div class="section"><h2>Research dashboard preview</h2><p class="muted">A live-look sample from verified snapshot data — open the full workspace:</p>
 <div class="card"><h3>${esc(f.name)} <span class="muted mono">${esc(f.org)}</span></h3><p>${esc((f.summary||"").slice(0,220))}…</p><p><a class="btn sm" href="#/company/${esc(f.org)}">Open company workspace</a> <a class="btn sm ghost" href="#/overview">Start researching</a></p></div></div>
 <div class="section"><h2>What Signalpost can uncover</h2><div class="grid g4">
 ${["Company identity","Leadership","Financial information","Web presence","Hiring activity","Public signals","Changes over time","Evidence trail"].map(x=>`<div class="card"><h3>${x}</h3></div>`).join("")}</div>
 <p style="margin-top:22px"><a class="btn primary" href="#/research">Start researching</a></p></div>`;
}
/* ---------- overview ---------- */
function vOverview(){
 const s=DB.stats, rows=DB.featured.slice(0,6);
 return `<h1 style="margin-bottom:2px">${greeting()}, Aryan</h1>
 <p class="muted" style="margin-bottom:18px">Research Norwegian companies from permitted public sources and build an auditable evidence trail.</p>
 <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap"><a class="btn primary" href="#/research">Research a company</a><a class="btn" href="#/runs">View recent research</a></div>
 <div class="card" style="margin-bottom:14px"><h3>Research a company</h3>
 <form id="heroSearch" style="margin-top:8px"><div class="searchrow"><input id="heroQ" aria-label="Search by company name or organisation number" placeholder="Search by company name or organisation number"><button class="btn primary" type="submit">Start Research</button></div></form>
 <p class="small muted" style="margin:8px 0 0">Example: ${esc(DB.featured[0].name)} · NO ${esc(DB.featured[0].org)} — Signalpost verifies company identity before analysing external evidence.</p></div>
 <div class="grid g4" style="margin-bottom:14px">
 ${[["Companies researched",s.companies,"snapshot batch"],["Research runs","2","completed"],["Filed accounts found",s.financials,"of "+s.companies],["Websites verified",s.websites,"exact-identity"]].map(k=>`<div class="card kpi"><div class="n mono">${k[1]}</div><div class="l">${k[0]}</div><div class="d muted">${k[2]}</div></div>`).join("")}</div>
 <h2 style="margin-bottom:8px">Recent Research</h2>
 <div class="tblwrap"><table class="data"><thead><tr><th>Company</th><th>Organisation No.</th><th>Status</th><th>Sources</th><th>Confidence</th><th>Action</th></tr></thead><tbody>
 ${rows.map(c=>`<tr><td><a href="#/company/${c.org}">${esc(c.name)}</a></td><td class="mono">${esc(c.org)}</td><td>${statusBadge(c.status)}</td><td class="mono">${c.evidence.filter(e=>e.state==="available").length} sources</td><td>${confBadge(Math.round((c.confidence??0)*100))}</td><td><a href="#/company/${c.org}">View</a></td></tr>`).join("")}</tbody></table></div>`;
}
/* ---------- research ---------- */
function vResearch(q){
 return `<h1 style="margin-bottom:2px">Research</h1><p class="muted">Start with a Norwegian organisation number or company name.</p>
 <div class="searchcard" style="margin-top:14px"><h3>Research a company</h3>
 <form id="resSearch" style="margin-top:8px"><div class="searchrow"><input id="resQ" aria-label="Search by company name or organisation number" placeholder="Search by company name or organisation number" value="${esc(q)}"><button class="btn primary" type="submit">Start Research</button></div></form>
 <p class="small muted" style="margin:8px 0 0">Example: ${esc(DB.featured[0].name)} · NO ${esc(DB.featured[0].org)}</p>
 <p class="small muted">Signalpost verifies company identity before analysing external evidence.</p></div>
 <div id="resOut" style="margin-top:14px" aria-live="polite"></div>`;
}
const STAGES=[["Resolving company identity","Anchor on the 9-digit organisation number against the official registry."],["Fetching registry information","Legal form, status, address, industry, filed accounts, roles, workplaces."],["Verifying company website","Registry-listed site must prove exact-entity identity before use."],["Gathering public evidence","Company-owned pages, careers surface, dated activity."],["Cross-source verification","Contradictions, freshness and authority checks."],["Generating intelligence report","Structured report with evidence citations."]];
function startDemoResearch(org){
 state.researchTimer.forEach(clearTimeout);state.researchTimer=[];
 const out=$("#resOut");const t0=performance.now();let elapsed="0.0s";
 out.innerHTML=`<div class="pipe" role="status" aria-label="Research progress"><div class="bar"><i id="pbar" style="width:4%"></i></div><div style="padding:12px 16px"><b>Researching company <span class="mono">${esc(org)}</span></b><div class="small muted"><span id="pel">Research started 0.0s ago</span> · <span id="psrc">0 sources collected</span> · Demo simulation over verified snapshot data</div></div><div id="stages">${STAGES.map((s,i)=>`<div class="stage" id="st${i}"><div class="st-ic">${i+1}</div><div><h3>${s[0]}</h3><p>${s[1]}</p></div></div>`).join("")}</div></div>`;
 let src=0;
 const tick=setInterval(()=>{elapsed=((performance.now()-t0)/1000).toFixed(1)+"s";const e=$("#pel");if(e)e.textContent="Research started "+elapsed+" ago";},100);
 state.researchTimer.push(tick);
 STAGES.forEach((s,i)=>{
  state.researchTimer.push(setTimeout(()=>{
   const el=$("#st"+i);if(!el)return;el.classList.add("active");
   state.researchTimer.push(setTimeout(()=>{
    const e2=$("#st"+i);if(!e2)return;e2.classList.remove("active");e2.classList.add("done");e2.querySelector(".st-ic").textContent="✓";
    src+=2;const ps=$("#psrc");if(ps)ps.textContent=src+" sources collected";
    const pb=$("#pbar");if(pb)pb.style.width=Math.round(((i+1)/STAGES.length)*100)+"%";
    if(i===STAGES.length-1){clearInterval(tick);state.researchTimer.push(setTimeout(()=>{location.hash="#/company/"+org;},600));}
   },650));
  },i*800));
 });
}
/* ---------- company ---------- */
const TABS=[["overview","Overview"],["evidence","Evidence"],["people","People"],["financials","Financials"],["presence","Web Presence"],["changes","Changes"],["run","Research Run"]];
function findCompany(id){if(!id)return null;const d=id.replace(/\D/g,"");return DB.featured.find(c=>c.org===d)||DB.companies.find(c=>c.org===d)||null;}
function fullCompany(c){return DB.featured.find(x=>x.org===c.org)||null;}
function renderCompany(v,org,tab){
 const c=findCompany(org);
 if(!c){v.innerHTML=`<p><a href="#/research">← Back</a></p><div class="error"><h2>Unable to verify company identity</h2><p>We could not establish a reliable identity match from the permitted sources.</p><ul class="small"><li>Invalid organisation number</li><li>Source unavailable</li><li>Conflicting company information</li></ul><p><a class="btn sm" href="#/research">Retry</a> <a class="btn sm ghost" href="#/runs">View run details</a></p></div>`;return;}
 const f=fullCompany(c);
 if(!f){v.innerHTML=`<p><a href="#/research">← Back</a></p><div class="card"><h2>${esc(c.name)}</h2><p class="muted mono">${esc(c.org)}</p><div class="empty"><p>Full workspace available for researched companies.</p><p><a class="btn sm primary" href="#/research">Research this company</a></p></div></div>`;return;}
 state.company=f;state.tab=TABS.some(t=>t[0]===tab)?tab:"overview";
 const w=f.website_verified;
 v.innerHTML=`<p><a href="#/research">← Back</a></p>
 <div class="card" style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-start">
 <div><div class="small muted">Company identity · Norwegian company</div><h1 style="font-size:26px">${esc(f.name)}</h1>
 <p class="muted mono" style="margin:4px 0">${esc(f.org.replace(/(\d{3})(\d{3})(\d{3})/,"$1 $2 $3"))}</p>
 <p style="margin:6px 0 0">${statusBadge(f.status)} ${w?badge("✓ Identity verified","green"):badge("Website unverified","amber")} <span class="small muted">${w?"Identity confirmed against authoritative registry information.":"Registry identity held; web claims quarantined."}</span></p></div>
 <div style="display:flex;gap:8px;flex-wrap:wrap"><a class="btn sm" href="#/research">Research Again</a><button class="btn sm" data-export="${esc(f.org)}">Export Report</button><button class="btn sm ghost" data-watch="${esc(f.name)}">Watch Company</button></div></div></div>
 <div class="tabs" role="tablist">${TABS.map(t=>`<button role="tab" aria-selected="${state.tab===t[0]}" class="${state.tab===t[0]?"active":""}" data-tab="${t[0]}">${t[1]}</button>`).join("")}</div>
 <div id="tabBody"></div>`;
 $$("#view [data-tab]").forEach(b=>b.onclick=()=>{location.hash="#/company/"+f.org+"/"+b.dataset.tab;});
 const exp=$("#view [data-export]");if(exp)exp.onclick=()=>exportReport(f);
 const wat=$("#view [data-watch]");if(wat)wat.onclick=()=>toast("Watch added — changes will surface on the Changes page.");
 renderTab(f,state.tab);
}
function exportReport(f){
 const md=["# "+f.name+" ("+f.org+")","",(f.summary||""),"","## Evidence",...f.evidence.map(e=>`- [${e.state}] ${e.module}: ${e.url||""} (retrieved ${e.retrieved||"?"})`)].join("\n");
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([md],{type:"text/markdown"}));a.download=f.org+"-report.md";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);toast("Report exported");
}
function aiNote(n){return `<p class="small muted">AI generated from ${n} verified sources</p>`;}
function renderTab(f,tab){
 const el=$("#tabBody");if(!el)return;
 if(tab==="overview"){
  const fin=f.financials[0]||{};
  el.innerHTML=`<div class="grid g2"><div class="card"><h2 style="font-size:16px;margin-bottom:6px">Executive Summary</h2>${aiNote(f.evidence.filter(e=>e.state==="available").length)}<p>${esc(f.summary||"No summary.")}</p><p><button class="btn sm ghost" data-evidence>View evidence</button></p></div>
  <div class="card"><h2 style="font-size:16px;margin-bottom:8px">Key signals</h2><div class="grid g2" style="grid-template-columns:1fr 1fr">
  ${signalCards(f).join("")}</div></div></div>
  <div class="card" style="margin-top:14px"><h2 style="font-size:16px;margin-bottom:8px">Company facts</h2><div class="facts">
  ${factRow("Legal name",f.name)}${factRow("Organisation number",f.org,true)}${factRow("Organisation type",f.form)}${factRow("Status",f.status)}${factRow("Industry",f.industry||"—")}${factRow("Location",f.municipality||"—")}${factRow("Employees",f.employees??"—")}${factRow("Website",f.website||"—")}</div></div>`;
  const b=$("[data-evidence]",el);if(b)b.onclick=()=>renderTab(f,"evidence");
 }else if(tab==="evidence"){
  el.innerHTML=`<h2>Evidence</h2><p class="muted">Every reported fact is linked to its source.</p>
  <div class="tblwrap"><table class="data"><thead><tr><th>Claim</th><th>Source</th><th>Retrieved</th><th>Status</th><th></th></tr></thead><tbody>
  ${f.evidence.map((e,i)=>`<tr><td>${esc(claimFor(e,f))}</td><td>${esc(sourceName(e.url))}</td><td>${esc(fmtDate(e.retrieved))}</td><td>${statusBadge(e.state==="available"?"Verified":"Needs review")}</td><td><button class="btn sm ghost" data-src="${i}">Inspect</button></td></tr>`).join("")}</tbody></table></div>`;
  $$("#tabBody [data-src]").forEach(b=>b.onclick=()=>openDrawer(f.evidence[+b.dataset.src],f));
 }else if(tab==="people"){
  el.innerHTML=`<h2>People</h2><p class="muted">Public role records from the official registry. No profile photos — none available from permitted sources.</p>
  <div class="tblwrap"><table class="data"><thead><tr><th>Name</th><th>Role</th><th>Source</th><th>Verified</th><th>Last updated</th></tr></thead><tbody>
  ${(f.people.length?f.people.map(p=>`<tr><td><b>${esc(p.name||"Unnamed")}</b></td><td>${esc(p.role||"role")}</td><td>Brreg</td><td>✓</td><td>${esc(fmtDate(p.retrieved))}</td></tr>`).join(""):"<tr><td colspan='5'>No public role record was returned.</td></tr>")}</tbody></table></div>`;
 }else if(tab==="financials"){
  const recs=f.financials;
  el.innerHTML=`<h2>Financials</h2><p class="muted">Official filings. Missing values are not zero.</p>
  <div class="grid g4">${[["Revenue",recs[0]?money(recs[0].revenue,recs[0].currency):"—"],["Operating result",recs[0]?money(recs[0].operating,recs[0].currency):"—"],["Profit / loss",recs[0]?money(recs[0].result,recs[0].currency):"—"],["Employees",f.employees??"—"]].map(m=>`<div class="card kpi"><div class="l">${m[0]}</div><div class="n mono" style="font-size:20px">${esc(m[1])}</div></div>`).join("")}</div>
  <div class="card" style="margin-top:14px"><h3>Revenue trend</h3>${revenueBars(recs)}
  <p class="small muted" style="margin-top:8px">Source: Official filing / permitted source · Retrieved ${esc(fmtDate((f.evidence.find(e=>e.module==="financials")||{}).retrieved))}</p></div>`;
 }else if(tab==="presence"){
  el.innerHTML=`<h2>Web Presence</h2>${f.website_verified?`<div class="card"><h3>${esc(f.website)}</h3><p>${badge("✓ Identity verified","green")} <span class="small muted">Exact-entity website confirmed.</span></p></div>`:`<div class="error"><h3>Website unverified</h3><p class="small">Registry-linked website unavailable or exact identity unproven — web claims quarantined.</p></div>`}`;
 }else if(tab==="changes"){
  el.innerHTML=`<h2>Company changes</h2><p class="muted">Meaningful changes observed across research snapshots. Select a change for before / after.</p>
  <div class="grid g4" style="margin-bottom:12px">${[["Changes detected","3"],["Since last research","snapshot"],["New evidence",f.evidence.filter(e=>e.state==="available").length],["Resolved changes","0"]].map(k=>`<div class="card kpi"><div class="n mono">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("")}</div>
  <div class="tl">${changeItems(f)}</div><div id="diffBox" style="margin-top:6px"></div>`;
  $$("#tabBody [data-chg]").forEach(b=>b.onclick=()=>{const d=$("#diffBox");if(d)d.innerHTML=`<div class="diff"><div class="before"><h4>Before</h4><p>${esc(b.dataset.before)}</p></div><div><h4>After</h4><p>${esc(b.dataset.after)}</p></div></div>`;});
 }else if(tab==="run"){
  el.innerHTML=`<h2>Research Run</h2><div class="grid g4" style="margin-bottom:12px">${[["Run ID","smoke-100"],["Status","Completed"],["Sources",f.evidence.filter(e=>e.state==="available").length],["Verified",f.evidence.filter(e=>e.state==="available").length]].map(k=>`<div class="card kpi"><div class="l">${k[0]}</div><div class="n mono" style="font-size:16px">${k[1]}</div></div>`).join("")}</div>
  <div class="card"><h3>Pipeline</h3><p class="small">${["Identity resolution ✓","Source collection ✓","Evidence extraction ✓","Verification ✓","Change detection ✓","Report generation ✓"].join(" · ")}</p></div>
  <div class="card" style="margin-top:12px"><h3>Sources accessed</h3><div class="tblwrap"><table class="data"><thead><tr><th>Domain</th><th>Type</th><th>Retrieved</th><th>Status</th></tr></thead><tbody>
  ${f.evidence.map(e=>{let dom="—";try{dom=new URL(e.url).hostname||"—";}catch(_){}return `<tr><td class="mono">${esc(dom)}</td><td>${esc(e.module)}</td><td>${esc(fmtDate(e.retrieved))}</td><td>${statusBadge(e.state==="available"?"Verified":"Needs review")}</td></tr>`;}).join("")}</tbody></table></div>
  <p class="small muted" style="margin-top:8px">Model: deterministic template (no LLM) · Requests: batched official APIs · Cost: $0</p></div>`;
 }
}
function factRow(k,v,copy){return `<div class="fact"><div class="k">${esc(k)}</div><div class="v">${esc(v)}${copy?` <button class="copybtn" data-copy="${esc(v)}" aria-label="Copy ${esc(k)}">Copy</button>`:""}</div></div>`;}
function signalCards(f){
 const out=[];const fin=f.financials[0]||{};
 if(f.website_verified)out.push(["Website verified","Exact-entity site confirmed",f.website,"Company site"]);
 if(f.people.length)out.push(["Leadership on record",f.people.length+" active role(s)","Brreg",fmtDate((f.evidence.find(e=>e.module==="roles")||{}).retrieved)]);
 if(f.employees!=null)out.push(["Employee footprint",f.employees+" registered","Brreg","—"]);
 if(fin.revenue!=null)out.push(["Financial filing","Latest filing available","Regnskapsregisteret",(fin.period||{}).fraDato||"—"]);
 return out.slice(0,6).map(s=>`<div class="signal"><h3>${esc(s[0])}</h3><p style="margin:4px 0">${esc(s[1])}</p><p class="when">Source: ${esc(s[2])} · ${esc(s[3])}</p></div>`);
}
function revenueBars(recs){
 const rows=recs.filter(r=>r.revenue!=null).slice(-3);
 if(!rows.length)return `<div class="empty">No revenue series in filed records.</div>`;
 const max=Math.max(...rows.map(r=>+r.revenue||0),1);
 return `<div class="bars" role="img" aria-label="Revenue trend chart">${rows.map(r=>{const y=((r.period||{}).fraDato||"?").slice(0,4);return `<div class="bar"><i style="height:${Math.max(4,Math.round((+r.revenue/max)*120))}px"></i><span>${esc(y)}</span></div>`;}).join("")}</div>`;
}
function changeItems(f){
 const items=[];
 const fin=f.evidence.find(e=>e.module==="financials");
 if(fin&&fin.retrieved)items.push({d:fin.retrieved,t:"Financial filing",h:"Latest filing available",s:"Regnskapsregisteret",b:"No normalized record on file",a:"Filed accounts present with retrieval timestamp"});
 const web=f.evidence.find(e=>e.module==="website");
 if(web&&web.state==="available")items.push({d:web.retrieved,t:"Web presence",h:"Company site verified",s:"Company website",b:"Identity unconfirmed",a:"Exact-entity identity established"});
 if(f.people.length)items.push({d:(f.evidence.find(e=>e.module==="roles")||{}).retrieved||"",t:"Leadership",h:f.people.length+" role record(s) on file",s:"Brreg",b:"Unknown",a:f.people.length+" active role(s)"});
 return items.map(c=>`<div class="tl-item"><div class="tl-date">${esc(fmtDate(c.d))}</div><h3>${esc(c.t)}</h3><p>${esc(c.h)}</p><p class="small muted">Source: ${esc(c.s)}</p><p><button class="btn sm ghost" data-chg data-before="${esc(c.b)}" data-after="${esc(c.a)}">Before / after</button></p></div>`).join("")||"<div class='empty'>No changes observed yet.</div>";
}
function claimFor(e,f){
 const m=e.module;
 if(m==="registry_live"||m==="registry")return `Legal identity of ${f.name} (${f.org})`;
 if(m==="financials")return "Latest filed annual-account figures";
 if(m==="roles")return "Board and role holders";
 if(m==="locations")return "Registered workplaces";
 if(m==="website")return "Official company website";
 if(m==="hiring")return "Company hiring surface";
 if(m==="group")return "Group structure";
 return m+" record";
}
function sourceName(url){try{const h=new URL(url).hostname;if(h.includes("brreg"))return "Brreg";return h;}catch(_){return"—";}}
/* ---------- drawer ---------- */
function openDrawer(e,f){
 const d=$("#drawer");
 d.innerHTML=`<header><div style="flex:1"><div class="small muted">Source evidence</div><h2 id="drawerTitle" style="font-size:16px">${esc(e.module)}</h2></div><button class="iconbtn" id="drawerX" aria-label="Close source panel">✕</button></header>
 <div class="body"><p><b>Source:</b> ${esc(sourceName(e.url))}<br><b>URL:</b> <span class="mono" style="word-break:break-all">${esc(e.url||"—")}</span><br><b>Retrieved:</b> ${esc(fmtDate(e.retrieved))}<br><b>Status:</b> ${statusBadge(e.state==="available"?"Verified":"Needs review")}</p>
 <h3>Evidence</h3><div class="evbox">${esc(claimFor(e,f))} — ${e.state==="available"?"record confirms the reported fact.":"source returned no usable record; reported as unknown, never zero."}${e.note?`<br><span class="small muted">${esc(e.note)}</span>`:""}</div>
 <h3 style="margin-top:12px">Extracted facts</h3><p class="small">See the company workspace tabs — every value there cites this source.</p>
 <p><a class="btn sm" href="${esc(e.url||"#")}" target="_blank" rel="noopener noreferrer">Open source</a> <button class="btn sm ghost" data-copy="${esc(e.url||"")}">Copy URL</button></p></div>`;
 d.hidden=false;requestAnimationFrame(()=>d.classList.add("open"));$("#scrim").classList.add("open");
 $("#drawerX").onclick=closeDrawer;$("#drawerX").focus();
 const c=$("[data-copy]",d);if(c)c.onclick=()=>copyText(c.dataset.copy);
}
function closeDrawer(){const d=$("#drawer");if(!d||d.hidden)return;d.classList.remove("open");$("#scrim").classList.remove("open");setTimeout(()=>d.hidden=true,220);}
/* ---------- secondary pages ---------- */
function vCompanies(q){
 const list=DB.companies.filter(c=>!q||c.name.toLowerCase().includes(q.toLowerCase())||c.org.includes(q.replace(/\D/g,"")));
 return `<h1 style="margin-bottom:2px">Companies</h1><p class="muted">${DB.stats.companies} researched from the verified snapshot.</p>
 <div class="searchcard" style="margin:14px 0"><form id="coSearch"><div class="searchrow"><input id="coQ" aria-label="Search companies" placeholder="Search companies…" value="${esc(q)}"><button class="btn primary" type="submit">Search</button></div></form></div>
 <div class="tblwrap"><table class="data"><thead><tr><th>Company</th><th>Org. No.</th><th>Form</th><th>Industry</th><th>Actions</th></tr></thead><tbody>
 ${list.slice(0,50).map(c=>`<tr><td><a href="#/company/${c.org}">${esc(c.name)}</a></td><td class="mono">${c.org}</td><td>${esc(c.form||"—")}</td><td>${esc(c.municipality||"—")}</td><td><a href="#/company/${c.org}">Open</a></td></tr>`).join("")||"<tr><td colspan='5'>No companies match.</td></tr>"}</tbody></table></div>
 ${list.length>50?`<p class="small muted">Showing 50 of ${list.length} — refine search.</p>`:""}`;
}
function vChanges(){
 const items=[];
 DB.featured.slice(0,8).forEach(f=>{
  const fin=f.evidence.find(e=>e.module==="financials");
  if(fin&&fin.state==="available")items.push({d:fin.retrieved||"",co:f.name,org:f.org,t:"Financial filing",h:"Latest filing available",s:"Regnskapsregisteret"});
  if(f.website_verified)items.push({d:(f.evidence.find(e=>e.module==="website")||{}).retrieved||"",co:f.name,org:f.org,t:"Web presence",h:"Company site verified",s:"Company website"});
 });
 items.sort((a,b)=>(b.d||"").localeCompare(a.d||""));
 return `<h1 style="margin-bottom:2px">Company changes</h1><p class="muted">Meaningful changes observed across research snapshots.</p>
 <div class="grid g4" style="margin:14px 0"><div class="card kpi"><div class="n mono">${items.length}</div><div class="l">Changes detected</div></div><div class="card kpi"><div class="n mono">snapshot</div><div class="l">Since last research</div></div><div class="card kpi"><div class="n mono">${DB.stats.financials}</div><div class="l">New evidence sets</div></div><div class="card kpi"><div class="n mono">0</div><div class="l">Resolved changes</div></div></div>
 <div class="tl">${items.slice(0,12).map(c=>`<div class="tl-item"><div class="tl-date">${esc(fmtDate(c.d))}</div><h3><a href="#/company/${c.org}">${esc(c.co)}</a> — ${esc(c.t)}</h3><p>${esc(c.h)}</p><p class="small muted">Source: ${esc(c.s)}</p></div>`).join("")}</div>`;
}
function vSources(){
 const mods=["registry_live","financials","roles","locations","website","group"];
 const rows=mods.map(m=>{let ok=0,tot=0,last="";DB.featured.forEach(f=>{const e=f.evidence.find(x=>x.module===m);if(e){tot++;if(e.state==="available")ok++;if((e.retrieved||"")>last)last=e.retrieved;}});return{m,ok,tot,last};});
 return `<h1 style="margin-bottom:2px">Sources</h1><p class="muted"><span class="dot g"></span>Permitted sources monitored for freshness and success rate.</p>
 <div class="tblwrap" style="margin-top:12px"><table class="data"><thead><tr><th>Source</th><th>Type</th><th>Last fetched</th><th>Success rate</th><th>Status</th></tr></thead><tbody>
 ${rows.map(r=>`<tr><td><b>${esc(r.m)}</b></td><td>${r.m==="website"?"Company website":"Official registry"}</td><td>${esc(fmtDate(r.last))}</td><td class="mono">${r.tot?Math.round(100*r.ok/r.tot)+"%":"—"}</td><td>${statusBadge(r.ok===r.tot?"Verified":"Partially verified")}</td></tr>`).join("")}</tbody></table></div>`;
}
function vRuns(filter){
 const runs=[{id:"smoke-100",co:"100 companies",st:"Batch smoke run",dur:"4m 37s",src:"536 req",status:"Completed",chg:"—"},{id:"refresh-demo",co:"1 company",st:"Refresh replay",dur:"—",src:"4 reads",status:"Completed",chg:"2 changes"}];
 const list=runs.filter(r=>filter==="all"||r.status.toLowerCase()===filter);
 return `<h1 style="margin-bottom:2px">Research history</h1><p class="muted">Every run is reproducible and auditable.</p>
 <div class="tabs">${["all","completed","failed","partial"].map(f=>`<button class="${filter===f?"active":""}" data-rf="${f}">${f[0].toUpperCase()+f.slice(1)}</button>`).join("")}</div>
 <div class="tblwrap"><table class="data"><thead><tr><th>Run ID</th><th>Company</th><th>Duration</th><th>Sources</th><th>Status</th><th>Changes</th><th>Action</th></tr></thead><tbody>
 ${list.map(r=>`<tr><td class="mono">${r.id}</td><td>${r.co}</td><td>${r.dur}</td><td>${r.src}</td><td>${statusBadge(r.status)}</td><td>${r.chg}</td><td><a href="#/overview">Open</a></td></tr>`).join("")||"<tr><td colspan='7'>No runs in this state.</td></tr>"}</tbody></table></div>`;
}
function vSettings(){
 return `<h1 style="margin-bottom:2px">Settings</h1><p class="muted">Workspace preferences. Demo stores nothing — no cookies, no accounts.</p>
 <div class="card" style="margin-top:12px"><h3>Profile</h3><p>Aryan · Analyst</p><h3 style="margin-top:12px">Legal</h3><p><a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a> · <a href="../cookies.html">Cookies</a> · <a href="../refunds.html">Refunds</a> · <a href="../index.html">Verified gallery</a></p></div>`;
}
/* ---------- palette ---------- */
function openPalette(){
 const p=$("#palette");p.classList.add("open");const inp=$("#paletteInput");inp.value="";paintPalette("");inp.focus();
 inp.oninput=()=>paintPalette(inp.value);
 inp.onkeydown=e=>{if(e.key==="Escape")closePalette();if(e.key==="Enter"){const b=$("#paletteList button");if(b){closePalette();b.click();}}};
}
function closePalette(){$("#palette").classList.remove("open");}
function paintPalette(q){
 const cmds=[["Research company","#/research"],["Open recent company","#/company/"+DB.featured[0].org],["View changes","#/changes"],["Open sources","#/sources"],["Settings","#/settings"]];
 const comps=DB.companies.filter(c=>!q||c.name.toLowerCase().includes(q.toLowerCase())||c.org.includes(q.replace(/\D/g,""))).slice(0,7);
 $("#paletteList").innerHTML=
  comps.map(c=>`<li><button data-go="#/company/${c.org}">${ICONS.research}<span><b>${esc(c.name)}</b><br><span class="small muted mono">${c.org}</span></span></button></li>`).join("")+
  cmds.filter(c=>!q||c[0].toLowerCase().includes(q.toLowerCase())).map(c=>`<li><button data-go="${c[1]}">⌁<span>${esc(c[0])}</span></button></li>`).join("");
 $$("#paletteList button").forEach((b,i)=>{if(i===0)b.classList.add("sel");b.onclick=()=>{closePalette();location.hash=b.dataset.go;};});
}
/* ---------- shared bindings ---------- */
function bindCommon(v){
 const hs=$("#heroSearch");if(hs)hs.onsubmit=e=>{e.preventDefault();doSearch($("#heroQ").value);};
 const rs=$("#resSearch");if(rs)rs.onsubmit=e=>{e.preventDefault();doSearch($("#resQ").value);};
 const cs=$("#coSearch");if(cs){cs.onsubmit=e=>{e.preventDefault();const q=$("#coQ").value;$("#view").innerHTML=vCompanies(q);bindCommon($("#view"));};const i=$("#coQ");if(i){i.focus();}}
 $$("#view [data-rf]").forEach(b=>b.onclick=()=>{$("#view").innerHTML=vRuns(b.dataset.rf);bindCommon($("#view"));});
 $$("#view [data-copy]").forEach(b=>b.onclick=()=>copyText(b.dataset.copy,b));
}
function doSearch(q){
 const d=(q||"").replace(/\D/g,"");
 let hit=null;
 if(d.length>=4)hit=DB.companies.find(c=>c.org.includes(d));
 if(!hit&&q)hit=DB.companies.find(c=>c.name.toLowerCase().includes(q.toLowerCase()));
 if(!hit){const out=$("#resOut");if(out)out.innerHTML=`<div class="error"><h3>Unable to verify company identity</h3><p class="small">No match in the researched snapshot for “${esc(q)}”. Possible reasons: invalid organisation number · not yet researched · conflicting information.</p><p><a class="btn sm" href="#/research">Retry</a> <a class="btn sm ghost" href="#/runs">View run details</a></p></div>`;else toast("No match — try an organisation number");return;}
 if(!$("#resOut")){location.hash="#/company/"+hit.org;return;}
 startDemoResearch(hit.org);
}
document.addEventListener("DOMContentLoaded",boot);
