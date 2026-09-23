// SVG charts retain missing observations and never smooth measured values.
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate = (value, historical) => new Intl.DateTimeFormat('en-GB', {
  timeZone:'Etc/GMT-5', day:'2-digit', month:'short', ...(historical ? {year:'numeric'} : {hour:'2-digit',minute:'2-digit',hour12:false})
}).format(new Date(value));
let serial = 0;
const mounted = new WeakMap();
export function clearChart(host) { mounted.get(host)?.disconnect(); mounted.delete(host); }

export function mountChart(host, values, {low, high, min=0, max=1, timestamps=[], historical=false, unit='0–1', label='Power', color='#315bea'}={}) {
  mounted.get(host)?.disconnect();
  const id = `wind-chart-${++serial}`;
  let selected = null;
  function draw() {
    if (!values.some(Number.isFinite)) { host.innerHTML='<div class="chart-empty">No observations available</div>'; return; }
    const width=Math.max(280,host.clientWidth), height=Math.max(220,host.clientHeight), left=48, right=18, top=42, bottom=42;
    const plotWidth=width-left-right, base=height-bottom, plotHeight=base-top;
    const x=i=>left+plotWidth*i/Math.max(1,values.length-1), y=v=>top+plotHeight*(1-(v-min)/(max-min||1));
    const segments = predicate => {
      const result=[]; let current=[];
      values.forEach((v,i)=>{if(predicate(v,i))current.push(i);else if(current.length){result.push(current);current=[];}});
      if(current.length)result.push(current);return result;
    };
    const paths=segments(Number.isFinite).map(indices=>indices.map((i,j)=>`${j?'L':'M'}${x(i)},${y(values[i])}`).join(' '));
    const band=low&&high ? segments((v,i)=>Number.isFinite(v)&&Number.isFinite(low[i])&&Number.isFinite(high[i])).map(indices=>
      `<path d="${indices.map((i,j)=>`${j?'L':'M'}${x(i)},${y(high[i])}`).join(' ')} ${[...indices].reverse().map(i=>`L${x(i)},${y(low[i])}`).join(' ')} Z" fill="url(#${id}-band)"/>`).join('') : '';
    const grid=Array.from({length:5},(_,i)=>{const value=max-(max-min)*i/4, yy=y(value);return `<line x1="${left}" x2="${width-right}" y1="${yy}" y2="${yy}" class="plot-grid"/><text x="${left-12}" y="${yy+4}" text-anchor="end" class="plot-label">${value.toFixed(max-min>4?0:2)}</text>`;}).join('');
    const ticks=width<440?3:5;
    const labels=Array.from({length:ticks},(_,i)=>{
      const n=Math.round((values.length-1)*i/(ticks-1)),stamp=timestamps[n]&&new Date(timestamps[n]);
      const fmt=options=>new Intl.DateTimeFormat('en-GB',{timeZone:'Etc/GMT-5',...options}).format(stamp);
      const text=stamp?(historical?fmt({month:'short',year:'numeric'}):fmt({hour:'2-digit',minute:'2-digit',hour12:false})):`+${n}h`;
      const second=stamp&&!historical?`<tspan x="${x(n)}" dy="14" class="plot-zone">${escape(fmt({day:'2-digit',month:'short'}))}</tspan>`:'';
      return `<text x="${x(n)}" y="${height-(second?23:14)}" text-anchor="${i===0?'start':i===ticks-1?'end':'middle'}" class="plot-label">${escape(text)}${second}</text>`;
    }).join('');
    const dots=values.length<=48 ? values.map((v,i)=>Number.isFinite(v)?`<circle cx="${x(i)}" cy="${y(v)}" r="2.6" fill="${color}" stroke="white" stroke-width="1.2"/>`:'').join('') : '';
    host.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escape(label)} ${historical?'daily history':'hourly forecast'}, ${escape(unit)}. Dates in Astana UTC+05. Missing observations shown as gaps.">
      <defs><linearGradient id="${id}-band" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${color}" stop-opacity=".19"/><stop offset="1" stop-color="${color}" stop-opacity=".035"/></linearGradient></defs>
      <text x="${left}" y="19" class="plot-unit">${escape(label)} · ${escape(unit)}</text><text x="${width-right}" y="19" text-anchor="end" class="plot-zone">UTC+05</text>
      ${grid}${band}${paths.map(d=>`<path d="${d}" fill="none" stroke="${color}" stroke-width="${historical?1.6:2.5}" stroke-linejoin="round" stroke-linecap="round"/>`).join('')}${dots}${labels}
      <g class="plot-cursor" visibility="hidden"><line y1="${top}" y2="${base}" stroke="${color}" stroke-dasharray="3 4" opacity=".5"/><circle r="5" fill="${color}" stroke="white" stroke-width="2"/></g>
      </svg><div class="plot-tooltip" hidden></div><div class="plot-interaction" tabindex="0" role="slider" aria-label="Inspect ${escape(label)} data. Use left and right arrow keys." aria-valuemin="0" aria-valuemax="${values.length-1}" aria-valuenow="0"></div>`;
    const overlay=host.querySelector('.plot-interaction'),tip=host.querySelector('.plot-tooltip'),cursor=host.querySelector('.plot-cursor');
    function inspect(index) {
      selected=Math.max(0,Math.min(values.length-1,index));
      const v=values[selected],time=timestamps[selected]?formatDate(timestamps[selected],historical):`+${selected}h`;
      const value=Number.isFinite(v)?`${v.toFixed(3)} ${unit}`:'No observation';
      tip.innerHTML=`<span>${escape(time)} · UTC+05</span><strong>${escape(value)}</strong>${low&&Number.isFinite(low[selected])&&Number.isFinite(high[selected])?`<small>Interval ${low[selected].toFixed(3)} – ${high[selected].toFixed(3)}</small>`:''}`;
      tip.hidden=false;tip.style.left=`${Math.max(4,Math.min(width-tip.offsetWidth-4,x(selected)-tip.offsetWidth/2))}px`;
      tip.style.top='28px';
      cursor.setAttribute('visibility','visible');const line=cursor.querySelector('line'),dot=cursor.querySelector('circle');
      line.setAttribute('x1',x(selected));line.setAttribute('x2',x(selected));dot.setAttribute('cx',x(selected));dot.setAttribute('cy',Number.isFinite(v)?y(v):base);dot.setAttribute('visibility',Number.isFinite(v)?'visible':'hidden');
      overlay.setAttribute('aria-valuenow',selected);overlay.setAttribute('aria-valuetext',`${time}: ${value}`);
    }
    overlay.onpointermove=e=>inspect(Math.round((e.clientX-host.getBoundingClientRect().left-left)/plotWidth*(values.length-1)));
    overlay.onpointerleave=()=>{tip.hidden=true;cursor.setAttribute('visibility','hidden');};
    overlay.onfocus=()=>inspect(selected??0);
    overlay.onblur=overlay.onpointerleave;
    overlay.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();inspect(e.key==='Home'?0:e.key==='End'?values.length-1:(selected??0)+(e.key==='ArrowRight'?1:-1));}};
  }
  const observer=new ResizeObserver(draw);mounted.set(host,observer);observer.observe(host);draw();
}
