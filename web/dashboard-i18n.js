// Text-node translation preserves controls and updates arriving from the API.
const rows = [
 ['PROJECT','ПРОЕКТ','ЖОБА'],['CONNECT','СВЯЗЬ','БАЙЛАНЫС'],
 ['About the model','О модели','Модель туралы'],['Forecast archive','Архив прогнозов','Болжамдар мұрағаты'],
 ['Methodology','Методология','Әдістеме'],['SCADA sources','Источники SCADA','SCADA дереккөздері'],
 ['Time zone UTC+05','Часовой пояс UTC+05','Уақыт белдеуі UTC+05'],['Contact','Контакты','Байланыс'],
 ['BACK TO TOP','НАВЕРХ','ЖОҒАРЫ'],
 ['DATA','ДАННЫЕ','ДЕРЕКТЕР'],
 ['Overview','Обзор','Шолу'],['Analytics','Аналитика','Талдау'],['AI Agent','ИИ-агент','ЖИ-агент'],
 ['Forecast mode','Режим прогноза','Болжам режимі'],['Replay · February 2026','Архив · Февраль 2026','Мұрағат · Ақпан 2026'],['Live weather forecast','Актуальный прогноз погоды','Ағымдағы ауа райы болжамы'],['Refresh forecast','Обновить прогноз','Болжамды жаңарту'],
 ['Power Output','Выработка энергии','Энергия өндіру'],['Wind Speed','Скорость ветра','Жел жылдамдығы'],['Temperature','Температура','Температура'],['Digital Twin','Цифровой двойник','Цифрлық егіз'],['DIGITAL TWIN','ЦИФРОВОЙ ДВОЙНИК','ЦИФРЛЫҚ ЕГІЗ'],['DATA / MOTION / ENERGY','ДАННЫЕ / ДВИЖЕНИЕ / ЭНЕРГИЯ','ДЕРЕКТЕР / ҚОЗҒАЛЫС / ЭНЕРГИЯ'],
 ['Generator','Генератор','Генератор'],['Gearbox','Редуктор','Редуктор'],['Shaft','Вал','Білік'],['Rotor','Ротор','Ротор'],['Reset inspection','Сбросить осмотр','Қарауды қалпына келтіру'],['Disassembly','Разборка','Бөлшектеу'],['Drag to orbit · scroll to zoom · click a turbine','Вращайте перетаскиванием · приближайте прокруткой · выберите турбину','Айналдыру үшін сүйреңіз · жақындату үшін айналдырыңыз · турбинаны таңдаңыз'],
 ['Temperature · SCADA','Температура · SCADA','Температура · SCADA'],['Forecast wind','Прогноз ветра','Жел болжамы'],['°C · archived','°C · архив','°C · мұрағат'],['m/s · selected hour','м/с · выбранный час','м/с · таңдалған сағат'],['m/s','м/с','м/с'],
 ['Power Generation Forecast','Прогноз выработки энергии','Энергия өндіру болжамы'],['AI-powered hourly forecast','Почасовой прогноз на основе ИИ','ЖИ негізіндегі сағаттық болжам'],['Forecast','Прогноз','Болжам'],['Prediction interval','Прогнозный интервал','Болжам аралығы'],['Forecast status','Статус прогноза','Болжам күйі'],['Weather & power forecast pipeline','Прогноз погоды и выработки энергии','Ауа райы мен энергия өндіру болжамы'],
 ['Mean power','Средняя мощность','Орташа қуат'],['Peak output','Пиковая мощность','Ең жоғары қуат'],['Peak time','Время пика','Ең жоғары қуат уақыты'],['Wind','Ветер','Жел'],['selected hour','выбранный час','таңдалған сағат'],['Power forecast','Прогноз мощности','Қуат болжамы'],['Hourly forecast · normalized power','Почасовой прогноз · нормализованная мощность','Сағаттық болжам · нормаланған қуат'],['24–48 hours','24–48 часов','24–48 сағат'],['Maximum forecast generation','Максимальная прогнозная выработка','Ең жоғары болжамды өндіріс'],['normalized power','нормализованная мощность','нормаланған қуат'],['normalized ·','нормализованная ·','нормаланған ·'],['normalized · 0–1','нормализованная · 0–1','нормаланған · 0–1'],['normalized · archived','нормализованная · архив','нормаланған · мұрағат'],['normalized','нормализованная','нормаланған'],
 ['Weather Forecast','Прогноз погоды','Ауа райы болжамы'],['Historical Data','Исторические данные','Тарихи деректер'],['Power','Мощность','Қуат'],['Forecast Timeline','Временная шкала прогноза','Болжам уақыт шкаласы'],['Predicted Power','Прогноз мощности','Болжамды қуат'],['Forecast execution','Выполнение прогноза','Болжамды орындау'],['Observation details','Данные наблюдений','Бақылау деректері'],['Coordinates','Координаты','Координаттар'],['Status','Статус','Күй'],['Archived SCADA','Архив SCADA','SCADA мұрағаты'],['Last Update','Последнее обновление','Соңғы жаңарту'],
 ['NORMALIZED POWER','НОРМАЛИЗОВАННАЯ МОЩНОСТЬ','НОРМАЛАНҒАН ҚУАТ'],['ARCHIVED OBSERVATIONS','АРХИВ НАБЛЮДЕНИЙ','БАҚЫЛАУЛАР МҰРАҒАТЫ'],['HOURLY FORECASTS','ПОЧАСОВЫЕ ПРОГНОЗЫ','САҒАТТЫҚ БОЛЖАМДАР'],
 ['COMPLETED','ЗАВЕРШЕНО','АЯҚТАЛДЫ'],['Loading','Загрузка','Жүктелуде'],['Loading forecast…','Загрузка прогноза…','Болжам жүктелуде…'],['Loading backend data…','Загрузка данных…','Деректер жүктелуде…'],['Waiting for backend…','Ожидание данных…','Деректер күтілуде…'],['Forecast unavailable','Прогноз недоступен','Болжам қолжетімсіз'],['Forecast unavailable. Use Refresh forecast to retry.','Прогноз недоступен. Нажмите «Обновить прогноз».','Болжам қолжетімсіз. «Болжамды жаңарту» түймесін басыңыз.'],['No observations available.','Нет данных наблюдений.','Бақылау деректері жоқ.'],
 ['FETCHING_WEATHER','ПОЛУЧЕНИЕ ПОГОДЫ','АУА РАЙЫН АЛУ'],['VALIDATING_DATA','ПРОВЕРКА ДАННЫХ','ДЕРЕКТЕРДІ ТЕКСЕРУ'],['PREPARING_FEATURES','ПОДГОТОВКА ПРИЗНАКОВ','БЕЛГІЛЕРДІ ДАЙЫНДАУ'],['RUNNING_MODEL','ЗАПУСК МОДЕЛИ','МОДЕЛЬДІ ІСКЕ ҚОСУ'],['VALIDATING_FORECAST','ПРОВЕРКА ПРОГНОЗА','БОЛЖАМДЫ ТЕКСЕРУ'],
 ['02 / ANALYTICS','02 / АНАЛИТИКА','02 / ТАЛДАУ'],['Energy in context.','Энергия в контексте.','Энергия туралы деректер.'],['Forecast, weather and historical turbine trends in one view.','Прогноз, погода и история турбин на одном экране.','Болжам, ауа райы және турбина тарихы бір экранда.'],['Power Forecast','Прогноз мощности','Қуат болжамы'],['03 / AI AGENT','03 / ИИ-АГЕНТ','03 / ЖИ-АГЕНТ'],['From signal to forecast.','От сигнала к прогнозу.','Сигналдан болжамға дейін.'],['Explore the actual backend execution path for the selected turbine.','Этапы расчёта прогноза для выбранной турбины.','Таңдалған турбина болжамын есептеу кезеңдері.'],['Agentic AI Pipeline','Процесс работы ИИ','ЖИ жұмыс үдерісі'],['Recalculate forecast ↗','Пересчитать прогноз ↗','Болжамды қайта есептеу ↗'],['Execution History','История выполнения','Орындалу тарихы'],['Latest backend run · Astana UTC+05','Последний запуск · время UTC+05','Соңғы іске қосу · уақыт UTC+05'],
 ['Mar 2023 — Jan 2026 · daily SCADA means (Astana UTC+05), gaps preserved','Март 2023 — Январь 2026 · среднесуточные SCADA (Астана UTC+05), пропуски сохранены','Наурыз 2023 — Қаңтар 2026 · күндік SCADA орташа мәндері (Астана UTC+05), бос аралықтар сақталған'],
 ['Latest available SCADA measurements · not live telemetry','Последние архивные измерения SCADA','SCADA жүйесінің соңғы мұрағаттық өлшемдері'],['● 3D model','● 3D-модель','● 3D модель'],['Loading 3D model…','Загрузка 3D-модели…','3D модель жүктелуде…'],
];
const dictionary = new Map(rows.map(row=>[row[0],row]));
export function initDashboardLanguage(onChange) {
 const app=document.querySelector('#application'),select=document.querySelector('#dashboard-language');
 let lang='en';const originals=new WeakMap();
 const translate=text=>{
   const i={en:0,ru:1,kk:2}[lang];if(!i)return text;
   if(dictionary.has(text))return dictionary.get(text)[i];
   return text.replace(/^Turbine (\d+)$/i,(_,n)=>`${i===1?'Турбина':'Турбина'} ${n}`)
    .replace(/^Generated: /,i===1?'Обновлено: ':'Жаңартылды: ')
    .replace(/^API connected · replay$/,i===1?'API подключён · архив':'API қосылған · мұрағат')
    .replace(/^API connected · live$/,i===1?'API подключён · актуальный прогноз':'API қосылған · ағымдағы болжам')
    .replace(/^Next (\d+)h$/,(_,n)=>i===1?`Следующие ${n} ч`:`Келесі ${n} сағ`)
    .replace(/^(\(?)(24|48)h(\)?)$/,(_,a,n,b)=>`${a}${n} ${i===1?'ч':'сағ'}${b}`)
    .replace(/m\/s/g,'м/с')
    .replace(/^Historical (power|wind speed|temperature)$/,(_,key)=>({power:i===1?'История мощности':'Қуат тарихы','wind speed':i===1?'История скорости ветра':'Жел жылдамдығы тарихы',temperature:i===1?'История температуры':'Температура тарихы'})[key])
    .replace(/^Normalized output · next$/,i===1?'Нормализованная мощность · следующие':'Нормаланған қуат · келесі');
 };
 const observer=new MutationObserver(apply);
 function apply(){
   observer.disconnect();
   const walker=document.createTreeWalker(app,NodeFilter.SHOW_TEXT);
   while(walker.nextNode()){
     const node=walker.currentNode;if(node.parentElement.closest('#dashboard-language,script,style,[translate="no"]'))continue;
     const current=node.textContent;let record=originals.get(node);
     if(!record||record.rendered!==current)record={source:current};
     const key=record.source.trim();const result=record.source.replace(key,translate(key));
     if(current!==result)node.textContent=result;
     record.rendered=result;originals.set(node,record);
   }
   observer.observe(app,{subtree:true,childList:true,characterData:true});
 }
 select.addEventListener('change',()=>onChange(select.value));
 return language=>{lang=language;select.value=lang;app.lang=lang;select.setAttribute('aria-label',lang==='ru'?'Язык интерфейса':lang==='kk'?'Интерфейс тілі':'Interface language');apply();};
}
