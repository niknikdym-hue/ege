#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'templates'/'runtime.js'
s=p.read_text(encoding='utf-8')
old="if(v.table&&v.control!=='row_checkboxes')out+=tableHtml(v.table,false,null);if(v.continuation_html)"
new="if(v.table)out+=tableHtml(v.table,v.control==='row_checkboxes',answerObj(state.current));if(v.continuation_html)"
if old not in s: raise SystemExit('body table target not found')
s=s.replace(old,new,1)
old2="function rowPanel(v){const a=answerObj(state.current)||{selected:[]};return `<div class=\"mb-answerbox\"><div class=\"mb-answer-title\">Выберите строки таблицы</div><div class=\"mb-answer-hint\">Отметьте подходящие номера. Итоговый код соберётся автоматически.</div>${tableHtml(v.table,true,a)}<div class=\"mb-code\" id=\"mb-code\">Код для бланка: ${esc(canonicalCode(v,a)||'—')}</div><button class=\"mb-btn mb-btn--secondary\" type=\"button\" id=\"mb-clear\">Сбросить ответ</button></div>`}"
new2="function rowPanel(v){const a=answerObj(state.current)||{selected:[]};return `<div class=\"mb-answerbox\"><div class=\"mb-answer-title\">Ответ</div><div class=\"mb-answer-hint\">Отметьте подходящие номера непосредственно в таблице выше. Итоговый код соберётся автоматически.</div><div class=\"mb-code\" id=\"mb-code\">Код для бланка: ${esc(canonicalCode(v,a)||'—')}</div><button class=\"mb-btn mb-btn--secondary\" type=\"button\" id=\"mb-clear\">Сбросить ответ</button></div>`}"
if old2 not in s: raise SystemExit('row panel target not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('row checkbox table now renders at official table position')
