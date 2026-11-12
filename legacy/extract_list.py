import re, json, html, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

slugs = ["aalto","aemeath","augusta","baizhi","brant","buling","calcharo","camellya","cantarella","carlotta","cartethyia","changli","chisa","chixia","ciaccona","danjin","denia","encore","galbrena","hiyuki","hsin","iuno","jianxin","jingran","jinhsi","jiyan","lily","lingyang","lucilla","lucy","lumi","lupa","luuk-herssen","lynae","mornye","mortefi","phoebe","phrolova","qingxiao","qiuyuan","rebecca","roccia","rover-aero","rover-electro","rover-havoc","rover-spectro","sanhua","sigrika","suisui","suoming","taoqi","the-shorekeeper","verina","xiangli-yao","yangyang","yangyang-xuanling","yinlin","youhu","yuanwu","zani","zhezhi"]

name_map = {'luuk-herssen':'Luuk Herssen','the-shorekeeper':'The Shorekeeper','xiangli-yao':'Xiangli Yao','rover-aero':'Rover (Aero)','rover-electro':'Rover (Electro)','rover-havoc':'Rover (Havoc)','rover-spectro':'Rover (Spectro)','yangyang-xuanling':'Yangyang (Xuanling)'}
def slug_name(s):
    if s in name_map: return name_map[s]
    return ' '.join(w.capitalize() for w in s.split('-'))

def fetch(slug):
    url = f"https://www.prydwen.gg/wuthering-waves/characters/{slug}"
    headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.9',
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'ignore')
        except Exception:
            if attempt == 2: raise
            time.sleep(1.5)

def parse_skill_details(det):
    body = det.find('div', class_='skill-with-coloring')
    if body is None:
        body = det
    lines = []
    for child in body.find_all(['p','li'], recursive=True):
        if child.name == 'p' and child.find_parent('li'):
            continue
        if child.find_parent(class_='pw-accordion'):
            continue
        txt = child.get_text(' ', strip=True).replace('\u200b','')
        txt = re.sub(r'\s+', ' ', txt).strip()
        if not txt: continue
        lines.append(('• ' if child.name == 'li' else '') + txt)
    out = []
    for l in lines:
        if not out or out[-1] != l:
            out.append(l)
    return out

def parse_skills(soup):
    skills = []
    tab = None
    for t in soup.find_all('div', class_='tab-inside'):
        if t.find('div', class_='skills'):
            tab = t; break
    scope = tab or soup
    seen = set()
    for box in scope.find_all('div', class_='box skill-new'):
        icon = box.find('div', class_='skill-icon')
        name_el = box.find('p', class_='skill-name')
        det = box.find('div', class_='skill-details')
        if not (icon and name_el and det): continue
        stype = icon.get_text(' ', strip=True)
        sname = name_el.get_text(' ', strip=True)
        key = (stype, sname)
        if key in seen: continue
        seen.add(key)
        skills.append({'type': stype, 'name': sname, 'desc': parse_skill_details(det)})
    return skills

def extract(slug):
    h = fetch(slug)
    soup = BeautifulSoup(h, 'lxml')
    text = soup.get_text('\n', strip=True)
    joined = re.sub(r'\s+', ' ', text)
    m = re.search(r'is a\s+(4|5)\s*★\s*rarity character from the\s+([A-Za-z]+)\s+element who uses the\s+([A-Za-z ]+?)\s+type weapon', joined, re.I)
    im = re.search(r'type weapon\.?\s*(.+?)(?:To learn more|Use the tabs|Video guide|Profile|Kit Review|Best guide)', joined, re.I)
    intro = im.group(1).strip() if im else ''
    intro = re.sub(r'\s+', ' ', intro)
    if 'To learn more' in intro: intro = ''
    full = soup.find('img', src=re.compile(r'_full\.webp$'))
    icon = soup.find('img', src=re.compile(r'_icon\.webp$'))
    card = soup.find('img', src=re.compile(r'_card\.webp$'))
    return {
        'slug': slug,
        'name': slug_name(slug),
        'rarity': int(m.group(1)) if m else 0,
        'element': m.group(2) if m else '',
        'weapon': m.group(3).strip() if m else '',
        'intro': intro,
        'skills': parse_skills(soup),
        'img_full': full['src'] if full else '',
        'img_icon': icon['src'] if icon else (card['src'] if card else ''),
        'img_card': card['src'] if card else '',
        'source': f"https://www.prydwen.gg/wuthering-waves/characters/{slug}",
    }

with ThreadPoolExecutor(max_workers=4) as ex:
    data = list(ex.map(extract, slugs))

data.sort(key=lambda c: (-c['rarity'], c['name']))
with open('/home/devmindtan/wuwa-characters/data_list.json','w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print('chars', len(data), 'skills', sum(len(c['skills']) for c in data))
for c in data:
    print(f"{c['name']:18} {c['rarity']}★ {c['element']:8} {c['weapon']:10} skills={len(c['skills'])} desc={sum(len(s['desc']) for s in c['skills'])}")
