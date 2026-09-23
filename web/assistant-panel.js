// Context follows the 3D selection. Late replies can never overwrite a newer selection.
import {backendUrl} from './backend.js';
export function createAssistantPanel(getState,onForecast){
 const $=s=>document.querySelector(s);
 const labels={overview:'Обзор турбины',generator:'Генератор',gearbox:'Редуктор',main_shaft:'Главный вал',rotor:'Ротор',nacelle:'Внутренние узлы'};
 const roles={overview:'Наблюдения, прогноз и риски выбранной турбины.',generator:'Преобразует механическое вращение в электрическую энергию.',gearbox:'В редукторной схеме изменяет скорость вращения привода.',main_shaft:'Передаёт вращение и крутящий момент ротора.',rotor:'Лопасти и ступица преобразуют энергию ветра во вращение.',nacelle:'Гондола размещает основные узлы привода.'};
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=(n,d=2)=>Number.isFinite(n)?n.toFixed(d):'—';
 const local=t=>new Intl.DateTimeFormat(document.documentElement.lang==='kk'?'kk-KZ':document.documentElement.lang==='ru'?'ru-RU':'en-GB',{timeZone:'Etc/GMT-5',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(t));
 let component='overview',data=null,dataKey='',serial=0,timer=null,busy=false,pending=null,updating=false;
 const cache=new Map();
 async function api(path,body){const r=await fetch(backendUrl(path),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const json=await r.json().catch(()=>({}));if(r.status===405||r.status===404)throw Error('Сервер не поддерживает эту функцию агента. Перезапустите backend с актуальным кодом и обновите страницу.');if(!r.ok)throw Error(typeof json.detail==='string'?json.detail:'Не удалось выполнить запрос');return json;}
 function setBusy(value){busy=value;$('#assistant-send').disabled=value;document.querySelectorAll('[data-assistant-action]').forEach(b=>b.disabled=value);}
 function paintFacts(){
  const s=getState();$('#assistant-turbine').textContent=`Турбина ${s.id.endsWith('1')?'01':'02'}`;
  $('#assistant-component').textContent=labels[component];$('#assistant-role').textContent=roles[component];
  if(!data){$('#assistant-facts').textContent='';return;}
  const obs=data.current,forecast=data.assessment;
  $('#assistant-facts').innerHTML=`<div><small>Ветер · SCADA</small><b>${fmt(obs?.wind_speed,1)} <em>м/с</em></b></div><div><small>Мощность · прогноз</small><b>${fmt(forecast?.mean_power)} <em>0–1</em></b></div>`;
  $('#assistant-source').innerHTML=`<p>Турбина: ${esc(s.id)}<br>Координаты: ${fmt(data.latitude,6)}, ${fmt(data.longitude,6)}<br>SCADA: ${obs?.timestamp?esc(local(obs.timestamp)):'нет'} · архив<br>Прогноз: ${esc(s.mode)} · ${s.hours} ч</p><p>Температура SCADA относится к воздуху. Датчиков состояния отдельных узлов нет. Геометрия 3D иллюстративная.</p>`;
 }
 function request(question='',workflow=false){
  if(!data)return;
  clearTimeout(timer);const token=++serial;
  $('#assistant-error').hidden=true;$('#assistant-answer').textContent=workflow?'Получаю погоду, рассчитываю прогноз и проверяю риски…':'Изучаю выбранную турбину и её данные…';
  $('#assistant-response-label').textContent='ИИ анализирует';$('#assistant-state').textContent='Обновляю ответ…';$('#agent-status').textContent='В работе';
  const s=getState(),language=$('#dashboard-language')?.value??'ru';
  const payload={turbine_id:s.id,hours:s.hours,mode:s.mode,component,question,language};
  const key=JSON.stringify([dataKey,payload,workflow]);
  pending={token,payload,key,workflow};
  drain();
 }
 async function drain(){
  if(busy||!pending)return;
  const task=pending;pending=null;setBusy(true);
  try{
   let r=cache.get(task.key);
   if(!r){
    r=task.workflow?await api('/api/agent/run',{turbine_id:task.payload.turbine_id,hours:task.payload.hours,mode:task.payload.mode,message:task.payload.question,language:task.payload.language}):await api('/api/agent/inspect',task.payload);
    if(!r.llm_error){cache.set(task.key,r);if(cache.size>40)cache.delete(cache.keys().next().value);}
   }
   if(task.token!==serial)return;
   paintFacts();
   if(task.workflow&&r.forecast){updating=true;try{onForecast(r.forecast);}finally{updating=false;}}
   $('#assistant-answer').textContent=r.answer;
   $('#assistant-response-label').textContent=r.engine==='openai'?'Вывод ИИ':'Сводка данных';
   $('#agent-status').textContent=r.llm_error?'Сводка':'Готов';
   $('#assistant-state').textContent=r.llm_error?'Данные доступны · ИИ недоступен':`${({en:'Based on',ru:'По данным',kk:'Дереккөз'})[task.payload.language]} ${task.payload.turbine_id.replace('_',' ')} · ${local(new Date())}`;
   if(r.llm_error){$('#assistant-error').textContent=r.llm_error;$('#assistant-error').hidden=false;}
   if(r.context){const missing=r.context.component_info.missing;$('#assistant-source').innerHTML+=`<p>Нет данных: ${esc(missing.join(', '))}.</p><a href="${esc(r.context.component_role_source)}" target="_blank" rel="noopener noreferrer">Принцип работы · U.S. DOE ↗</a>`;}
  }catch(error){if(task.token===serial){$('#assistant-response-label').textContent='Пояснение недоступно';$('#assistant-answer').textContent='Не удалось получить пояснение. Данные турбины остаются доступны выше.';$('#assistant-error').textContent=error.message;$('#assistant-error').hidden=false;$('#assistant-state').textContent='Повторите запрос';$('#agent-status').textContent='Ошибка';}}
  finally{setBusy(false);if(pending)drain();}
 }
 function schedule(){clearTimeout(timer);timer=setTimeout(()=>request(),350);}
 $('#assistant-form').onsubmit=e=>{e.preventDefault();const q=$('#assistant-question').value.trim();if(!q)return;request(q);$('#assistant-question').value='';};
 $('#assistant-question').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(!busy)$('#assistant-form').requestSubmit();}};
 document.querySelectorAll('[data-assistant-action]').forEach(b=>b.onclick=()=>{if(b.dataset.assistantAction==='component')request(`Расскажи о выбранном узле «${labels[component]}» и какие данные этой турбины доступны.`);else request(b.dataset.assistantAction==='risks'?'Оцени риски прогноза выбранной турбины и качество данных.':'Построй прогноз выбранной турбины, объясни пик и сравни точность с базовым прогнозом.',true);});
 addEventListener('windai-language-change',()=>{if(data&&!document.querySelector('#application').hidden)schedule();});
 return {
  clear(){serial++;pending=null;clearTimeout(timer);component='overview';data=null;dataKey='';paintFacts();$('#assistant-answer').textContent='Загружаю данные выбранной турбины…';$('#assistant-response-label').textContent='Анализ данных';$('#agent-status').textContent='Загрузка';$('#assistant-state').textContent='Ожидание данных';},
  update(value){const changed=dataKey!==`${value.run_id}:${getState().hours}:${getState().mode}`;data=value;dataKey=`${value.run_id}:${getState().hours}:${getState().mode}`;paintFacts();if(changed&&!updating&&!document.querySelector('#application').hidden)schedule();},
  activate(){if(data)schedule();},
  inspect(selection){if(selection.turbine_id!==getState().id)return;const next=labels[selection.component]?selection.component:'overview';if(next===component)return;component=next;serial++;paintFacts();if(data)request();}
 };
}
