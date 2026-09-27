/* Signalpost 3D landing engine — first-party, dependency-free canvas.
   Restrained enterprise 3D: projected orbits, glass nodes, thin links,
   parallax camera, scroll morph, hover panels. No WebGL lib, no cookies.
   Honors prefers-reduced-motion; degrades gracefully without JS (static hero). */
"use strict";
(function(){
const REDUCED=matchMedia("(prefers-reduced-motion: reduce)").matches;
const MOBILE=matchMedia("(max-width: 760px)").matches;
const DPR=Math.min(devicePixelRatio||1,MOBILE?1.5:2);

function fit(cv){
  const r=cv.getBoundingClientRect(),w=Math.max(280,r.width),h=Math.max(280,r.height);
  cv.width=w*DPR;cv.height=h*DPR;
  const ctx=cv.getContext("2d");ctx.setTransform(DPR,0,0,DPR,0,0);
  return{ctx,w,h};
}
/* pseudo-3D projection */
function project(x,y,z,cx,cy,cam){
  const s=cam.f/(cam.f+z);
  return{x:cx+x*s*cam.zoom,y:cy+y*s*cam.zoom,s};
}
function glassNode(ctx,x,y,r,label,sub,opts){
  opts=opts||{};
  const g=ctx.createRadialGradient(x-r*.35,y-r*.4,r*.1,x,y,r);
  if(opts.hot){g.addColorStop(0,"rgba(147,197,253,.95)");g.addColorStop(.55,"rgba(59,130,246,.55)");g.addColorStop(1,"rgba(30,58,138,.85)");}
  else if(opts.ok){g.addColorStop(0,"rgba(134,239,172,.9)");g.addColorStop(.6,"rgba(34,197,94,.4)");g.addColorStop(1,"rgba(20,83,45,.85)");}
  else{g.addColorStop(0,"rgba(203,213,225,.85)");g.addColorStop(.55,"rgba(100,116,139,.35)");g.addColorStop(1,"rgba(15,23,42,.9)");}
  ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fillStyle=g;ctx.fill();
  ctx.lineWidth=opts.hot?2:1.25;
  ctx.strokeStyle=opts.hot?"rgba(147,197,253,.95)":opts.ok?"rgba(34,197,94,.8)":"rgba(148,163,184,.55)";
  ctx.stroke();
  ctx.beginPath();ctx.arc(x-r*.3,y-r*.35,r*.22,0,7);ctx.fillStyle="rgba(255,255,255,.18)";ctx.fill();
  if(label){ctx.fillStyle=opts.hot?"#EFF6FF":"#CBD5E1";ctx.font=(opts.big?"700 ":"600 ")+(opts.big?13:11)+"px Inter,system-ui,sans-serif";
    ctx.textAlign="center";ctx.fillText(label,x,y+r+16);
    if(sub){ctx.fillStyle="#64748B";ctx.font="10px Inter,system-ui,sans-serif";ctx.fillText(sub,x,y+r+29);}}
}
function link(ctx,a,b,color,width,alpha){
  const gr=ctx.createLinearGradient(a.x,a.y,b.x,b.y);
  gr.addColorStop(0,color.replace("A",0));gr.addColorStop(.5,color.replace("A",alpha));gr.addColorStop(1,color.replace("A",0));
  ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.lineWidth=width;ctx.strokeStyle=gr;ctx.stroke();
}
/* ---- orbital intelligence graph ---- */
function orbitGraph(cv,cfg){
  let S=fit(cv),t=Math.random()*10,mx=0,my=0,tx=0,ty=0,hover=-1,scroll=0;
  const nodes=cfg.nodes.slice(0,MOBILE?cfg.mobileNodes||5:99);
  const parts=Array.from({length:MOBILE?24:60},()=>({a:Math.random()*7,r:.4+Math.random()*1.6,s:.05+Math.random()*.25,o:Math.random()}));
  const panel=cfg.panel;
  addEventListener("resize",()=>{S=fit(cv);});
  cv.parentElement.addEventListener("mousemove",e=>{const r=cv.getBoundingClientRect();tx=((e.clientX-r.left)/r.width-.5);ty=((e.clientY-r.top)/r.height-.5);});
  cv.parentElement.addEventListener("mouseleave",()=>{tx=0;ty=0;hover=-1;if(panel)panel.hidden=true;});
  cv.addEventListener("mousemove",e=>{
    const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;hover=-1;
    nodes.forEach((n,i)=>{if(i===0||!n._p)return;const d=Math.hypot(n._p.x-px,n._p.y-py);if(d<26)hover=i;});
    if(panel){if(hover>0){const n=nodes[hover];
      panel.innerHTML="<b>"+n.label+"</b><span>"+n.desc+"</span><em>✓ Verified · "+n.src+"</em>";
      panel.hidden=false;}else panel.hidden=true;}
    cv.style.cursor=hover>0?"pointer":"default";
  });
  if(cfg.scroll){addEventListener("scroll",()=>{const r=cv.getBoundingClientRect();
    scroll=Math.min(1,Math.max(0,-r.top/(r.height||1)));},{passive:true});}
  const cam={f:520,zoom:1};
  function frame(){
    t+=REDUCED?0:.008;mx+=(tx-mx)*.04;my+=(ty-my)*.04;
    const{ctx,w,h}=S,cx=w/2+mx*26,cy=h/2+my*20;
    ctx.clearRect(0,0,w,h);
    const bg=ctx.createRadialGradient(cx,cy,10,cx,cy,Math.max(w,h)*.7);
    bg.addColorStop(0,"rgba(37,99,235,.10)");bg.addColorStop(1,"rgba(0,0,0,0)");
    ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
    parts.forEach(p=>{p.o+=p.s*.01;const x=cx+Math.cos(p.a+p.o)*w*.42,y=cy+Math.sin(p.a*1.3+p.o)*h*.4;
      ctx.beginPath();ctx.arc(x,y,p.r,0,7);ctx.fillStyle="rgba(147,197,253,.28)";ctx.fill();});
    const R=Math.min(w,h)*.30*(1+scroll*.25);
    const c=nodes[0],cp=project(0,Math.sin(t*.6)*8,0,cx,cy,cam);c._p=cp;
    nodes.forEach((n,i)=>{if(!i)return;const a=n.a0+t*n.sp;
      const x=Math.cos(a)*R*n.rx,y=Math.sin(a)*R*.52*n.ry,z=Math.sin(a)*R*.35;
      n._p=project(x,y,z,cx,cy,cam);});
    nodes.forEach((n,i)=>{if(!i)return;link(ctx,cp,n._p,"rgba(96,165,250,A)",1.1,.5);});
    const order=nodes.map((n,i)=>i).sort((a,b)=>nodes[a]._p.s-nodes[b]._p.s);
    order.forEach(i=>{const n=nodes[i],p=n._p;
      if(!i)glassNode(ctx,p.x,p.y,30*p.s+14,c.label,c.sub,{big:true,hot:hover===0});
      else glassNode(ctx,p.x,p.y,11*p.s+7,n.label,null,{hot:hover===i,ok:n.ok});});
    if(!REDUCED)requestAnimationFrame(frame);
  }
  if(REDUCED){for(let i=0;i<40;i++)t+=.008;}
  frame();
}
addEventListener("DOMContentLoaded",()=>{
  const f=document.getElementById("heroSearch");
  if(f)f.addEventListener("submit",e=>{e.preventDefault();location.href="app/#/research";});
  const ex=document.querySelector("[data-ex]");
  if(ex)ex.addEventListener("click",()=>{const q=document.getElementById("heroQ");if(q)q.value="888567232";location.href="app/#/research";});
  document.querySelectorAll("canvas[data-graph]").forEach(cv=>{
    const kind=cv.dataset.graph;
    if(kind==="hero")orbitGraph(cv,{
      mobileNodes:5,
      panel:document.getElementById("nodePanel"),
      scroll:true,
      nodes:[
        {label:"Equinor ASA",sub:"923 609 016 · source of truth"},
        {label:"Registry",desc:"Official organisation information",src:"Brønnøysund Register Centre",a0:.2,sp:.12,rx:1,ry:1,ok:true},
        {label:"Financials",desc:"Filed annual accounts",src:"Regnskapsregisteret",a0:1.4,sp:.1,rx:1.05,ry:.95,ok:true},
        {label:"Leadership",desc:"Board and role holders",src:"Brreg roles",a0:2.6,sp:.13,rx:.95,ry:1.05,ok:true},
        {label:"Website",desc:"Verified company site",src:"Company-owned",a0:3.8,sp:.11,rx:1.05,ry:1,ok:true},
        {label:"Jobs",desc:"Careers surface",src:"Company site",a0:5,sp:.14,rx:1,ry:.9},
        {label:"Sources",desc:"Dated public mentions",src:"Permitted pages",a0:5.9,sp:.09,rx:.9,ry:1.05}
      ]});
    if(kind==="evidence")orbitGraph(cv,{
      mobileNodes:4,
      panel:document.getElementById("evPanel"),
      nodes:[
        {label:"Active",sub:"verified fact"},
        {label:"Brreg",desc:"Registry record confirms active status",src:"data.brreg.no · 27 Sep 2026",a0:.5,sp:.14,rx:1,ry:1,ok:true},
        {label:"Filing",desc:"2025 accounts on file",src:"Regnskapsregisteret",a0:2.5,sp:.11,rx:1,ry:1,ok:true},
        {label:"Website",desc:"Official site reference",src:"Company-owned",a0:4.4,sp:.13,rx:1,ry:1}
      ]});
    if(kind==="constellation")orbitGraph(cv,{
      mobileNodes:6,
      nodes:[
        {label:"Company",sub:"connected evidence"},
        {label:"Registry",a0:.1,sp:.1,rx:1,ry:1,ok:true},{label:"Website",a0:1.1,sp:.13,rx:1.05,ry:.95,ok:true},
        {label:"Financials",a0:2.1,sp:.09,rx:.95,ry:1.05,ok:true},{label:"Jobs",a0:3.2,sp:.12,rx:1,ry:1},
        {label:"News",a0:4.2,sp:.1,rx:1.05,ry:.9},{label:"Filings",a0:5.2,sp:.14,rx:.95,ry:1.05,ok:true}
      ]});
  });
});
})();
