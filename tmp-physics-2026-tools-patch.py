from pathlib import Path
import json, re

PKG = Path('ege-fizika-demoversiya-v3-1-fixed')
p = PKG / 'ege-fizika-demoversiya-T123-06.txt'
s = p.read_text(encoding='utf-8')

if 'function installExamTools()' not in s:
    marker = 'function installRuntimeStyles(){'
    assert marker in s
    tools = r'''var PHYSICS_SYMBOLS=["²","³","⁻¹","₀","₁","₂","₃","₄","₅","₆","₇","₈","₉","→","↑","↓","±","≈","√","π","α","β","γ","φ","ω","Δ","Σ","λ","μ","ν","ρ","ε","η","Ω","·","×","≤","≥","v⃗","a⃗","F⃗","p⃗","B⃗","E⃗"];
var calcLastAnswer=0;
function insertAtCursor(el,text){if(!el)return;var st=typeof el.selectionStart==="number"?el.selectionStart:el.value.length,en=typeof el.selectionEnd==="number"?el.selectionEnd:st;el.setRangeText(text,st,en,"end");el.dispatchEvent(new Event("input",{bubbles:true}));el.focus()}
function physicsSymbolKeyboardHtml(targetId){return '<div class="ephys-symbol-keyboard" data-target="'+escapeHtml(targetId)+'" aria-label="Клавиатура физических символов"><div class="ephys-symbol-keyboard__label">Физические знаки</div><div class="ephys-symbol-keyboard__keys">'+PHYSICS_SYMBOLS.map(function(x){return '<button type="button" class="ephys-symbol-key" data-symbol="'+escapeHtml(x)+'">'+escapeHtml(x)+'</button>'}).join("")+'</div></div>'}
function installSymbolKeyboards(container){container.querySelectorAll("textarea").forEach(function(el){if(!el.id||el.getAttribute("data-symbol-keyboard")==="true")return;el.setAttribute("data-symbol-keyboard","true");var h=document.createElement("div");h.innerHTML=physicsSymbolKeyboardHtml(el.id);var kb=h.firstElementChild;el.insertAdjacentElement("afterend",kb);kb.querySelectorAll("button[data-symbol]").forEach(function(b){b.addEventListener("click",function(){insertAtCursor(el,b.getAttribute("data-symbol"))})})})}
function calcTokenize(input){var s=String(input||"").replace(/,/g,".").replace(/π/g,"pi").replace(/×/g,"*").replace(/÷/g,"/").replace(/−/g,"-").replace(/\s+/g,"");var o=[],i=0;while(i<s.length){var r=s.slice(i),m;if((m=r.match(/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/))){o.push({t:"num",v:Number(m[0])});i+=m[0].length;continue}if((m=r.match(/^[A-Za-z]+/))){o.push({t:"id",v:m[0].toLowerCase()});i+=m[0].length;continue}var c=s[i];if("+-*/^()".indexOf(c)>=0){o.push({t:c,v:c});i++;continue}throw new Error("Недопустимый символ: "+c)}return o}
function calcEvaluate(input){var t=calcTokenize(input),p=0;function q(x){return t[p]&&t[p].t===x}function take(x){if(!q(x))throw new Error("Ожидается "+x);return t[p++]}function ex(){var v=te();while(q("+")||q("-")){var op=t[p++].t,r=te();v=op==="+"?v+r:v-r}return v}function te(){var v=po();while(q("*")||q("/")){var op=t[p++].t,r=po();if(op==="/"&&r===0)throw new Error("Деление на ноль");v=op==="*"?v*r:v/r}return v}function po(){var v=un();if(q("^")){p++;v=Math.pow(v,po())}return v}function un(){if(q("+")){p++;return un()}if(q("-")){p++;return-un()}return pr()}function pr(){if(q("num"))return take("num").v;if(q("(")){p++;var v=ex();take(")");return v}if(q("id")){var id=take("id").v;if(id==="pi")return Math.PI;if(id==="e")return Math.E;if(id==="ans")return calcLastAnswer;if(!q("("))throw new Error("После "+id+" нужны скобки");p++;var a=ex();take(")");if(id==="sin")return Math.sin(a*Math.PI/180);if(id==="cos")return Math.cos(a*Math.PI/180);if(id==="tan")return Math.tan(a*Math.PI/180);if(id==="sqrt")return Math.sqrt(a);if(id==="ln")return Math.log(a);if(id==="log")return Math.log10(a);if(id==="abs")return Math.abs(a);throw new Error("Неизвестная функция: "+id)}throw new Error("Неполное выражение")}var v=ex();if(p!==t.length)throw new Error("Проверьте выражение");if(!Number.isFinite(v))throw new Error("Результат не является конечным числом");return v}
function calculatorHtml(){var k=[['7','7'],['8','8'],['9','9'],['÷','/'],['√','sqrt('],['4','4'],['5','5'],['6','6'],['×','*'],['x²','^2'],['1','1'],['2','2'],['3','3'],['−','-'],['xʸ','^'],['0','0'],[',','.'],['(', '('],[')',')'],['+','+'],['sin','sin('],['cos','cos('],['tan','tan('],['π','pi'],['EXP','E'],['log','log('],['ln','ln('],['Ans','ans']];return '<div class="ephys-calculator"><p class="ephys-mini"><strong>Непрограммируемый мини-калькулятор.</strong> Тригонометрия — в градусах. Без CAS, формульного решателя и программирования.</p><label for="ephys-calc-expression">Выражение</label><input id="ephys-calc-expression" class="ephys-calc-display" autocomplete="off"><div class="ephys-calc-result" id="ephys-calc-result" aria-live="polite">0</div><div class="ephys-calc-grid"><button type="button" data-calc-action="clear">C</button><button type="button" data-calc-action="back">⌫</button>'+k.map(function(x){return '<button type="button" data-calc-insert="'+escapeHtml(x[1])+'">'+x[0]+'</button>'}).join("")+'<button type="button" data-calc-action="recip">1/x</button><button type="button" data-calc-action="sign">±</button><button type="button" class="ephys-calc-equals" data-calc-action="equals">=</button></div></div>'}
function bindCalculator(){var i=byId("ephys-calc-expression"),r=byId("ephys-calc-result");if(!i||!r)return;function eq(){try{var v=calcEvaluate(i.value);calcLastAnswer=v;r.textContent=Number(v.toPrecision(12)).toString();r.removeAttribute("data-error")}catch(e){r.textContent=e.message;r.setAttribute("data-error","true")}}document.querySelectorAll("#ephys-modal-body [data-calc-insert]").forEach(function(b){b.addEventListener("click",function(){insertAtCursor(i,b.getAttribute("data-calc-insert"))})});document.querySelectorAll("#ephys-modal-body [data-calc-action]").forEach(function(b){b.addEventListener("click",function(){var a=b.getAttribute("data-calc-action");if(a==="clear"){i.value="";r.textContent="0";r.removeAttribute("data-error");i.focus()}else if(a==="back"){var st=i.selectionStart||0,en=i.selectionEnd||st;if(st===en&&st>0)st--;i.setRangeText("",st,en,"end");i.focus()}else if(a==="recip"){i.value=i.value?'1/('+i.value+')':'1/(';i.focus()}else if(a==="sign"){i.value=i.value?'-('+i.value+')':'-';i.focus()}else if(a==="equals")eq()})});i.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();eq()}});i.focus()}
function openCalculator(){openModal("Калькулятор",calculatorHtml());bindCalculator()}
function installExamTools(){if(byId("ephys-tools-style"))return;var st=document.createElement("style");st.id="ephys-tools-style";st.textContent="#"+ROOT_ID+" .ephys-toolbar{grid-template-columns:auto 1fr auto auto auto}#"+ROOT_ID+" .ephys-symbol-keyboard{margin:10px 0 4px;padding:10px;border:1px solid #dfe4eb;border-radius:12px;background:#f8fafc}#"+ROOT_ID+" .ephys-symbol-keyboard__label{font-size:13px;font-weight:800;margin-bottom:8px}#"+ROOT_ID+" .ephys-symbol-keyboard__keys{display:flex;gap:6px;flex-wrap:wrap}#"+ROOT_ID+" .ephys-symbol-key{min-width:38px;min-height:36px;padding:6px 8px;border:1px solid #cdd4df;border-radius:9px;background:#fff;color:#17324d;font:inherit;font-weight:800;cursor:pointer}#"+ROOT_ID+" .ephys-symbol-key:hover{background:#eef4ff;border-color:#8aa6d8}#"+ROOT_ID+" .ephys-calculator{max-width:620px;margin:0 auto}#"+ROOT_ID+" .ephys-calc-display{width:100%;padding:14px;border:1px solid #cdd4df;border-radius:12px;font:600 18px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace}#"+ROOT_ID+" .ephys-calc-result{margin:10px 0 14px;padding:12px 14px;border-radius:10px;background:#f3f7ff;font:800 20px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}#"+ROOT_ID+" .ephys-calc-result[data-error=true]{background:#fff0f0;color:#8a2634}#"+ROOT_ID+" .ephys-calc-grid{display:grid;grid-template-columns:repeat(5,minmax(42px,1fr));gap:7px}#"+ROOT_ID+" .ephys-calc-grid button{min-height:44px;border:1px solid #cdd4df;border-radius:10px;background:#fff;color:#17324d;font:inherit;font-weight:800;cursor:pointer}#"+ROOT_ID+" .ephys-calc-grid button:hover{background:#f4f7fb}#"+ROOT_ID+" .ephys-calc-grid .ephys-calc-equals{background:#315fb5;color:#fff;border-color:#315fb5}@media(max-width:900px){#"+ROOT_ID+" .ephys-toolbar{grid-template-columns:1fr auto auto auto}#"+ROOT_ID+" .ephys-progress{grid-column:1/-1}}@media(max-width:560px){#"+ROOT_ID+" .ephys-toolbar{grid-template-columns:1fr 1fr}#"+ROOT_ID+" .ephys-toolbar .ephys-timer-wrap,#"+ROOT_ID+" .ephys-progress{grid-column:1/-1}#"+ROOT_ID+" .ephys-toolbar button{width:100%}#"+ROOT_ID+" .ephys-symbol-keyboard__keys{flex-wrap:nowrap;overflow-x:auto;padding-bottom:4px}}";document.head.appendChild(st);var f=byId("ephys-finish-top"),ref=byId("ephys-reference");if(f&&ref&&!byId("ephys-calculator")){var b=document.createElement("button");b.className="ep-button ep-button--small ep-button--secondary";b.id="ephys-calculator";b.type="button";b.textContent="Калькулятор";b.addEventListener("click",openCalculator);f.parentNode.insertBefore(b,f)}}
'''
    s = s.replace(marker, tools + marker, 1)
    old = 'bindZoom(stage);updateNav();updateValidation(t,getAnswer(t.number));'
    assert old in s
    s = s.replace(old, 'installSymbolKeyboards(stage);bindZoom(stage);updateNav();updateValidation(t,getAnswer(t.number));', 1)
    old = 'installRuntimeStyles();applyResultSemantics();'
    assert old in s
    s = s.replace(old, 'installRuntimeStyles();installExamTools();applyResultSemantics();', 1)
    p.write_text(s, encoding='utf-8')

contract = {
    'source_year': 2026,
    'status': 'IMPLEMENTED_PENDING_BROWSER_GATE',
    'symbol_keyboard': {
        'targets': ['extended answer textarea', 'draft textarea'],
        'required_capabilities': ['square/superscript', 'vector notation', 'subscripts/indices', 'common physics and math symbols'],
        'does_not_solve': True
    },
    'calculator': {
        'type': 'non-programmable mini scientific calculator',
        'operations': ['arithmetic', 'parentheses', 'powers', 'sqrt', 'reciprocal', 'scientific notation', 'sin/cos/tan in degrees', 'log10', 'ln', 'pi', 'e', 'Ans'],
        'forbidden': ['CAS', 'equation solver', 'formula solver', 'programming', 'symbolic algebra'],
        'fipi_alignment': 'official 2026 instruction permits ruler and non-programmable calculator'
    },
    'storage_contract': 'unchanged'
}
(PKG / 'PHYSICS-2026-EXAM-TOOLS-CONTRACT.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Export runtime JS for node --check in the workflow.
m = re.search(r'<script>(.*)</script>\s*$', p.read_text(encoding='utf-8'), re.S)
assert m
Path('/tmp/physics-runtime-with-tools.js').write_text(m.group(1), encoding='utf-8')
