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
 ['Power Output','Мощность','Қуат'],['Wind Speed','Скорость ветра','Жел жылдамдығы'],['Temperature','Температура','Температура'],['Digital Twin','Цифровой двойник','Цифрлық егіз'],['DIGITAL TWIN','ЦИФРОВОЙ ДВОЙНИК','ЦИФРЛЫҚ ЕГІЗ'],['DATA / MOTION / ENERGY','ДАННЫЕ / ДВИЖЕНИЕ / ЭНЕРГИЯ','ДЕРЕКТЕР / ҚОЗҒАЛЫС / ЭНЕРГИЯ'],
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
rows.push(...[["AI Agent", "ИИ-агент", "ЖИ-агент"],
 ["Ready", "Готов", "Дайын"],
 ["IN FOCUS", "В ФОКУСЕ", "НАЗАРДА"],
 ["Turbine overview", "Обзор турбины", "Турбинаға шолу"],
 ["Select a turbine or inspect its parts in 3D.", "Выберите турбину или раскройте её узлы в 3D.", "Турбинаны таңдаңыз немесе оның бөлшектерін 3D режимінде қараңыз."],
 ["Data analysis", "Анализ данных", "Деректерді талдау"],
 ["Loading selected turbine data…", "Загружаю данные выбранной турбины…", "Таңдалған турбинаның деректері жүктелуде…"],
 ["Data and limitations", "Данные и ограничения", "Деректер мен шектеулер"],
 ["Forecast ↗", "Прогноз ↗", "Болжам ↗"],
 ["Risks", "Риски", "Тәуекелдер"],
 ["About this part", "Об узле", "Бөлшек туралы"],
 ["Question about this turbine", "Вопрос об этой турбине", "Осы турбина туралы сұрақ"],
 ["Ask about this turbine…", "Спросите об этой турбине…", "Осы турбина туралы сұраңыз…"],
 ["Send question", "Отправить вопрос", "Сұрақты жіберу"],
 ["Selected turbine context", "Контекст выбранной турбины", "Таңдалған турбинаның контексті"],
 ["All features ↗", "Все функции ↗", "Барлық мүмкіндіктер ↗"],
 ["Forecast horizon", "Горизонт прогноза", "Болжам көкжиегі"],
 ["AI assistant for the selected turbine", "ИИ-агент выбранной турбины", "Таңдалған турбинаның ЖИ-агенті"],
 ["Quality assessment · January 2026", "Проверка качества · январь 2026", "Сапаны бағалау · 2026 жылғы қаңтар"],
 ["Separate evaluation model. February actuals are unavailable; February accuracy has not been measured.", "Отдельная оценочная модель. Фактических значений февраля нет; точность за февраль не рассчитана.", "Бөлек бағалау моделі. Ақпанның нақты мәндері жоқ; ақпан айындағы дәлдік есептелмеген."],
 ["Loading results…", "Загрузка результатов…", "Нәтижелер жүктелуде…"],
 ["Turbine", "Турбина", "Турбина"],
 ["Model MAE", "MAE модели", "Модельдің MAE мәні"],
 ["Baseline MAE", "MAE базового", "Базалық болжамның MAE мәні"],
 ["MAE reduction", "Снижение MAE", "MAE төмендеуі"],
 ["Interval coverage", "Покрытие интервала", "Аралықтың қамту үлесі"],
 ["Try the agent's capabilities", "Попробуйте возможности агента", "Агент мүмкіндіктерін сынаңыз"],
 ["Test the agent in action", "Проверьте агента в действии", "Агентті іс жүзінде сынаңыз"],
 ["Choose a scenario for the selected turbine. The answer and actual tool calls will appear below.", "Выберите сценарий — агент выполнит задачу для выбранной турбины. Ниже появятся ответ и реальные вызовы инструментов.", "Таңдалған турбина үшін сценарий таңдаңыз. Төменде жауап пен құралдардың нақты шақырулары көрсетіледі."],
 ["01 / FORECAST", "01 / ПРОГНОЗ", "01 / БОЛЖАМ"],
 ["Calculate power ↗", "Рассчитать выработку ↗", "Қуатты есептеу ↗"],
 ["Weather → ML model → hourly forecast", "Погода → ML-модель → почасовой прогноз", "Ауа райы → ML моделі → сағаттық болжам"],
 ["02 / DATA", "02 / ДАННЫЕ", "02 / ДЕРЕКТЕР"],
 ["Check data ↗", "Проверить данные ↗", "Деректерді тексеру ↗"],
 ["Sources, freshness and limitations", "Источники, актуальность и ограничения", "Дереккөздер, өзектілік және шектеулер"],
 ["03 / RISKS", "03 / РИСКИ", "03 / ТӘУЕКЕЛДЕР"],
 ["Explain risks ↗", "Объяснить риски ↗", "Тәуекелдерді түсіндіру ↗"],
 ["Forecast intervals and power ramps", "Интервалы прогноза и скачки мощности", "Болжам аралықтары мен қуаттың күрт өзгерістері"],
 ["04 / QUALITY", "04 / КАЧЕСТВО", "04 / САПА"],
 ["Compare with baseline ↗", "Сравнить с базовым ↗", "Базалық болжаммен салыстыру ↗"],
 ["Measured MAE and interval coverage", "Измеренные MAE и покрытие интервала", "Өлшенген MAE және аралықтың қамту үлесі"],
 ["05 / CHANGES", "05 / ИЗМЕНЕНИЯ", "05 / ӨЗГЕРІСТЕР"],
 ["Compare revisions ↗", "Сравнить версии ↗", "Нұсқаларды салыстыру ↗"],
 ["What changed after recalculation", "Что изменилось после пересчёта", "Қайта есептеуден кейінгі өзгерістер"],
 ["06 / DIGITAL TWIN", "06 / ЦИФРОВОЙ ДВОЙНИК", "06 / ЦИФРЛЫҚ ЕГІЗ"],
 ["Explore the turbine ↗", "Исследовать турбину ↗", "Турбинаны зерттеу ↗"],
 ["Select a part in 3D and ask the AI", "Выберите узел в 3D и задайте вопрос ИИ", "3D бөлшегін таңдап, ЖИ-ге сұрақ қойыңыз"],
 ["WindAI operator assistant", "ИИ-диспетчер WindAI", "WindAI ЖИ-диспетчері"],
 ["Forecast, data checks and risk explanations · Astana time", "Прогноз, проверка данных и объяснение рисков · время Астаны", "Болжам, деректерді тексеру және тәуекелдерді түсіндіру · Астана уақыты"],
 ["Ready to start", "Готов к запуску", "Іске қосуға дайын"],
 ["Agent task", "Задача агенту", "Агентке тапсырма"],
 ["Run AI agent ↗", "Запустить ИИ-агента ↗", "ЖИ-агентті іске қосу ↗"],
 ["Selected turbine · current horizon", "Выбранная турбина · текущий горизонт", "Таңдалған турбина · ағымдағы болжам көкжиегі"],
 ["The agent will call forecasting and validation tools. Numerical values come from the ML model.", "Агент вызовет инструменты расчёта и проверки. Численные значения поступают из ML-модели.", "Агент есептеу және тексеру құралдарын шақырады. Сандық мәндер ML моделінен алынады."],
 ["Tool calls and results", "Вызовы инструментов и результаты", "Құрал шақырулары мен нәтижелері"],
 ["Automatic updates", "Автоматическое обновление", "Автоматты жаңарту"],
 ["Checking status…", "Проверка состояния…", "Күйі тексерілуде…"],
 ["Check for updates", "Проверить обновления", "Жаңартуларды тексеру"],
 ["Save the hourly forecast with intervals, Astana time and data source.", "Сохраните почасовой прогноз с интервалами, временем Астаны и источником данных.", "Сағаттық болжамды аралықтарымен, Астана уақытымен және дереккөзімен сақтаңыз."],
 ["Download forecast CSV ↓", "Скачать прогноз CSV ↓", "Болжамды CSV форматында жүктеу ↓"],
 ["View charts and metrics ↗", "Посмотреть графики и метрики ↗", "Графиктер мен метрикаларды қарау ↗"],
 ["Export CSV", "Скачать CSV", "CSV жүктеу"],
 ["Start the agent for the selected turbine and horizon.", "Запустите агента для выбранной турбины и горизонта.", "Таңдалған турбина мен болжам көкжиегі үшін агентті іске қосыңыз."],
 ["Agent is working…", "Агент работает…", "Агент жұмыс істеуде…"],
 ["Checking data, calculating the forecast and assessing risks. This usually takes up to a minute.", "Проверяю данные, рассчитываю прогноз и оцениваю риски. Обычно это занимает до минуты.", "Деректер тексеріліп, болжам есептеліп, тәуекелдер бағалануда. Бұл әдетте бір минутқа дейін созылады."],
 ["Completed · OpenAI", "Завершено · OpenAI", "Аяқталды · OpenAI"],
 ["Fallback calculation", "Резервный расчёт", "Резервтік есептеу"],
 ["Calculation error", "Ошибка расчёта", "Есептеу қатесі"],
 ["Error", "Ошибка", "Қате"],
 ["Monitor is disabled in server settings", "Монитор выключен в настройках сервера", "Монитор сервер баптауларында өшірілген"],
 ["Monitor unavailable", "Монитор недоступен", "Монитор қолжетімсіз"],
 ["Checking weather and input data…", "Проверяю погоду и входные данные…", "Ауа райы мен кіріс деректері тексерілуде…"],
 ["Wind · SCADA", "Ветер · SCADA", "Жел · SCADA"],
 ["Power · forecast", "Мощность · прогноз", "Қуат · болжам"],
 ["Main shaft", "Главный вал", "Негізгі білік"],
 ["Internal components", "Внутренние узлы", "Ішкі бөлшектер"],
 ["Observations, forecast and risks for the selected turbine.", "Наблюдения, прогноз и риски выбранной турбины.", "Таңдалған турбинаның бақылаулары, болжамы және тәуекелдері."],
 ["Converts mechanical rotation into electrical energy.", "Преобразует механическое вращение в электрическую энергию.", "Механикалық айналуды электр энергиясына айналдырады."],
 ["Changes the drive rotation speed in a geared design.", "В редукторной схеме изменяет скорость вращения привода.", "Редукторлы құрылымда жетектің айналу жылдамдығын өзгертеді."],
 ["Transmits rotor rotation and torque.", "Передаёт вращение и крутящий момент ротора.", "Ротордың айналуы мен айналу моментін береді."],
 ["The blades and hub convert wind energy into rotation.", "Лопасти и ступица преобразуют энергию ветра во вращение.", "Қалақтар мен күпшек жел энергиясын айналуға айналдырады."],
 ["The nacelle houses the main drive components.", "Гондола размещает основные узлы привода.", "Гондолада жетектің негізгі бөлшектері орналасқан."],
 ["Fetching weather, calculating the forecast and checking risks…", "Получаю погоду, рассчитываю прогноз и проверяю риски…", "Ауа райы алынып, болжам есептеліп, тәуекелдер тексерілуде…"],
 ["Examining the selected turbine and its data…", "Изучаю выбранную турбину и её данные…", "Таңдалған турбина мен оның деректері зерттелуде…"],
 ["AI is analyzing", "ИИ анализирует", "ЖИ талдауда"],
 ["Updating response…", "Обновляю ответ…", "Жауап жаңартылуда…"],
 ["Running", "В работе", "Орындалуда"],
 ["AI conclusion", "Вывод ИИ", "ЖИ қорытындысы"],
 ["Data summary", "Сводка данных", "Деректер жиынтығы"],
 ["Summary", "Сводка", "Жиынтық"],
 ["Data available · AI unavailable", "Данные доступны · ИИ недоступен", "Деректер бар · ЖИ қолжетімсіз"],
 ["Explanation unavailable", "Пояснение недоступно", "Түсіндірме қолжетімсіз"],
 ["Could not get an explanation. Turbine data remains available above.", "Не удалось получить пояснение. Данные турбины остаются доступны выше.", "Түсіндірме алу мүмкін болмады. Турбина деректері жоғарыда қолжетімді."],
 ["Try again", "Повторите запрос", "Қайта сұраңыз"],
 ["Waiting for data", "Ожидание данных", "Деректер күтілуде"],
 ["OPENAI_API_KEY is not configured on the server.", "OPENAI_API_KEY не настроен на сервере.", "Серверде OPENAI_API_KEY бапталмаған."],
 ["SCADA temperature is air temperature. There are no sensors for individual component condition. The 3D geometry is illustrative.", "Температура SCADA относится к воздуху. Датчиков состояния отдельных узлов нет. Геометрия 3D иллюстративная.", "SCADA температурасы — ауа температурасы. Жеке бөлшектердің күй датчиктері жоқ. 3D геометриясы көрнекілік үшін берілген."],
 ["How it works · U.S. DOE ↗", "Принцип работы · U.S. DOE ↗", "Жұмыс істеу қағидасы · U.S. DOE ↗"],
 ["Astana · UTC+05", "Астана · UTC+05", "Астана · UTC+05"],
 ["Rotor animation follows forecast wind; illustrative speed, not measured RPM.", "Вращение ротора отражает прогноз ветра; скорость условная, а не измеренные обороты.", "Ротор анимациясы жел болжамына сәйкес келеді; жылдамдық шартты, өлшенген айналым емес."],
 ["Interactive 3D wind farm", "Интерактивный 3D-ветропарк", "Интерактивті 3D жел паркі"],
 ["Forecast hour", "Час прогноза", "Болжам сағаты"],
 ["Historical turbine data", "Исторические данные турбины", "Турбинаның тарихи деректері"],
 ["Awaiting API response", "Ожидание ответа API", "API жауабы күтілуде"],
 ["No observations available", "Нет данных наблюдений", "Бақылау деректері жоқ"],
 ["No observation", "Нет наблюдения", "Бақылау жоқ"],
 ["WIND", "ВЕТЕР", "ЖЕЛ"],
 ["FUTURE", "БУДУЩЕЕ", "БОЛАШАҚ"]]);
rows.push(...[["Build a forecast, check data quality and explain the main risks. Compare accuracy with the baseline.", "Построй прогноз, проверь качество данных и объясни главные риски. Сравни точность с базовым прогнозом.", "Болжам жаса, деректер сапасын тексер және негізгі тәуекелдерді түсіндір. Дәлдікті базалық болжаммен салыстыр."], ["Wind speed", "Скорость ветра", "Жел жылдамдығы"], ["h", "ч", "сағ"], ["Loading", "Загрузка", "Жүктелуде"], ["Digital Twin — Data / Motion / Energy", "Цифровой двойник — Данные / Движение / Энергия", "Цифрлық егіз — Деректер / Қозғалыс / Энергия"]]);
export function translated(text) {
 const i={en:0,ru:1,kk:2}[document.documentElement.lang]??0;
 return dictionary.get(text)?.[i]??text;
}
const dictionary = new Map();
for (const row of rows) for (const source of row) if (!dictionary.has(source)) dictionary.set(source, row);
export function initDashboardLanguage(onChange) {
 const app=document.querySelector('#application'),select=document.querySelector('#dashboard-language');
 let lang='en';const originals=new WeakMap();
 const translate=text=>{
   const i={en:0,ru:1,kk:2}[lang];
   if(dictionary.has(text))return dictionary.get(text)[i];
   if(i===0)return text.replace(/^Турбина (\d+)$/, 'Turbine $1');
   return text.replace(/^(?:Turbine|Турбина) (\d+)$/i,(_,n)=>`${['Turbine','Турбина','Турбина'][i]} ${n}`)
    .replace(/^(24|48) hours$/,(_,n)=>`${n} ${['hours','часов','сағат'][i]}`)
    .replace(/^Turbine (\d+)$/i,(_,n)=>`${i===1?'Турбина':'Турбина'} ${n}`)
    .replace(/^Generated: /,i===1?'Обновлено: ':'Жаңартылды: ')
    .replace(/^API connected · replay$/,i===1?'API подключён · архив':'API қосылған · мұрағат')
    .replace(/^API connected · live$/,i===1?'API подключён · актуальный прогноз':'API қосылған · ағымдағы болжам')
    .replace(/^Next (\d+)h$/,(_,n)=>i===1?`Следующие ${n} ч`:`Келесі ${n} сағ`)
    .replace(/^(\(?)(24|48)h(\)?)$/,(_,a,n,b)=>`${a}${n} ${i===1?'ч':'сағ'}${b}`)
    .replace(/m\/s/g,'м/с')
    .replace(/^Historical (power|wind speed|temperature)$/,(_,key)=>({power:i===1?'История мощности':'Қуат тарихы','wind speed':i===1?'История скорости ветра':'Жел жылдамдығы тарихы',temperature:i===1?'История температуры':'Температура тарихы'})[key])
    .replace(/^Normalized output · next$/,i===1?'Нормализованная мощность · следующие':'Нормаланған қуат · келесі');
 };
 const attributes=new WeakMap();
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
   for(const node of app.querySelectorAll('[placeholder],[aria-label],[title],[alt]')){
     const records=attributes.get(node)||{};
     for(const attr of ['placeholder','aria-label','title','alt']){
       if(!node.hasAttribute(attr))continue;
       const current=node.getAttribute(attr);let record=records[attr];
       if(!record||record.rendered!==current)record={source:current};
       record.rendered=translate(record.source);
       if(current!==record.rendered)node.setAttribute(attr,record.rendered);
       records[attr]=record;
     }
     attributes.set(node,records);
   }
   observer.observe(app,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['placeholder','aria-label','title','alt']});
 }
 select.addEventListener('change',()=>onChange(select.value));
 return language=>{lang=language;select.value=lang;app.lang=lang;select.setAttribute('aria-label',lang==='ru'?'Язык интерфейса':lang==='kk'?'Интерфейс тілі':'Interface language');apply();};
}
