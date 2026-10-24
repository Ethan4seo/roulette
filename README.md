# 빙글 룰렛

가입·설치 없이 쓰는 무료 온라인 돌림판입니다. (점심 메뉴, 벌칙, 숫자 뽑기)

## 구조
- `src/assets/` : 화면 디자인(style.css)과 룰렛 동작(roulette.js)
- `build.py` : 페이지 내용과 함께 `docs/`에 완성된 사이트를 만듭니다
- `docs/` : 실제로 공개되는 사이트 (GitHub Pages가 이 폴더를 그대로 공개)
- `site.json` : 사이트 설정 한 곳 — 도메인, 구글 애드센스 번호, 문의 이메일, 검색 등록 확인 코드

## 수정 후 다시 만들기
```
python3 build.py
```
`site.json`에 값을 넣고 다시 만들면 sitemap.xml, ads.txt, CNAME, 광고 코드가 자동으로 들어갑니다.
