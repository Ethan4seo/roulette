"""빙글 룰렛 사이트 생성기.

src/ 의 CSS·JS 와 아래 페이지 내용으로 docs/ 에 완성된 사이트를 만든다 (GitHub Pages 가 docs/ 를 그대로 공개).
설정은 site.json 한 곳에서 바꾼다: 도메인(url), 구글 애드센스 번호(adsense_client), 문의 이메일 등.

    python build.py                 # docs/ 생성
    python build.py --preview 파일   # 미리보기용 한 장짜리 페이지(Claude Artifact 형식)도 생성
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "docs"
CFG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
NAME = CFG["name"]
YEAR = "2026"
UPDATED = "2026-10-24"

FONTS = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600&family=Jua&display=swap"

NAV = [("", "룰렛 돌리기"), ("lunch", "점심 메뉴"), ("penalty", "벌칙"), ("number", "숫자 뽑기")]

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<circle cx="32" cy="34" r="29" fill="#1e2738"/>
<g transform="translate(32 34)">
<path d="M0 0 L0 -24 A24 24 0 0 1 20.78 -12 Z" fill="#ff6b57"/>
<path d="M0 0 L20.78 -12 A24 24 0 0 1 20.78 12 Z" fill="#ffc145"/>
<path d="M0 0 L20.78 12 A24 24 0 0 1 0 24 Z" fill="#3cc9a8"/>
<path d="M0 0 L0 24 A24 24 0 0 1 -20.78 12 Z" fill="#5b95ff"/>
<path d="M0 0 L-20.78 12 A24 24 0 0 1 -20.78 -12 Z" fill="#a487ff"/>
<path d="M0 0 L-20.78 -12 A24 24 0 0 1 0 -24 Z" fill="#ff8cc6"/>
<circle r="6" fill="#f0412c" stroke="#1e2738" stroke-width="2.5"/>
</g>
<path d="M24 1 H40 V7 L32 17 L24 7 Z" fill="#f0412c"/>
</svg>
"""

# ---------- 페이지 내용 ----------
COMMON_FAQ_RANDOM = ("결과는 정말 무작위인가요?",
                     "네. 브라우저에 들어 있는 암호용 난수 생성기(crypto.getRandomValues)로 멈출 자리를 정합니다. "
                     "누가 언제 돌려도 각 칸이 뽑힐 확률은 그 칸의 크기에 정확히 비례하고, 이전 결과의 영향을 받지 않습니다.")
COMMON_FAQ_SAVE = ("적은 항목은 어디에 저장되나요?",
                   "다음에 다시 쓸 수 있게 지금 쓰는 기기의 브라우저에만 저장됩니다. 서버로 보내거나 다른 사람이 볼 수 있는 곳에 남기지 않습니다.")

PAGES = [
    {
        "slug": "", "key": "main",
        "title": f"룰렛 돌리기 - 무료 온라인 돌림판 | {NAME}",
        "description": "항목을 적고 버튼만 누르면 끝나는 무료 온라인 룰렛(돌림판). 점심 메뉴, 벌칙, 당번, 경품 추첨을 공정하게 정하세요. 가입·설치 없이 휴대폰에서 바로 됩니다.",
        "h1": "룰렛 돌리기",
        "lede": "항목을 적고 돌리면 끝. 점심 메뉴, 벌칙, 당번, 경품 추첨까지 공정하게 정해 주는 무료 돌림판입니다.",
        "items": ["민준", "서연", "도윤", "하은", "지호", "수아"],
        "chips": ["names", "lunch", "penalty", "numbers", "yesno"],
        "how": [("항목 적기", "오른쪽 칸에 한 줄에 하나씩 적습니다. 사람 이름, 메뉴, 벌칙, 선물 무엇이든 됩니다."),
                ("돌리기", "'돌리기' 버튼이나 돌림판 가운데를 누르세요. 컴퓨터에서는 스페이스바를 눌러도 돌아갑니다."),
                ("결과 확인과 공유", "멈춘 칸이 결과입니다. 결과는 기록에 남고, '이 룰렛 공유'를 누르면 같은 항목이 담긴 링크를 친구에게 보낼 수 있어요.")],
        "uses_title": "이럴 때 써요",
        "uses": ["커피 내기, 밥값 내기", "청소·발표·회의록 당번 정하기", "댓글 이벤트 당첨자 추첨", "모임 장소나 여행지 고르기",
                 "수업 시간 발표 순서 정하기 ('당첨된 항목은 빼고 다시 돌리기'를 켜면 순서대로 뽑혀요)"],
        "faq": [COMMON_FAQ_RANDOM,
                ("특정 항목이 더 잘 나오게 할 수 있나요?", "항목 뒤에 *2, *3처럼 숫자를 붙이면 그 칸이 그만큼 커지고 뽑힐 확률도 같은 비율로 올라갑니다. 예를 들어 '치킨*2'는 다른 항목보다 두 배 자주 나옵니다."),
                ("항목은 몇 개까지 넣을 수 있나요?", "2개부터 60개까지 넣을 수 있습니다. 항목이 많을수록 글씨가 작아지니 휴대폰에서는 20개 안쪽을 권합니다."),
                ("당첨된 사람을 빼고 계속 뽑을 수 있나요?", "'당첨된 항목은 빼고 다시 돌리기'를 켜 두면, 다음에 돌릴 때 직전에 당첨된 항목이 목록에서 빠집니다. 발표 순서나 여러 명을 차례로 뽑을 때 좋습니다."),
                COMMON_FAQ_SAVE],
    },
    {
        "slug": "lunch", "key": "lunch",
        "title": f"점심 메뉴 룰렛 - 오늘 뭐 먹지? | {NAME}",
        "description": "오늘 점심 뭐 먹을지 고민될 때 돌리는 점심 메뉴 룰렛. 한식·중식·일식·양식 기본 메뉴가 들어 있고, 회사 근처 식당 이름으로 바꿔 쓸 수 있어요.",
        "h1": "점심 메뉴 룰렛",
        "lede": "\"오늘 뭐 먹지?\" 회의는 그만. 메뉴를 돌림판에 맡기고 바로 출발하세요.",
        "items": ["김치찌개", "제육볶음", "짜장면", "돈가스", "쌀국수", "초밥", "햄버거", "칼국수"],
        "chips": ["lunch", "yesno", "names"],
        "how": [("후보 메뉴 정하기", "기본 메뉴 8개가 들어 있습니다. 회사나 학교 근처 식당 이름으로 바꾸면 결과가 나오자마자 출발할 수 있어요."),
                ("돌리기", "버튼을 누르면 4~6초 동안 돌다가 멈춥니다. 멈춘 칸이 오늘의 점심입니다."),
                ("팀원과 같이 보기", "'이 룰렛 공유'로 링크를 보내면 팀원도 같은 메뉴판으로 돌려 볼 수 있습니다.")],
        "uses_title": "메뉴 고르는 요령",
        "uses": ["후보는 6~8개가 적당합니다. 너무 많으면 '이건 좀…' 하는 결과가 자주 나와요.",
                 "어제 먹은 메뉴는 미리 빼 두세요.",
                 "다들 좋아하는 메뉴는 뒤에 *2를 붙여 칸을 키우면 당첨 확률이 두 배가 됩니다.",
                 "결과에 따르기로 돌리기 전에 정해 두면 고민이 훨씬 빨리 끝납니다."],
        "faq": [("메뉴를 우리 동네 식당으로 바꿀 수 있나요?", "네. 오른쪽 칸의 글자를 지우고 식당 이름을 한 줄에 하나씩 적으면 바로 돌림판이 바뀝니다. 적은 목록은 이 기기에 저장돼 다음에도 그대로 나옵니다."),
                ("결과가 마음에 안 들면 다시 돌려도 되나요?", "물론입니다. 다만 매번 다시 돌리면 끝이 안 나니, '한 번만 다시'처럼 규칙을 정해 두는 걸 권합니다."),
                COMMON_FAQ_RANDOM],
    },
    {
        "slug": "penalty", "key": "penalty",
        "title": f"벌칙 룰렛 - 모임·게임 벌칙 정하기 | {NAME}",
        "description": "게임에서 진 사람의 벌칙을 공정하게 정하는 벌칙 룰렛. 웃기지만 무리하지 않은 기본 벌칙이 들어 있고, 우리끼리 벌칙으로 바꿔 쓸 수 있어요.",
        "h1": "벌칙 룰렛",
        "lede": "진 사람도 웃으면서 받는 벌칙. 고르는 사람 탓하지 않게 돌림판에 맡기세요.",
        "items": ["노래 한 소절", "성대모사 하나", "커피 사기", "애교 3초", "칭찬 세 마디", "다음 판 깍두기", "엉덩이로 이름 쓰기", "면제 찬스"],
        "chips": ["penalty", "names", "yesno"],
        "how": [("벌칙 정하기", "기본 벌칙 8개가 들어 있습니다. 모임 분위기에 맞게 고치거나 새 벌칙을 한 줄씩 더 적으세요."),
                ("진 사람이 직접 돌리기", "진 사람이 버튼을 누르게 하면 결과에 대한 불만이 줄어듭니다."),
                ("결과 기록 보기", "누가 어떤 벌칙을 받았는지 기록에 시간과 함께 남습니다.")],
        "uses_title": "벌칙 정할 때 지키면 좋은 것",
        "uses": ["모두가 웃을 수 있는 정도로만 정하세요. 누군가 곤란해지는 벌칙은 빼는 게 좋습니다.",
                 "돈이 드는 벌칙은 '5천 원 이하'처럼 금액을 미리 정하세요.",
                 "몸이 불편하거나 위험한 벌칙, 억지로 시키는 벌칙은 넣지 않습니다.",
                 "'면제 찬스' 같은 칸을 하나 넣으면 분위기가 더 살아납니다."],
        "faq": [("벌칙을 사람마다 다르게 할 수 있나요?", "모임마다 저장해 두기는 어렵지만, '이 룰렛 공유'로 만든 링크를 즐겨찾기 해 두면 그 벌칙 목록을 언제든 다시 열 수 있습니다."),
                ("자주 나왔으면 하는 벌칙이 있어요.", "그 벌칙 뒤에 *2나 *3을 붙이세요. 칸이 커지는 만큼 당첨 확률도 올라갑니다."),
                COMMON_FAQ_RANDOM],
    },
    {
        "slug": "number", "key": "number",
        "title": f"숫자 룰렛 - 번호 뽑기·순서 정하기 | {NAME}",
        "description": "시작 번호와 끝 번호만 넣으면 숫자 룰렛이 만들어집니다. 번호 추첨, 발표 순서, 좌석 번호 뽑기를 공정하게 하세요.",
        "h1": "숫자 룰렛",
        "lede": "번호 범위만 정하면 끝. 출석 번호, 응모 번호, 발표 순서를 공정하게 뽑아요.",
        "items": [str(i) for i in range(1, 11)],
        "chips": ["numbers", "yesno"],
        "range": True,
        "how": [("번호 범위 넣기", "'시작'과 '끝'에 숫자를 넣고 '번호 채우기'를 누르세요. 예를 들어 1과 30을 넣으면 1번부터 30번까지 칸이 생깁니다."),
                ("돌리기", "버튼을 누르면 돌림판이 돌다가 한 번호에서 멈춥니다."),
                ("여러 명 뽑기", "'당첨된 항목은 빼고 다시 돌리기'를 켜면 한 번 뽑힌 번호는 다음 판에서 빠져서 겹치지 않게 차례로 뽑을 수 있습니다.")],
        "uses_title": "이럴 때 써요",
        "uses": ["반 출석 번호로 발표자 뽑기", "응모 번호로 경품 당첨자 추첨", "자리 번호, 조 번호 정하기", "게임 순서 정하기"],
        "faq": [("같은 번호가 또 나올 수 있나요?", "'당첨된 항목은 빼고 다시 돌리기'를 끄면 매번 모든 번호가 다시 후보가 되므로 같은 번호가 나올 수 있습니다. 겹치지 않게 뽑으려면 켜 두세요."),
                ("번호는 몇 개까지 되나요?", "한 번에 60개까지 넣을 수 있습니다. 그보다 많으면 1~60, 61~120처럼 나눠서 뽑으세요."),
                COMMON_FAQ_RANDOM],
    },
]

CHIP_LABEL = {"names": "이름 예시", "lunch": "점심 메뉴", "penalty": "벌칙", "numbers": "숫자 1~10", "yesno": "예 / 아니오"}


# ---------- 조립 ----------
def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page_url(slug: str) -> str:
    base = CFG.get("url", "").rstrip("/")
    return f"{base}/{slug + '/' if slug else ''}" if base else ""


def header(root: str, current: str, preview: bool) -> str:
    links = "" if preview else "".join(
        f'<a href="{root}{s + "/" if s else ""}"{" aria-current=\"page\"" if s == current else ""}>{esc(t)}</a>' for s, t in NAV)
    nav = f'<nav class="nav" aria-label="룰렛 종류">{links}</nav>' if links else ""
    home = "#" if preview else (root or "./")
    return (f'<header class="top"><div class="wrap"><a class="brand" href="{home}">{FAVICON.replace("<svg ", "<svg aria-hidden=\"true\" ")}{esc(NAME)}</a>'
            f'{nav}</div></header>')


def footer(root: str, preview: bool) -> str:
    links = "" if preview else f'<nav><a href="{root}about/">소개·문의</a><a href="{root}privacy/">개인정보처리방침</a></nav>'
    return f'<footer class="foot"><div class="wrap"><span>© {YEAR} {esc(NAME)}</span>{links}</div></footer>'


def tool(p: dict) -> str:
    chips = "".join(f'<button type="button" class="chip" data-preset="{c}">{CHIP_LABEL[c]}</button>' for c in p["chips"])
    rng = ""
    if p.get("range"):
        rng = ('<div class="range"><label for="from">시작</label><input id="from" type="number" inputmode="numeric" value="1">'
               '<label for="to">끝</label><input id="to" type="number" inputmode="numeric" value="10">'
               '<button type="button" class="btn" id="fill-range">번호 채우기</button></div>')
    return f"""<section class="tool wrap" aria-label="룰렛">
  <div class="stage">
    <div class="wheel-box">
      <canvas id="wheel" role="img" aria-label="룰렛 돌림판"></canvas>
      <div class="pointer" id="pointer" aria-hidden="true"></div>
      <button type="button" class="hub" id="hub" aria-label="룰렛 돌리기">돌려!</button>
    </div>
    <div class="result" id="result" role="status" aria-live="polite"><span class="label">결과가 여기에 나와요</span></div>
    <button type="button" class="spin" id="spin">돌리기</button>
    <p class="hint">컴퓨터에서는 스페이스바로도 돌릴 수 있어요</p>
  </div>
  <div class="panel">
    <div class="panel-head"><label for="items">항목</label><span class="count" id="count">{len(p["items"])}개</span></div>
    {rng}
    <textarea id="items" spellcheck="false" autocomplete="off">{esc(chr(10).join(p["items"]))}</textarea>
    <p class="help">한 줄에 하나씩 적어요. 뒤에 <code>*2</code>를 붙이면 칸과 확률이 두 배가 됩니다. (예: 치킨*2)</p>
    <div class="chips"><span class="chips-title">빠르게 채우기</span>{chips}</div>
    <div class="opts">
      <label><input type="checkbox" id="remove-winner"> 당첨된 항목은 빼고 다시 돌리기</label>
      <label><input type="checkbox" id="sound" checked> 소리 켜기</label>
    </div>
    <div class="row"><button type="button" class="btn" id="shuffle">순서 섞기</button><button type="button" class="btn" id="share">이 룰렛 공유</button></div>
    <input id="share-url" class="btn" type="text" readonly hidden aria-label="공유 링크">
    <div class="history"><h2>결과 기록 <button type="button" class="link" id="clear-history">지우기</button></h2><ol id="history"></ol></div>
  </div>
</section>"""


def content(p: dict) -> str:
    steps = "".join(f"<li><div><b>{esc(t)}</b>{esc(d)}</div></li>" for t, d in p["how"])
    uses = "".join(f"<li>{esc(u)}</li>" for u in p["uses"])
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in p["faq"])
    return f"""<div class="content wrap">
  <section><h2>사용 방법</h2><ol class="steps">{steps}</ol></section>
  <section><h2>{esc(p["uses_title"])}</h2><ul class="uses">{uses}</ul></section>
  <section class="faq"><h2>자주 묻는 질문</h2>{faq}</section>
</div>"""


def head(p: dict, root: str, ver: str) -> str:
    url = page_url(p["slug"])
    tags = [f'<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            f'<title>{esc(p["title"])}</title>',
            f'<meta name="description" content="{esc(p["description"])}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:title" content="{esc(p["h1"] + " | " + NAME)}">',
            f'<meta property="og:description" content="{esc(p["description"])}">',
            f'<meta property="og:site_name" content="{esc(NAME)}">',
            '<meta property="og:locale" content="ko_KR">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="theme-color" content="#f0412c">',
            f'<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">',
            f'<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">',
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            f'<link rel="stylesheet" href="{FONTS}">',
            f'<link rel="stylesheet" href="{root}assets/style.css?v={ver}">']
    if url:
        base = CFG["url"].rstrip("/")
        tags += [f'<link rel="canonical" href="{url}">', f'<meta property="og:url" content="{url}">',
                 f'<meta property="og:image" content="{base}/og.png">']
        if p.get("h1"):
            ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": p["h1"], "url": url,
                  "applicationCategory": "UtilitiesApplication", "operatingSystem": "웹 브라우저", "inLanguage": "ko",
                  "offers": {"@type": "Offer", "price": "0", "priceCurrency": "KRW"}, "description": p["description"]}
            tags.append(f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    if CFG.get("google_site_verification"):
        tags.append(f'<meta name="google-site-verification" content="{esc(CFG["google_site_verification"])}">')
    if CFG.get("naver_site_verification"):
        tags.append(f'<meta name="naver-site-verification" content="{esc(CFG["naver_site_verification"])}">')
    if CFG.get("adsense_client"):
        tags.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(CFG["adsense_client"])}" crossorigin="anonymous"></script>')
    return "\n".join(tags)


def document(p: dict, body: str, root: str, ver: str, script: bool = True) -> str:
    js = f'\n<script src="{root}assets/roulette.js?v={ver}" defer></script>' if script else ""
    return (f'<!doctype html>\n<html lang="ko">\n<head>\n{head(p, root, ver)}\n</head>\n<body data-page="{p["key"]}">\n'
            f'{header(root, p["slug"], False)}\n<main>\n{body}\n</main>\n{footer(root, False)}\n'
            f'<div class="toast" id="toast" role="status" aria-live="polite" hidden></div>{js}\n</body>\n</html>\n')


def tool_body(p: dict) -> str:
    hero = f'<section class="hero wrap"><h1>{esc(p["h1"])}</h1><p class="lede">{esc(p["lede"])}</p></section>'
    return f"{hero}\n{tool(p)}\n{content(p)}"


def contact_html() -> str:
    mail = CFG.get("contact_email", "").strip()
    return f'<a href="mailto:{esc(mail)}">{esc(mail)}</a>' if mail else "문의 이메일 준비 중입니다."


def about_page(root: str, ver: str) -> str:
    p = {"slug": "about", "key": "about", "title": f"소개·문의 | {NAME}", "h1": "",
         "description": f"{NAME}는 가입이나 설치 없이 쓰는 무료 온라인 돌림판입니다. 만든 이유와 문의 방법을 안내합니다."}
    body = f"""<article class="doc wrap">
<h1>{esc(NAME)} 소개</h1>
<p>{esc(NAME)}는 점심 메뉴, 벌칙, 당번, 경품 추첨처럼 일상에서 무언가를 공정하게 정해야 할 때 쓰는 무료 온라인 돌림판입니다.
가입이나 앱 설치 없이 휴대폰과 컴퓨터 브라우저에서 바로 쓸 수 있습니다.</p>
<h2>공정한 결과를 위해</h2>
<p>돌림판이 멈출 자리는 브라우저의 암호용 난수 생성기로 정합니다. 각 항목이 뽑힐 확률은 화면에 보이는 칸의 크기와 같고, 운영자를 포함해 누구도 결과를 미리 정할 수 없습니다.</p>
<h2>내 정보는 어떻게 되나요</h2>
<p>적은 항목은 쓰는 기기의 브라우저에만 저장되며 서버로 보내지 않습니다. 자세한 내용은 <a href="{root}privacy/">개인정보처리방침</a>을 확인하세요.</p>
<h2>문의</h2>
<p>오류 제보, 기능 제안, 광고 문의는 아래 이메일로 보내 주세요.</p>
<p>{contact_html()}</p>
</article>"""
    return document(p, body, root, ver, script=False)


def privacy_page(root: str, ver: str) -> str:
    p = {"slug": "privacy", "key": "privacy", "title": f"개인정보처리방침 | {NAME}", "h1": "",
         "description": f"{NAME}의 개인정보처리방침입니다. 수집하는 정보, 쿠키와 광고, 문의 방법을 안내합니다."}
    body = f"""<article class="doc wrap">
<h1>개인정보처리방침</h1>
<p class="meta">시행일: {UPDATED}</p>
<p>{esc(NAME)}(이하 "사이트")는 이용자의 개인정보를 소중히 여기며, 「개인정보 보호법」 등 관련 법령을 지킵니다.</p>
<h2>1. 수집하는 개인정보</h2>
<p>사이트는 회원가입이 없으며 이름, 연락처 등 개인을 알아볼 수 있는 정보를 직접 수집하지 않습니다.
돌림판에 적은 항목은 다음 방문 때 다시 보여 주기 위해 이용자 기기의 브라우저 저장소(localStorage)에만 저장되며, 사이트 서버로 전송되지 않습니다.
브라우저 설정에서 사이트 데이터를 지우면 함께 삭제됩니다.</p>
<h2>2. 쿠키와 광고</h2>
<p>사이트는 운영비를 마련하기 위해 Google 애드센스 광고를 게재할 수 있습니다. Google을 포함한 제3자 광고 사업자는 쿠키를 사용하여 이용자가 이 사이트와 다른 사이트를 방문한 기록을 바탕으로 광고를 게재할 수 있습니다.</p>
<ul>
<li>Google의 광고 쿠키 사용으로 Google과 파트너는 이용자의 사이트 방문 기록을 바탕으로 광고를 게재할 수 있습니다.</li>
<li>이용자는 <a href="https://adssettings.google.com" rel="noopener" target="_blank">Google 광고 설정</a>에서 맞춤 광고를 끌 수 있습니다.</li>
<li>Google이 데이터를 사용하는 방식은 <a href="https://policies.google.com/technologies/partner-sites" rel="noopener" target="_blank">Google 파트너 사이트 데이터 사용 안내</a>에서 확인할 수 있습니다.</li>
</ul>
<p>이용자는 브라우저 설정으로 쿠키 저장을 거부할 수 있으며, 이 경우에도 돌림판 기능은 그대로 쓸 수 있습니다.</p>
<h2>3. 방문 통계</h2>
<p>사이트 개선을 위해 방문 수, 접속 기기 종류 같은 개인을 식별할 수 없는 통계 정보를 활용할 수 있습니다.</p>
<h2>4. 개인정보 보호 문의</h2>
<p>개인정보와 관련한 문의는 아래로 연락해 주세요.</p>
<p>{contact_html()}</p>
<h2>5. 방침 변경</h2>
<p>이 방침이 바뀌면 이 페이지에 시행일과 함께 알립니다.</p>
</article>"""
    return document(p, body, root, ver, script=False)


def not_found(ver: str) -> str:
    p = {"slug": "404", "key": "404", "title": f"페이지를 찾을 수 없어요 | {NAME}", "h1": "", "description": "요청한 페이지가 없습니다."}
    body = '<article class="doc wrap"><h1>페이지를 찾을 수 없어요</h1><p>주소가 바뀌었거나 없는 페이지입니다.</p><p><a href="/">룰렛 돌리기로 가기</a></p></article>'
    return document(p, body, "/", ver, script=False)


def build() -> str:
    css = (SRC / "assets/style.css").read_text(encoding="utf-8")
    js = (SRC / "assets/roulette.js").read_text(encoding="utf-8")
    ver = hashlib.sha1((css + js).encode()).hexdigest()[:8]
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(SRC / "assets/style.css", OUT / "assets/style.css")
    shutil.copy(SRC / "assets/roulette.js", OUT / "assets/roulette.js")
    for f in ("og.png", "apple-touch-icon.png"):
        if (SRC / f).exists():
            shutil.copy(SRC / f, OUT / f)
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    for p in PAGES:
        root = "../" if p["slug"] else ""
        d = OUT / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(document(p, tool_body(p), root, ver), encoding="utf-8")
    for slug, fn in (("about", about_page), ("privacy", privacy_page)):
        (OUT / slug).mkdir(exist_ok=True)
        (OUT / slug / "index.html").write_text(fn("../", ver), encoding="utf-8")
    (OUT / "404.html").write_text(not_found(ver), encoding="utf-8")

    base = CFG.get("url", "").rstrip("/")
    robots = "User-agent: *\nAllow: /\n" + (f"\nSitemap: {base}/sitemap.xml\n" if base else "")
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")
    if base:
        urls = [page_url(p["slug"]) for p in PAGES] + [f"{base}/about/", f"{base}/privacy/"]
        sm = "".join(f"<url><loc>{u}</loc><lastmod>{UPDATED}</lastmod></url>" for u in urls)
        (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n', encoding="utf-8")
        host = base.split("://", 1)[-1]
        if not host.endswith("github.io"):
            (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")
    if CFG.get("adsense_client"):
        pub = CFG["adsense_client"].replace("ca-", "")
        (OUT / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    return ver


def preview(path: Path) -> None:
    """Claude 미리보기(Artifact)용: 첫 페이지 하나에 CSS·JS 를 넣은 한 장짜리 파일."""
    p = PAGES[0]
    css = (SRC / "assets/style.css").read_text(encoding="utf-8")
    js = (SRC / "assets/roulette.js").read_text(encoding="utf-8")
    body = tool_body(p)
    out = (f'<title>{esc(NAME)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
           f'<link rel="stylesheet" href="{FONTS}">\n<style>\n{css}\n</style>\n'
           f'{header("", "", True)}\n<main>\n{body}\n</main>\n{footer("", True)}\n'
           f'<div class="toast" id="toast" role="status" aria-live="polite" hidden></div>\n<script>\n{js}\n</script>\n')
    path.write_text(out, encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path)
    a = ap.parse_args()
    v = build()
    print(f"docs/ 생성 완료 (버전 {v})")
    if a.preview:
        preview(a.preview)
        print(f"미리보기: {a.preview}")
