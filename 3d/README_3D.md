# Wind Farm 3D Digital Twin

Создано по пяти референсам в `assets/` и подходу механической иерархии из AGENT_3D_TWO_STATES_GUIDE.md. Это визуальная модель, не CAD и не модель конкретного производителя.

## Результат и архитектура

Blender 5.2 → Python/bpy → models/wind_farm.blend → GLB → Three.js r180.
Исходник редактируемый. В сцене две независимые турбины. Общая геометрия лопастей переиспользуется. Вращение выполняется только runtime-контроллером, без AnimationMixer. Свет и камера не экспортируются.

```
WindFarm
├── Ground
├── Turbine_1
│   ├── Foundation / Tower / YawBearing / AccessDoor
│   ├── Nacelle
│   │   ├── NacelleShell
│   │   ├── MainShaft
│   │   ├── Gearbox
│   │   └── Generator / Cooling fins
│   └── Rotor
│       ├── Hub
│       └── Blade_1 / Blade_2 / Blade_3
└── Turbine_2 (та же структура, отдельное управление)
```

Узлы компонентов имеют префиксы T1_ и T2_, extras: turbine_id, component_id. Корни турбин содержат assembly_id и selectable. Blender: Z вверх; glTF: Y вверх. Вал и локальная ось вращения ротора — X.

## Размеры и референсы

| Параметр | Принято |
|---|---:|
| Высота оси ротора | 81 м |
| Радиус до кончика лопасти | 42,4 м |
| Радиус башни снизу / сверху | 2,2 / 1,35 м |
| Гондола | 10 × 4,3 × 4,1 м |
| Позиции турбин, Blender | (-49,-9,0), (49,23,0) м |

Все размеры — допущения: приложенные изображения не содержат размерных чертежей. Фотографии определяют силуэт; схемы — порядок ступица → главный вал → редуктор → генератор. Красные концы лопастей взяты из иллюстративного референса. Фундамент и площадка условные.

## Пересоздание, экспорт и проверка

Из корня репозитория:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python 3d/scripts/build_wind_farm.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python 3d/scripts/validate_wind_farm.py
npm ci --prefix 3d/web
npm test --prefix 3d/web
npm run dev --prefix 3d/web
```

Открыть http://127.0.0.1:5173/web/ . Только повторный экспорт:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python 3d/scripts/export_wind_farm.py
```

Генератор перезаписывает свои выходные файлы. Рендеры: renders/assembled.png и renders/inspection.png. Во втором рендере корпус скрыт для наглядности; браузер использует прозрачность 0,18.

## Three.js integration

```js
import { createWindFarmControls } from './wind_farm_controls.mjs';
const gltf = await new GLTFLoader().loadAsync('/models/wind_farm.glb');
scene.add(gltf.scene);
const farm = createWindFarmControls(THREE, gltf);
farm.selectTurbine('turbine_1');
farm.inspectComponent('turbine_1', 'generator');
farm.resetInspection(); // оставляет выбранную турбину подсвеченной
farm.clearSelection(); // восстанавливает исходные материалы
farm.setRotorSpeed('turbine_1', 0.35); // рад/с, визуальная демонстрация
farm.update(deltaSeconds); // внутри render loop
farm.getTurbineId(raycasterHit.object);
farm.getFocusTarget('turbine_1'); // center, size, boundingBox
farm.getComponentFocusTarget('turbine_1', 'generator');
farm.applyTurbineState('turbine_1', { windSpeed: 8 }); // пример входа, не метеоданные
farm.reset(); // исходные материалы и ориентации, скорость 0
farm.dispose(); // восстановить оригинальные материалы и удалить копии
```

Осмотр поддерживает generator, gearbox, main_shaft, rotor и другие component_id. Копии материалов изолируют подсветку между турбинами. Не запускайте AnimationMixer на тех же узлах.

## Backend

Просмотр запрашивает GET /api/turbines/{turbine_id}/details при выборе. Он показывает current из ответа и передаёт current.wind_speed контроллеру. Для отдельного backend настройте reverse proxy /api на том же origin. Без backend работает геометрия, показано честное сообщение о недоступности данных. Прогнозы и метрики не синтезируются. Полный ML dashboard в эту модель не входит.

## Проверки и ограничения

reports/validation_report.json: повторный импорт GLB, один корень, имена, родители, метаданные, pivot, материалы, мировые трансформации.
reports/web_validation.json: загрузка реального GLB через GLTFLoader, переключение выбора, независимые материалы и роторы, инспекция трёх механизмов, сброс, поиск ID и bounding box.
reports/model_manifest.json содержит измеренные характеристики экспортированного GLB.
В браузере вручную проверены загрузка, выбор и X-Ray. Нет физической симуляции, аэродинамического расчёта или сертифицированной компоновки. Гондола и механизмы упрощены; полной взрыв-схемы нет. Состояния NORMAL / SELECTED / INSPECTION используют одну модель.
