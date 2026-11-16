"""Import the SOYUZ training catalogue only. The CRM remains read-only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('J:/Projects/Shaver Family (CRM)/app/data/reference/price_list.json')
catalogue = json.loads(SOURCE.read_text(encoding='utf-8'))
records = {s['source_rows'][0]: s for s in catalogue['services'] if s['branch'] == 'souz'}
assert records[27]['name'] == 'Мужская стрижка' and records[27]['price_from'] == 1500
assert records[44]['price_from'] == 2300
data = json.loads((ROOT / 'content/service-catalog.json').read_text(encoding='utf-8'))
if data['metadata']['status'] == 'soyuz-training-catalogue':
    raise SystemExit('SOYUZ import already applied; review a later catalogue revision before importing again.')
photos = json.loads((ROOT / 'content/service-photos.json').read_text(encoding='utf-8'))
mapping = {
    '267602': 27, '15270008': 20, '267630': 44, '267628': 35, '6129311': 76,
    '28485114': 4, '5768512': 61, '12398982': 30, '267631': 41, '4449458': 33,
    '646764': 53, '267649': 50, '7171247': 22, '15747139': 25, '28485093': 2,
    '15747049': 72, '28485066': 74, '6129319': 78, '6129299': 80, '4483882': 68,
    '14360790': 84, '267692': 88, '14360785': 86, '11066470': 90,
}
descriptions = {
    27: 'Обсудим форму и длину. В стрижку входят мытьё головы, работа ножницами или машинкой и укладка феном со стайлингом под твои волосы.',
    30: 'Для волос от 5 см, если хочешь сохранить длину. Стрижём ножницами, без машинки; работа с каждой прядью занимает больше времени.',
    35: 'Стрижка для мальчиков от 4 до 12 лет включительно: знакомство с инструментами, мытьё головы, стрижка и укладка.',
    41: 'Форма бороды в комбинированных техниках и СПА с горячими полотенцами или вапоризатором. По пожеланиям и особенностям кожи заменим опасную бритву шейвером или триммером. СПА входит в стоимость.',
    44: 'Мужская стрижка и моделирование бороды опасной бритвой за один визит. СПА входит в стоимость. По пожеланиям и особенностям кожи используем шейвер или триммер.',
    50: 'Моделирование бороды, СПА-уход и тонирование. СПА входит в стоимость; опасную бритву можно заменить шейвером или триммером.',
    53: 'Мужская стрижка, моделирование бороды, СПА-уход и тонирование бороды за один визит. СПА входит в стоимость; способ бритья обсудим перед началом.',
    33: 'Мытьё головы, аккуратная окантовка и вечерняя укладка — освежить образ между стрижками.',
    57: 'Бритьё головы и СПА-уход.',
    48: 'Бритьё головы налысо, моделирование бороды опасной бритвой, СПА и тонирование бороды.',
    20: 'Мужская стрижка, маска для волос, скрабирование кожи головы, коррекция бровей, удаление волос из ушей и носа и пятиэтапный СПА-уход за лицом.',
    22: 'Моделирование бороды и СПА, коррекция бровей, удаление волос из ушей и носа и пятиэтапный уход за кожей лица.',
    25: 'Мужская стрижка и моделирование бороды со СПА, питание волос маской, пилинг кожи головы, коррекция бровей, удаление волос из ушей и носа и пятиэтапный уход за лицом.',
    4: 'Классический массаж лица для отдыха и расслабления. Эстетическая и релаксационная услуга, не медицинская процедура.',
    2: 'Экспресс-массаж с проработкой шеи, овала лица, зоны глаз и лба. Эстетическая и релаксационная услуга, не медицинская процедура.',
    72: 'Десятиэтапный СПА-уход за кожей лица. Состав ухода уточни перед записью.',
    74: 'Подравниваем брови и убираем лишние волоски, сохраняя естественную форму.',
    76: 'Быстрая коррекция формы бровей воском и опасной бритвой.',
    78: 'Удаление нежелательных волос из ушей воском.',
    80: 'Удаление нежелательных волос из носа воском.',
    68: 'Удаление волос из носа и ушей и коррекция бровей в одном комплексе.',
    70: 'Мужское оформление бровей и окрашивание за один визит.',
    82: 'Глубокое очищение кожи головы и корней волос. Питательную маску наносят на волосы средней длины или длинные волосы.',
    84: 'Окрашивание волос для изменения оттенка или закрашивания седины. Стоимость уточняем в указанном диапазоне перед процедурой.',
    86: 'Окрашивание бороды для более плотного покрытия седины или изменения оттенка. Стоимость уточняем в указанном диапазоне перед процедурой.',
    88: 'Тонирование волос: менее плотное покрытие и естественный оттенок. Стоимость уточняем в указанном диапазоне перед процедурой.',
    90: 'Тонирование бороды для более ровного оттенка. Стоимость уточняем в указанном диапазоне перед процедурой.',
    61: 'Совместная запись отца и сына. Стоимость и время зависят от состава записи; условия уточни у администратора.',
}
def service(identifier, row):
    source = records[row]
    minimum, maximum = source['duration_min'], source['duration_max']
    duration = '' if minimum is None else f'{minimum} мин' if minimum == maximum else f'{minimum}–{maximum} мин'
    return {'id': identifier, 'name': source['name'].replace('NEW! ', ''), 'description': descriptions[row],
            'duration': duration, 'price': source['price_from'], 'priceLabel': source['price_display'],
            'source': {'branch': 'souz', 'file': source['source_file'], 'rows': source['source_rows'],
                       'priceFrom': source['price_from'], 'priceTo': source['price_to'],
                       'descriptionStatus': source['description_status']}}
for category in data['categories']:
    category['services'] = [service(s['id'], mapping[s['id'].split('-')[-1]]) for s in category['services']]
def add(category_id, row, suffix):
    category = next(c for c in data['categories'] if c['id'] == category_id)
    identifier = f'{category_id}-soyuz-{suffix}'
    category['services'].append(service(identifier, row))
    photos['images'][identifier] = photos['images'][category['services'][0]['id']]
add('hair-beard', 57, 'head-shave')
add('main', 48, 'head-beard')
add('extra', 70, 'brows-color')
add('extra', 82, 'peeling')
premium = next(c for c in data['categories'] if c['id'] == 'premium')
premium['name'] = 'Премиум и СПА'
extra = next(c for c in data['categories'] if c['id'] == 'extra')
for row in [4, 2, 72]:
    item = next(s for s in extra['services'] if s['source']['rows'][0] == row)
    extra['services'].remove(item)
    premium['services'].append(item)
metadata = {'source': str(SOURCE).replace('\\', '/'), 'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'asOf': '2026-11-09', 'exportDate': catalogue['export_date'], 'status': 'soyuz-training-catalogue',
            'branch': 'souz', 'branchAttribution': catalogue['branch_attribution'],
            'livePricesVerified': False, 'ownerPolicy': 'Use SOYUZ administrator training; no biowave, braids or cornrows.'}
data['metadata'] = metadata
assert len({s['id'] for c in data['categories'] for s in c['services']}) == sum(len(c['services']) for c in data['categories'])
assert max(len(c['services']) for c in data['categories']) <= 8
for filename, value in [('service-catalog.json', data), ('service-photos.json', photos),
                         ('service-catalog-sources.json', {**metadata, 'sourceFiles': catalogue['source_files'],
                         'notes': ['Only souz records imported. Ranges retained. Empty duration remains empty.',
                         'Booking-time, model recruitment and unconfirmed student/promotion conditions are not ordinary public services.',
                         'Cross-brand descriptions are not copied. Short descriptions use literal service composition.']})]:
    (ROOT / 'content' / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Imported SOYUZ training prices and durations; CRM unchanged.')
