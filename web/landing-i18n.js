import {initDashboardLanguage} from './dashboard-i18n.js';
// Translate text nodes in place so links, typography and event handlers stay intact.
const translations = [
 ['About','О проекте','Жоба туралы'],
 ['How It Works','Как это работает','Қалай жұмыс істейді'],
 ['Technology','Технологии','Технологиялар'],
 ['Launch Demo','Открыть демо','Демоны ашу'],
 ['Power','Энергия','Желден'],
 ['from wind.','ветра.','қуат.'],
 ['Clarity','Ясность','Деректен'],
 ['from data.','данных.','айқындық.'],
 ['[ HACKALEM AI / WIND ENERGY INTELLIGENCE ]','[ HACKALEM AI / ИНТЕЛЛЕКТ ВЕТРОЭНЕРГЕТИКИ ]','[ HACKALEM AI / ЖЕЛ ЭНЕРГЕТИКАСЫНДАҒЫ ЗИЯТКЕРЛІК ]'],
 ['Agentic AI for Wind Power Forecasting','ИИ-агенты для прогноза ветровой генерации','Жел энергиясын болжайтын ЖИ-агенттер'],
 ['Predict wind power generation 24–48 hours ahead.','Прогноз выработки энергии на 24–48 часов вперёд.','Энергия өндіруді 24–48 сағат бұрын болжаңыз.'],
 ['Autonomous weather analysis, machine learning','Автономный анализ погоды, машинное обучение','Ауа райын автоматты талдау, машиналық оқыту'],
 ['forecasting and real-time energy insights.','и оперативная аналитика энергогенерации.','және энергия өндіруді жедел талдау.'],
 ['THE WIND FARM, REIMAGINED','НОВЫЙ ВЗГЛЯД НА ВЕТРОПАРК','ЖЕЛ ПАРКІНЕ ЖАҢА КӨЗҚАРАС'],
 ['Turbines','Турбины','Турбина'],['48h','48 ч','48 сағ'],['Forecast','Прогноз','Болжам'],
 ['ML Forecast Pipeline','ML-прогнозирование','ML арқылы болжау'],
 ['SCROLL TO EXPLORE ↓','ЛИСТАЙТЕ ДАЛЬШЕ ↓','ТӨМЕН АЙНАЛДЫРЫҢЫЗ ↓'],
 ['＋ TURBINE 01','＋ ТУРБИНА 01','＋ ТУРБИНА 01'],['＋ TURBINE 02','＋ ТУРБИНА 02','＋ ТУРБИНА 02'],
 ['CLEAN','ЧИСТАЯ','ТАЗА'],['ENERGY','ЭНЕРГИЯ','ЭНЕРГИЯ'],['BRIGHTER','СВЕТЛОЕ','ЖАРҚЫН'],['TOMORROW','БУДУЩЕЕ','БОЛАШАҚ'],
 ['FORECAST · 24—48H ↗','ПРОГНОЗ · 24—48 Ч ↗','БОЛЖАМ · 24—48 САҒ ↗'],
 ['01 / ABOUT','01 / О ПРОЕКТЕ','01 / ЖОБА ТУРАЛЫ'],
 ['Forecast the energy','Энергия будущего —','Болашақ энергияны'],['ahead.','в вашем прогнозе.','болжаңыз.'],
 ['WindAI turns turbine history and local weather forecasts into a clear, hourly view of expected power generation. Explore two turbines and the decisions behind each forecast.','WindAI превращает историю работы турбин и местные прогнозы погоды в понятный почасовой прогноз выработки. Изучите две турбины и узнайте, на чём основан каждый прогноз.','WindAI турбиналардың жұмыс тарихы мен жергілікті ауа райы болжамын энергия өндірудің түсінікті сағаттық болжамына айналдырады. Екі турбинаны зерттеп, әр болжамның негізін біліңіз.'],
 ['02 / HOW IT WORKS','02 / КАК ЭТО РАБОТАЕТ','02 / ҚАЛАЙ ЖҰМЫС ІСТЕЙДІ'],
 ['From weather signal','От данных о погоде','Ауа райы деректерінен'],['to power forecast.','к прогнозу энергии.','энергия болжамына дейін.'],
 ['Weather Forecast','Прогноз погоды','Ауа райы болжамы'],['Hourly conditions at turbine coordinates','Почасовая погода в точке расположения турбины','Турбина орналасқан жердегі сағаттық ауа райы'],
 ['Data Processing','Обработка данных','Деректерді өңдеу'],['Prepare historical and forecast inputs','Подготовка исторических и прогнозных данных','Тарихи және болжамдық деректерді дайындау'],
 ['ML Prediction','ML-прогноз','ML болжамы'],['Estimate normalized hourly power','Расчёт нормализованной почасовой мощности','Нормаланған сағаттық қуатты есептеу'],
 ['AI Validation','Проверка ИИ','ЖИ тексеруі'],['Check forecast output','Проверка результатов прогноза','Болжам нәтижелерін тексеру'],
 ['24–48h Power Forecast','Прогноз на 24–48 часов','24–48 сағаттық қуат болжамы'],['Explore the next hours','Выработка в ближайшие часы','Алдағы сағаттардағы энергия өндіру'],
 ['03 / AGENTIC AI','03 / ИИ-АГЕНТЫ','03 / ЖИ-АГЕНТТЕР'],['One connected','Единый','Біртұтас'],['workflow.','рабочий процесс.','жұмыс үдерісі.'],
 ['Weather Agent','Агент погоды','Ауа райы агенті'],['Retrieves a forecast for the turbine coordinates.','Получает прогноз погоды по координатам турбины.','Турбина координаттары бойынша ауа райы болжамын алады.'],
 ['Data Agent','Агент данных','Деректер агенті'],['Prepares historical and weather data.','Готовит исторические и погодные данные.','Тарихи және ауа райы деректерін дайындайды.'],
 ['Forecast Agent','Агент прогноза','Болжау агенті'],['Runs the power prediction model.','Запускает модель прогноза мощности.','Қуатты болжау моделін іске қосады.'],
 ['Validation Agent','Агент проверки','Тексеру агенті'],['Checks the forecast output.','Проверяет результаты прогноза.','Болжам нәтижелерін тексереді.'],
 ['Result','Результат','Нәтиже'],['Delivers an hourly 24–48h forecast.','Выдаёт почасовой прогноз на 24–48 часов.','24–48 сағатқа арналған сағаттық болжамды ұсынады.'],
 ['04 / DIGITAL TWIN','04 / ЦИФРОВОЙ ДВОЙНИК','04 / ЦИФРЛЫҚ ЕГІЗ'],['See the whole','Весь ветропарк','Бүкіл жел паркі'],['wind farm.','перед вами.','көз алдыңызда.'],
 ['Explore each turbine and see how weather conditions translate into predicted power generation.','Изучите каждую турбину и узнайте, как погода влияет на прогноз выработки энергии.','Әр турбинаны зерттеп, ауа райының энергия өндіру болжамына қалай әсер ететінін көріңіз.'],
 ['Explore Digital Twin ↗','Открыть цифровой двойник ↗','Цифрлық егізді ашу ↗'],
 ['05 / LOOK AHEAD','05 / ВЗГЛЯД В БУДУЩЕЕ','05 / БОЛАШАҚҚА КӨЗҚАРАС'],['Clean Energy.','Чистая энергия.','Таза энергия.'],['Smarter Tomorrow.','Разумное будущее.','Ақылды болашақ.'],['Powered by Agentic AI.','На основе ИИ-агентов.','ЖИ-агенттер негізінде.'],['Launch WindAI','Открыть WindAI','WindAI ашу'],
 ['HARNESSING','ИСПОЛЬЗУЕМ','ТАБИҒАТ'],['NATURE INTELLIGENCE','ИНТЕЛЛЕКТ ПРИРОДЫ','ЗИЯТКЕРЛІГІН'],['FOR A BRIGHTER','ДЛЯ СВЕТЛОГО','ЖАРҚЫН'],
 ['CLEANER SKIES','ЧИСТОЕ НЕБО','ТАЗА АСПАН'],['STRONGER COMMUNITIES','СИЛЬНОЕ ОБЩЕСТВО','МЫҚТЫ ҚОҒАМ'],['A BRIGHTER TOMORROW','СВЕТЛОЕ БУДУЩЕЕ','ЖАРҚЫН БОЛАШАҚ'],['MORE WIND','БОЛЬШЕ ВЕТРА','КӨБІРЕК ЖЕЛ'],['A BRIGHTER','СВЕТЛАЯ','ЖАРҚЫН'],['PLANET','ПЛАНЕТА','ҒАЛАМШАР'],['DATA','ДАННЫЕ','ДЕРЕКТЕР'],['MODELS','МОДЕЛИ','МОДЕЛЬДЕР'],['CLEANER AIR','ЧИСТЫЙ ВОЗДУХ','ТАЗА АУА'],['BRIGHTER TOMORROW','СВЕТЛОЕ БУДУЩЕЕ','ЖАРҚЫН БОЛАШАҚ'],
 ['Product','Продукт','Өнім'],['Impact','Наш вклад','Біздің үлесіміз'],['Analytics','Аналитика','Талдау'],['AI Agent','ИИ-агент','ЖИ-агент'],['CLEAN ENERGY','ЧИСТАЯ ЭНЕРГИЯ','ТАЗА ЭНЕРГИЯ'],['SMARTER TOMORROW','РАЗУМНОЕ БУДУЩЕЕ','АҚЫЛДЫ БОЛАШАҚ'],
];
const dictionary = new Map(translations.map(([en, ru, kk]) => [en, {en, ru, kk}]));
const landing = document.querySelector('#landing');
const selector = landing.querySelector('.language-select');
const walker = document.createTreeWalker(landing, NodeFilter.SHOW_TEXT);
const nodes = [];
while (walker.nextNode()) {
 const node = walker.currentNode;
 const original = node.textContent;
 if (dictionary.has(original.trim())) nodes.push({node, original, key: original.trim()});
}
const attributes = [
 [landing.querySelector('.hero-background'), 'alt', {en:'White wind turbines over a blue mountain landscape',ru:'Белые ветротурбины на фоне синих гор',kk:'Көк таулар аясындағы ақ жел турбиналары'}],
 ...[...landing.querySelectorAll('[aria-label="WindAI home"]')].map(node => [node,'aria-label',{en:'WindAI home',ru:'WindAI — главная',kk:'WindAI — басты бет'}]),
 [landing.querySelector('.landing-head nav'),'aria-label',{en:'Landing navigation',ru:'Навигация по лендингу',kk:'Лендинг навигациясы'}],
 [landing.querySelector('.landing-footer nav'),'aria-label',{en:'Footer navigation',ru:'Навигация в подвале',kk:'Төменгі навигация'}],
];
const setDashboardLanguage=initDashboardLanguage(language=>setLanguage(language));
function setLanguage(language) {
 const lang = ['en','ru','kk'].includes(language) ? language : 'en';
 selector.value = lang;
 landing.lang = lang;
 document.documentElement.lang = lang;
 setDashboardLanguage(lang);
 for (const {node, original, key} of nodes) node.textContent = original.replace(key, dictionary.get(key)[lang]);
 for (const [node, attribute, labels] of attributes) node.setAttribute(attribute, labels[lang]);
 try { localStorage.setItem('windai-language', lang); } catch { /* Private browsing can disable storage. */ }
 dispatchEvent(new Event('resize'));
}
let savedLanguage = 'en';
try { savedLanguage = localStorage.getItem('windai-language') || 'en'; } catch { /* Keep the default. */ }
setLanguage(savedLanguage);
selector.addEventListener('change', () => setLanguage(selector.value));
addEventListener('hashchange', () => { document.documentElement.lang = selector.value; });
