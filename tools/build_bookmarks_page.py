"""Build bookmarks.html: a "sticking checklist" for the top bookmarks (one self-contained static file).
Reads top-bookmarks.json, combined-standards.json and the side-bookmark colour of each standard in index.html.
Safe to re-run (it just overwrites bookmarks.html).

    python tools/build_bookmarks_page.py           (run from the MARKER_GUIDE folder)
"""
import html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_top_bookmarks import MEANING, text_on  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VOLS = [('א', "כרך א' · תקני ביקורת"), ('ב', "כרך ב' · התנהגות מקצועית, תקנות ומדריכים")]


def esc(t):
    return html.escape(t, quote=True)


def write_html(w):
    if not w:
        return '—'
    return '<span>%s</span>' % '–'.join('<bdi>%s</bdi>' % esc(t) for t in w.split('–'))


def side_info(index_html, sid):
    """(side colour, text colour, number, short title) of a standard, from index.html."""
    m = re.search(r'<details class="std"[^>]*id="%s">\s*<summary><span class="no tg" style="--c:(#[0-9A-Fa-f]{6});'
                  r'--tc:(#[0-9A-Fa-f]{6})"[^>]*>(.*?)</span>' % re.escape(sid), index_html, re.S)
    assert m, sid
    n = re.search(r'<a class="nl" href="#%s"[^>]*><span class="tg"[^>]*>.*?</span><span class="t">(.*?)</span>' % re.escape(sid), index_html, re.S)
    return m.group(1), m.group(2), html.unescape(m.group(3)).strip(), html.unescape(n.group(1)).strip() if n else None


CSS = r'''
:root{--paper:#FCFBF8;--ink:#111820;--ink2:#434E59;--line:#D9D5CA;--card:#FFFFFF;--soft:#F3F1EA;--ok:#2E9E1F;--hh:150px}
*{box-sizing:border-box}
html{scroll-padding-top:calc(var(--hh) + 8px);-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:#000;font-family:'Heebo','Segoe UI','Arial Hebrew',Arial,sans-serif;font-size:15.5px;line-height:1.45}
a{color:inherit}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
header.top{position:sticky;top:0;z-index:20;background:var(--paper);border-bottom:1px solid var(--line);padding:8px 0 9px;box-shadow:0 2px 8px rgba(17,24,32,.06)}
.h1row{display:flex;flex-wrap:wrap;align-items:center;gap:4px 14px}
h1{margin:0;font-size:19px;font-weight:900;flex:none}
.back{font-size:14px;font-weight:700;color:var(--ink2);text-decoration:none;padding:3px 0}
.back:hover{text-decoration:underline;color:#000}
.cnt{display:flex;align-items:center;gap:10px;margin-inline-start:auto;min-width:0}
.cnt b{font-size:15px;font-weight:900;white-space:nowrap;font-variant-numeric:tabular-nums}
.pb{width:130px;height:7px;border-radius:99px;background:var(--soft);box-shadow:inset 0 0 0 1px var(--line);overflow:hidden;flex:none}
.pb i{display:block;height:100%;width:0;background:var(--ok);border-radius:99px;transition:width .2s}
.rst{font:inherit;font-size:12.5px;font-weight:700;padding:3px 10px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink2);cursor:pointer}
.rst:hover{border-color:var(--ink2);color:#000}
.flt{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;margin-top:8px}
.tgl{font:inherit;font-size:14px;font-weight:700;padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.tgl:hover{border-color:var(--ink2)}
.tgl[aria-pressed=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.cbs{display:flex;gap:6px;align-items:center;margin:0 6px}
.cbtn{width:28px;height:28px;padding:0;border-radius:50%;border:2px solid rgba(0,0,0,.2);background:var(--c);cursor:pointer;flex:none}
.cbtn[aria-pressed=true]{border-color:var(--ink);box-shadow:0 0 0 2px #fff inset}
.sep{width:1px;height:20px;background:var(--line);margin:0 2px}
.shown{font-size:13.5px;color:var(--ink2);margin-inline-start:auto;white-space:nowrap}
main{padding-bottom:60px}
details.key{margin:14px 0 4px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:0 14px}
details.key summary{cursor:pointer;font-weight:900;font-size:16px;padding:10px 0}
.keyl{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:6px 18px;padding:2px 0 8px;font-size:14.5px}
.keyl span{display:flex;align-items:center;gap:8px}
.keyl i{display:inline-block;width:28px;height:14px;border-radius:2px 5px 5px 2px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.16);flex:none}
.keyn{margin:0 0 12px;color:var(--ink2);font-size:14.5px}
h2{font-size:21px;font-weight:900;margin:26px 0 6px}
.std{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:12px 0;overflow:hidden;scroll-margin-top:calc(var(--hh) + 8px)}
.std.all{opacity:.72}
.sh{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:10px 14px;border-bottom:1px solid var(--line);background:var(--soft)}
.tg{display:inline-grid;place-items:center;min-width:52px;height:30px;padding:0 8px;border-radius:2px 7px 7px 2px;background:var(--c);color:var(--tc);font-weight:900;font-size:15px;font-variant-numeric:tabular-nums;line-height:1;box-shadow:inset 0 0 0 1px rgba(0,0,0,.16);flex:none}
.sh .tg{font-size:17px}
.sh h3{margin:0;font-size:15.5px;font-weight:700;flex:1 1 180px;min-width:0}
.sc{font-weight:900;font-size:15px;color:var(--ink2);font-variant-numeric:tabular-nums;white-space:nowrap}
.std.all .sc{color:var(--ok);font-size:20px;line-height:1}
.gl{font-size:13px;color:var(--ink2);text-decoration:none;white-space:nowrap}
.gl:hover{text-decoration:underline;color:#000}
.row{display:grid;grid-template-columns:22px minmax(0,1fr);gap:2px 12px;align-items:center;padding:9px 14px;border-top:1px solid var(--line);cursor:pointer;background:var(--card)}
.sh+.row{border-top:0}
.row:hover{background:#FAF9F4}
.row input{width:22px;height:22px;margin:0;accent-color:#2E9E1F;cursor:pointer;grid-row:1/3;align-self:center}
.row .tg{justify-self:start;max-width:100%;min-width:64px;white-space:nowrap}
.top1{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;min-width:0}
.lb{font-size:15.5px;color:#000;min-width:0}
.mt{font-size:13.5px;color:var(--ink2)}
.mt .n{font-weight:700}
.row.note .top1{font-size:15.5px}
.row.note b{font-weight:900;color:#000}
.pen{color:var(--ink2)}
.row.done{background:#F4FAEF}
.row.done .top1,.row.done .mt{opacity:.6}
.sideonly{margin:10px 2px 0;font-size:14px;color:var(--ink2)}
.sideonly b{color:#000;font-weight:900}
.hide{display:none!important}
.empty{margin:30px 0;text-align:center;color:var(--ink2)}
@media (max-width:640px){
  .row .top1{grid-column:2;flex-wrap:nowrap;align-items:flex-start}
  .row.note .top1{flex-wrap:wrap}
  .row .lb{flex:1 1 0}
  .row .mt{grid-column:2}
}
@media (min-width:641px){
  .row{grid-template-columns:22px minmax(0,1fr) auto}
  .row input{grid-row:auto}
  .top1{flex-wrap:nowrap}
  .row .tg{width:128px;flex:none}
  .lb{flex:1}
  .mt{white-space:nowrap;text-align:end}
  .row.note .top1{flex-wrap:wrap}
}
@media (max-width:640px){
  body{font-size:15.5px}
  .wrap{padding:0 12px}
  header.top{padding:6px 0 7px}
  h1{font-size:16.5px}
  .back{font-size:13px}
  .cnt{width:100%;margin:0}
  .pb{flex:1;width:auto}
  .cnt b{font-size:14px}
  .flt{margin-top:6px;gap:5px 6px}
  .tgl{font-size:13px;padding:3px 9px}
  .cbs{gap:4px;margin:0 2px}
  .cbtn{width:24px;height:24px}
  .shown{margin:0;width:100%;font-size:12.5px;white-space:normal}
  .sh{padding:9px 12px}
  .sh h3{font-size:15.5px}
  .row{padding:9px 12px}
  .lb{font-size:15.5px}
  .mt{font-size:13.5px}
  h2{font-size:18px}
  .keyl{grid-template-columns:1fr}
}
@media (min-width:1024px){
  body{font-size:17px}
  h1{font-size:22px}
  .sh h3{font-size:17.5px;font-weight:700}
  .sh h3{font-weight:700}
  .sh .tg{font-size:17px}
  .tg{font-size:16px}
  .lb,.row.note .top1{font-size:17px}
  .mt,.sc,.gl{font-size:15px}
  .row{padding:10px 16px}
  .sh{padding:11px 16px}
}
/* the tag keeps its natural size inside a fixed column, so the descriptions line up */
@media (min-width:641px){
  .row .top1{display:grid;grid-template-columns:150px minmax(0,1fr);gap:14px}
  .row .tg{width:auto;justify-self:start}
  .row.note .top1{display:flex}
  .mt{min-width:230px}
}
.mt .n{font-weight:900;color:#000}
@media (min-width:1500px){
  .wrap{max-width:1420px;padding:0 24px}
  .lb,.row.note .top1{font-size:18.5px}
  .mt,.sc,.gl{font-size:16.5px}
  .tg{font-size:17px;height:32px}
  .sh h3{font-size:19px}
  .sh .tg{font-size:18.5px;height:34px;min-width:60px}
  .row{padding:12px 20px}
  .sh{padding:13px 20px}
  .row .top1{grid-template-columns:175px minmax(0,1fr);gap:18px}
  .row input{width:24px;height:24px}
  .mt{min-width:270px}
  h1{font-size:25px}
}
/* phone: the header scrolls away; only the progress counter stays, as a bar at the bottom */
@media (max-width:640px){
  header.top{position:static;box-shadow:none}
  .cnt{position:fixed;bottom:10px;left:10px;right:10px;width:auto;z-index:20;margin:0;padding:8px 12px;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 4px 16px rgba(17,24,32,.18)}
  body{padding-bottom:70px}
  html{scroll-padding-top:12px}
  .std{scroll-margin-top:12px}
}
'''

JS = r'''(function(){
  var KEY='mg-bm-v1', state={};
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
  function load(){ state={}; try{ var v=JSON.parse(localStorage.getItem(KEY)||'{}'); if(v&&typeof v==='object'&&!Array.isArray(v)) state=v; }catch(e){} }
  function save(){ try{ localStorage.setItem(KEY,JSON.stringify(state)); }catch(e){} }
  var rows=$$('.row'), cards=$$('.std'), vols=$$('.vol'), total=rows.length;
  var f={vol:'',color:'',rest:false};
  function applyState(){ rows.forEach(function(r){ var on=!!state[r.dataset.id]; r.querySelector('input').checked=on; r.classList.toggle('done',on); }); }
  function counters(){
    var done=0;
    cards.forEach(function(c){
      var rs=$$('.row',c), d=rs.filter(function(r){return r.classList.contains('done')}).length; done+=d;
      $('.sc',c).textContent = d===rs.length ? '✓' : d+'/'+rs.length;
      c.classList.toggle('all',d===rs.length);
    });
    $('#cnt').textContent='הודבקו '+done+' מתוך '+total;
    var pb=$('#pb'); pb.firstElementChild.style.width=(total?100*done/total:0)+'%'; pb.setAttribute('aria-valuenow',done);
  }
  function filter(){
    var shown=0;
    rows.forEach(function(r){
      var c=r.closest('.std'), ok=(!f.vol||c.dataset.vol===f.vol)&&(!f.color||r.dataset.color===f.color)&&(!f.rest||!r.classList.contains('done'));
      r.classList.toggle('hide',!ok); if(ok) shown++;
    });
    cards.forEach(function(c){ c.classList.toggle('hide',!$('.row:not(.hide)',c)); });
    vols.forEach(function(v){
      var any=!!$('.std:not(.hide)',v), so=$('.sideonly',v);
      v.classList.toggle('hide',!any);
      if(so) so.classList.toggle('hide',!!f.color||!!f.rest||(!!f.vol&&f.vol!==v.dataset.vol));
    });
    $('#shown').textContent='מוצגות '+shown+' שורות';
    $('#empty').classList.toggle('hide',shown>0);
  }
  function refresh(){ counters(); filter(); }
  document.addEventListener('change',function(e){
    var i=e.target; if(!i.matches||!i.matches('.row input')) return;
    var r=i.closest('.row'); if(i.checked) state[r.dataset.id]=1; else delete state[r.dataset.id];
    r.classList.toggle('done',i.checked); save(); refresh();
  });
  function toggleBtn(btn,key,val){
    var on=btn.getAttribute('aria-pressed')==='true';
    $$('[data-f="'+key+'"]').forEach(function(b){ b.setAttribute('aria-pressed','false'); });
    if(!on) btn.setAttribute('aria-pressed','true');
    f[key]=on?'':val; filter();
  }
  $$('[data-f="vol"]').forEach(function(b){ b.addEventListener('click',function(){ toggleBtn(b,'vol',b.dataset.v); }); });
  $$('[data-f="color"]').forEach(function(b){ b.addEventListener('click',function(){ toggleBtn(b,'color',b.dataset.v); }); });
  $('#rest').addEventListener('click',function(){ var b=this, on=b.getAttribute('aria-pressed')==='true'; b.setAttribute('aria-pressed',on?'false':'true'); f.rest=!on; filter(); });
  $('#reset').addEventListener('click',function(){
    if(!confirm('למחוק את כל הסימונים בדף הזה?')) return;
    state={}; save(); applyState(); refresh();
  });
  window.addEventListener('storage',function(e){ if(e.key===KEY){ load(); applyState(); refresh(); } });
  function setHH(){ document.documentElement.style.setProperty('--hh',$('header.top').offsetHeight+'px'); }
  function goHash(){
    var id=''; try{ id=decodeURIComponent(location.hash.slice(1)); }catch(e){ id=location.hash.slice(1); }
    var el=id&&document.getElementById(id); if(el&&el.classList.contains('std')){ if(el.classList.contains('hide')) return; el.scrollIntoView(); }
  }
  load(); applyState(); refresh(); setHH();
  window.addEventListener('resize',setHH);
  if(window.ResizeObserver) new ResizeObserver(setHH).observe($('header.top'));
  window.addEventListener('hashchange',goHash);
  goHash();
  window.addEventListener('load',function(){ setHH(); goHash(); });
})();'''


def main():
    data = json.loads((ROOT / 'top-bookmarks.json').read_text(encoding='utf-8'))
    notes = {n['sid']: n for n in json.loads((ROOT / 'combined-standards.json').read_text(encoding='utf-8'))}
    index_html = (ROOT / 'index.html').read_text(encoding='utf-8')
    colors = data['colors']
    font_link = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?family=Heebo[^>]*>', index_html).group(0)

    ids, side_only = set(), {v: [] for v, _ in VOLS}
    parts = {v: [] for v, _ in VOLS}
    n_bm = n_note = n_cards = 0

    def add_id(i):
        assert i not in ids, 'duplicate row id: ' + i
        ids.add(i)
        return i

    for std in data['standards']:
        sid, vol = std['sid'], std['vol']
        assert vol in parts, vol
        sc, stc, no, short = side_info(index_html, sid)
        note = notes.get(sid)
        if not std['bookmarks'] and not note:
            side_only[vol].append((no, short or std['title']))
            continue
        title = short or std['title']
        rows = []
        if note:
            rid = add_id('%s|note' % sid)
            rows.append('<label class="row note" data-id="%s" data-color=""><input type="checkbox">'
                        '<span class="top1"><span class="pen">&#9998; לכתוב ליד כותרת התקן:</span> <b>%s</b></span></label>'
                        % (esc(rid), esc(note['write'])))
            n_note += 1
        for b in std['bookmarks']:
            rid = add_id('%s|%s|%s' % (sid, b['write'], b['page']))
            meta = []
            if b['page'] is not None:
                meta.append("עמ' <span class=\"n\">%d</span>" % b['page'])
            meta.append('מסלול <span class="n">%d</span>' % b['lane'])
            if b['count']:
                meta.append('×%d' % b['count'])
            rows.append('<label class="row" data-id="%s" data-color="%s"><input type="checkbox">'
                        '<span class="top1"><span class="tg" style="--c:%s;--tc:%s" title="%s">%s</span><span class="lb">%s</span></span>'
                        '<span class="mt">%s</span></label>'
                        % (esc(rid), esc(b['color']), b['hex'], text_on(b['hex']),
                           esc('סימנייה %s · %s' % (b['color_name'], MEANING[b['color']])),
                           write_html(b['write']), esc(b['label']), ' · '.join(meta)))
            n_bm += 1
        parts[vol].append(
            '<section class="std" id="%s" data-vol="%s"><div class="sh"><span class="tg" style="--c:%s;--tc:%s">%s</span>'
            '<h3 title="%s">%s</h3><span class="sc"></span><a class="gl" href="./#%s">לתקן במפרט</a></div>\n%s\n</section>\n'
            % (esc(sid), esc(vol), sc, stc, esc(no), esc(std['title']), esc(title), esc(sid), '\n'.join(rows)))
        n_cards += 1

    body = []
    for v, heading in VOLS:
        so = ''
        if side_only[v]:
            so = '<p class="sideonly"><b>סימניית צד בלבד:</b> %s</p>' % ' · '.join(
                '<b>%s</b> %s' % (esc(n), esc(t)) for n, t in side_only[v])
        body.append('<div class="vol" data-vol="%s"><h2>%s</h2>\n%s%s</div>' % (esc(v), esc(heading), ''.join(parts[v]), so))

    cbtns = ''.join('<button type="button" class="cbtn" data-f="color" data-v="%s" style="--c:%s" aria-pressed="false" '
                    'title="%s" aria-label="%s"></button>'
                    % (k, c['hex'], esc('%s · %s' % (c['name'], MEANING[k])), esc('%s · %s' % (c['name'], MEANING[k])))
                    for k, c in colors.items())
    keyl = ''.join('<span style="--c:%s"><i></i>%s · %s</span>' % (c['hex'], esc(c['name']), esc(MEANING[k])) for k, c in colors.items())
    total = n_bm + n_note

    page = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>רשימת הדבקה – סימניות</title>
%(font)s
<style>%(css)s</style>
</head>
<body>
<header class="top"><div class="wrap">
<div class="h1row"><h1>רשימת הדבקה לסימניות</h1><a class="back" href="./">&rarr; למפרט המרקרים</a>
<div class="cnt"><b id="cnt">הודבקו 0 מתוך %(total)d</b><div class="pb" id="pb" role="progressbar" aria-valuemin="0" aria-valuemax="%(total)d" aria-valuenow="0" aria-label="התקדמות"><i></i></div><button type="button" class="rst" id="reset">איפוס</button></div></div>
<div class="flt"><button type="button" class="tgl" data-f="vol" data-v="א" aria-pressed="false">כרך א'</button><button type="button" class="tgl" data-f="vol" data-v="ב" aria-pressed="false">כרך ב'</button><span class="sep"></span>
<span class="cbs">%(cbtns)s</span><span class="sep"></span><button type="button" class="tgl" id="rest" aria-pressed="false">רק מה שנשאר</button>
<span class="shown" id="shown" aria-live="polite"></span></div>
</div></header>
<main class="wrap">
<details class="key"><summary>מקרא הצבעים</summary><div class="keyl">%(keyl)s</div>
<p class="keyn">כותבים רק את מספר הסעיף, או נ ומספר הנספח · המסלול (1–8) הוא המיקום בקצה העליון של הדף, מימין לשמאל</p></details>
%(body)s
<p class="empty hide" id="empty">אין שורות שמתאימות למסננים שנבחרו.</p>
</main>
<script>%(js)s</script>
</body>
</html>
''' % dict(font=font_link, css=CSS, total=total, cbtns=cbtns, keyl=keyl, body='\n'.join(body), js=JS)

    (ROOT / 'bookmarks.html').write_text(page, encoding='utf-8', newline='\n')

    # --- checks ---
    assert n_bm == sum(len(s['bookmarks']) for s in data['standards']) == 126, n_bm
    assert n_note == len(notes) == 13, n_note
    assert page.count('<input type="checkbox">') == total == 139
    assert len(ids) == 139
    assert page.count('<section class="std"') == n_cards
    side_n = sum(len(x) for x in side_only.values())
    assert n_cards + side_n == len(data['standards']) == 63
    print('rows: %d bookmarks + %d notes = %d | cards: %d | side-only: %d | ids unique: %s'
          % (n_bm, n_note, total, n_cards, side_n, len(ids) == total))


if __name__ == '__main__':
    main()
