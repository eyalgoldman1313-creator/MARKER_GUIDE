"""Bake top-bookmarks.json into index.html: a "סימניות עליונות" strip in every standard,
a colour key under the "הפירוט לכל תקן" heading, and the CSS/JS that go with them.
Safe to re-run: everything it inserts is removed first.

    python tools/apply_top_bookmarks.py            (run from the MARKER_GUIDE folder)
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEANING = {'Y': 'גבול: חריג, תנאי, איסור, מועד, סף', 'G': 'מה המבקר חייב לעשות', 'P': 'מושג או הגדרה',
           'p': 'מצב אצל המבוקר', 'O': 'דיווח, תקשור ותיעוד', 'b': 'שיקול דעת', 'B': 'קישור לתקן או לחוק אחר',
           'V': 'נספחים ונוסחי דוח'}


def text_on(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return '#FFFFFF' if 1.05 / (L + 0.05) > (L + 0.05) / 0.0646 else '#16202A'


def esc(t):
    return html.escape(t, quote=True)


def strip_html(std):
    bms = std['bookmarks']
    real = [b for b in bms if not b['side']]
    if not bms:
        return '<div class="tbm none"><b class="tbm-h">סימניות עליונות</b><span>אין · סימניית צד בלבד</span></div>\n'
    out = ['<div class="tbm"><b class="tbm-h">סימניות עליונות <i>%d</i></b><div class="tbm-l">' % len(real)]
    for b in bms:
        meta = []
        if b['page'] is not None: meta.append("עמ' %d" % b['page'])
        if b['count']: meta.append('נבחן ×%d' % b['count'])
        meta.append('סימניית הצד מספיקה' if b['side'] else 'מסלול %d' % b['lane'])
        rows = ','.join(str(r) for r in b['rows'])
        tag = 'a' if rows else 'span'
        attrs = ' href="#" data-rows="%s"' % rows if rows else ''
        title = ('בעמוד הפתיחה של התקן, בלי סימנייה עליונה · ' if b['side'] else 'סימנייה %s · %s · ' % (b['color_name'], MEANING[b['color']])) + b['label']
        out.append('<%s class="tb%s"%s style="--c:%s;--tc:%s" title="%s"><span class="tg">%s</span>'
                   '<span class="tb-x"><span class="tb-t">%s</span><span class="tb-m">%s</span></span></%s>'
                   % (tag, ' side' if b['side'] else '', attrs, b['hex'], text_on(b['hex']), esc(title),
                      esc(b['write']) or '&nbsp;', esc(b['label']), ' · '.join(meta), tag))
    out.append('</div></div>\n')
    return ''.join(out)


CSS = r'''
/*tbm-start*/
.tbm{margin:10px 0;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--paper)}
.tbm-h{display:flex;align-items:center;gap:8px;font-size:14.5px;font-weight:900;margin-bottom:8px}
.tbm-h i{font-style:normal;font-size:12px;font-weight:700;background:var(--ink);color:#fff;border-radius:999px;padding:0 8px}
.tbm.none{display:flex;gap:10px;align-items:baseline;color:var(--ink2);font-size:14px}
.tbm.none .tbm-h{margin:0;color:var(--ink)}
.tbm-l{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:6px 10px}
.tb{display:flex;align-items:flex-start;gap:9px;padding:5px 8px;border-radius:8px;background:var(--card);border:1px solid var(--line);color:var(--ink);text-decoration:none;min-width:0}
a.tb:hover{border-color:var(--ink2)}
.tb.side{background:transparent;border-style:dashed}
.tb.side .tg{background:transparent;color:var(--ink2);box-shadow:inset 0 0 0 1.5px var(--c)}
.tb .tg{min-width:54px;height:28px;font-size:14px;padding:0 6px;white-space:nowrap}
.tb-x{display:flex;flex-direction:column;min-width:0;line-height:1.3}
.tb-t{font-size:14px;font-weight:700;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.tb-m{font-size:12.5px;color:var(--ink2);white-space:nowrap}
.tbm-key{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 12px;font-size:13.5px;color:var(--ink2)}
.tbm-key b{color:var(--ink);font-weight:900}
.tbm-key span{display:inline-flex;align-items:center;gap:6px}
.tbm-key .tg.sm{min-width:24px;height:13px;padding:0}
td.sec.bmk::before{content:'';display:block;width:30px;height:9px;margin:0 auto 5px;background:var(--c);border-radius:0 0 5px 5px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.2)}
@media (min-width:1024px){
  .tbm-h{font-size:16px} .tb-t{font-size:15.5px} .tb-m{font-size:13.5px} .tb .tg{font-size:15px;height:30px;min-width:60px}
  .tbm-l{grid-template-columns:repeat(auto-fill,minmax(290px,1fr))} .tbm-key{font-size:14.5px}
}
@media (max-width:640px){ td.sec.bmk::before{width:24px;margin:0 0 4px} .tbm-l{grid-template-columns:1fr} }
/*tbm-end*/
'''

JS = r'''<script id="tbm-js">(function(){
  [].forEach.call(document.querySelectorAll('details.std'),function(d){
    var rows=d.querySelectorAll('table.mk tr');
    [].forEach.call(d.querySelectorAll('.tb[data-rows]'),function(a){
      var c=getComputedStyle(a).getPropertyValue('--c');
      a.dataset.rows.split(',').forEach(function(i){ var r=rows[+i], td=r&&r.querySelector('td.sec'); if(td&&!a.classList.contains('side')){ td.classList.add('bmk'); td.style.setProperty('--c',c); } });
    });
  });
  document.addEventListener('click',function(e){
    var a=e.target.closest('a.tb'); if(!a) return; e.preventDefault(); e.stopPropagation();
    var d=a.closest('details.std'), r=d.querySelectorAll('table.mk tr')[+a.dataset.rows.split(',')[0]]; if(!r) return;
    r.classList.remove('hide'); r.scrollIntoView({block:'center'}); r.classList.remove('flash'); void r.offsetWidth; r.classList.add('flash');
  },true);
})();
</script>'''


def main():
    data = json.loads((ROOT / 'top-bookmarks.json').read_text(encoding='utf-8'))
    p = ROOT / 'index.html'
    s = p.read_text(encoding='utf-8')
    # remove anything from a previous run
    s = re.sub(r'<div class="tbm none">.*?</div>\n', '', s, flags=re.S)
    s = re.sub(r'<div class="tbm"><b class="tbm-h">.*?</div></div>\n', '', s, flags=re.S)
    s = re.sub(r'<div class="tbm-key">.*?</div>\n', '', s, flags=re.S)
    s = re.sub(r'\n/\*tbm-start\*/.*?/\*tbm-end\*/\n', '', s, flags=re.S)
    s = re.sub(r'<script id="tbm-js">.*?</script>', '', s, flags=re.S)

    n = 0
    for std in data['standards']:
        m = re.search(r'<details class="std"[^>]*id="%s">.*?<div class="body">\n' % re.escape(std['sid']), s, re.S)
        assert m, std['sid']
        end = s.index('</details>', m.end())
        body = s[m.end():end]
        k = body.find('<p class="hot">')
        if k < 0: k = body.find('<table class="mk">')
        assert k >= 0, std['sid']
        s = s[:m.end()] + body[:k] + strip_html(std) + body[k:] + s[end:]
        n += 1
    assert n == 63, n

    key = '<div class="tbm-key"><b>צבע הסימנייה העליונה:</b>' + ''.join(
        '<span><i class="tg sm" style="--c:%s"></i>%s · %s</span>' % (c['hex'], c['name'], MEANING[k]) for k, c in data['colors'].items()) + '</div>\n'
    anchor = '<div class="bar" id="bar">'
    assert s.count(anchor) == 1
    s = s.replace(anchor, key + anchor)
    a = '\n@media print{'
    assert s.count(a) == 1
    s = s.replace(a, CSS + a)
    assert s.count('</body></html>') == 1
    s = s.replace('</body></html>', JS + '</body></html>')
    p.write_text(s, encoding='utf-8')
    print('strips:', n, '| top bookmarks:', sum(not b['side'] for x in data['standards'] for b in x['bookmarks']))


if __name__ == '__main__':
    main()
