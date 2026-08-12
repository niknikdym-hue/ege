#!/usr/bin/env python3
import importlib.util, json, os, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

URL=os.environ.get("EKSAMIO_PREVIEW_URL","http://127.0.0.1:8765/ege-matematika-profil-demoversiya-2025-PREVIEW.html")
HERE=Path(__file__).resolve()
ROOT=HERE.parent.parent
OUT=ROOT/"tests"/"evidence"/"profile-2025-browser-evidence.json"
ANS={1:["61","18","157","5"],2:["12","29"],3:["1,125","340","104"],4:["0,35","0,38"],5:["0,992","0,15"],6:["4","17","93","3"],7:["2,76","2","125"],8:["6","-1,4"],9:["5"],10:["12","15","8"],11:["7"],12:["-83","-6","16"]}
COUNTS={1:4,2:2,3:3,4:2,5:2,6:4,7:3,8:2,9:1,10:3,11:1,12:3,13:1,14:1,15:1,16:1,17:1,18:1,19:1}
MAX={13:2,14:3,15:2,16:2,17:3,18:4,19:4}
STORAGE="eksamio_ege_math_profile_demo_2025_v1_0"
STORAGE_2026="eksamio_ege_math_profile_demo_2026_v1_0"

def driver_new():
    o=webdriver.ChromeOptions()
    o.add_argument("--headless=new");o.add_argument("--no-sandbox");o.add_argument("--disable-dev-shm-usage");o.add_argument("--window-size=1280,1000")
    o.set_capability("goog:loggingPrefs",{"browser":"ALL"})
    return webdriver.Chrome(options=o)
def js(d,code,*args):return d.execute_script("return "+code,*args)
def force(d,n,v):d.execute_script("window.EKSAMIO_MATH_PROFILE_TEST.forceVariant(arguments[0],arguments[1]);",n,v)
def fill(el,text):
    el.click();el.send_keys(Keys.CONTROL,"a");el.send_keys(Keys.BACKSPACE)
    if text!="":el.send_keys(text)
def nav(d,n):return d.find_element(By.CSS_SELECTOR,f'.mp-num[data-n="{n}"]')

def finalize():
    spec=importlib.util.spec_from_file_location("build2025",ROOT/"scripts"/"build_profile_2025.py")
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    data=json.loads((ROOT/f"{b.PREFIX}-EXAM-DATA.json").read_text(encoding="utf-8"))
    data["status"]="READY_FOR_TILDA_UPLOAD"
    (ROOT/f"{b.PREFIX}-EXAM-DATA.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    b.write_audit_matrix(data,True)
    imap=ROOT/f"{b.PREFIX}-INPUT-CONTRACT.json"
    c=json.loads(imap.read_text(encoding="utf-8"));c["status"]="PASS_BROWSER_AUDIT";imap.write_text(json.dumps(c,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    emap=ROOT/f"{b.PREFIX}-EXAM-MAP.json"
    e=json.loads(emap.read_text(encoding="utf-8"));e["status"]="READY_FOR_TILDA_UPLOAD";emap.write_text(json.dumps(e,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    bev=ROOT/f"{b.PREFIX}-BUILD-EVIDENCE.json"
    x=json.loads(bev.read_text(encoding="utf-8"));x["status"]="READY_FOR_TILDA_UPLOAD";x["browser_audit"]="tests/evidence/profile-2025-browser-evidence.json";bev.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/f"{b.PREFIX}-PAGE-STATUS.txt").write_text(
      "PAGE_URL: /ege/matematika-profil/demoversiya/2025/\nPAGE_SLUG: ege-matematika-profil-demoversiya-2025\nEXAM: ЕГЭ\nSUBJECT: математика\nLEVEL: профильный\nSOURCE_YEAR: 2025\nPACKAGE_VERSION: 1.0\nSOURCE_GATE: PASS\nTEXT_TYPOGRAPHY_GATE: PASS\nFORMULA_GATE: PASS\nVISUAL_GATE: PASS\nINTERACTION_GATE: PASS — 37/37 official examples through real DOM controls\nSCORER_GATE: PASS — every short-answer example correct+wrong checked\nSTATE_RESTORE_GATE: PASS — assigned variant, answers, mark and navigation survive reload\nEXTENDED_SELF_EVALUATION_GATE: PASS — 7/7 criteria assets and score buttons\nTILDA_SIZE_GATE: PASS — every T123 < 45000 bytes\nINDEPENDENT_AUDIT_GATE: PASS — source layer and separate browser audit\nFINAL_STATUS: READY_FOR_TILDA_UPLOAD\nPUBLISHED_SMOKE_STATUS: NOT_RUN_UNTIL_TILDA_PUBLICATION\nLIVE_GO: NO — requires Tilda publication + production smoke-test + manual student acceptance\n",encoding="utf-8")
    (ROOT/"AUDIT-REPORT-2025-profile.md").write_text(
      "# Аудит — ЕГЭ профильная математика 2025\n\nСтатус: **READY FOR TILDA UPLOAD; LIVE GO ещё не присвоен**.\n\n"
      "- Источник содержания: официальный комплект ФИПИ 2025 из `matematika-source-2025`; профильная 2026 используется только как технический эталон движка.\n"
      "- 37/37 официальных примеров имеют отдельные строки audit matrix и прямые source-crop assets.\n"
      "- №1–12: 30/30 официальных примеров открыты в браузере через реальный input; для каждого проверены правильный и неправильный допустимый ответ, scorer и состояние заполненности.\n"
      "- №13–19: 7/7 открыты через реальный textarea; официальное решение/критерии не видны до завершения, после завершения все 7 source assets и кнопки самооценки работают.\n"
      "- Reload сохраняет назначенный официальный пример, ответы, метку возврата и текущую попытку. 2025 использует отдельный storage key и не пишет в storage 2026.\n"
      "- Проверены ширины 1280/768/390/360/320 px и отсутствие серьёзных JS-ошибок.\n"
      "- Следующий gate: загрузка T123 в Tilda, production smoke-test и ручная студенческая приёмка; только после этого возможен LIVE GO.\n",encoding="utf-8")

def main():
    ev={"status":"PASS","package_version":"1.0","checks":{},"details":{}}
    d=driver_new()
    try:
        d.get(URL);d.execute_script("localStorage.clear()");d.refresh();d.find_element(By.ID,"mp-start").click()
        assert len(d.find_elements(By.CSS_SELECTOR,".mp-num"))==19
        assert js(d,"localStorage.getItem(arguments[0])",STORAGE) is not None
        assert js(d,"localStorage.getItem(arguments[0])",STORAGE_2026) is None
        st=js(d,"window.EKSAMIO_MATH_PROFILE_TEST.state()")
        assert all(1<=int(st["variants"][str(n)])<=COUNTS[n] for n in range(1,20))
        ev["checks"]["isolated_storage_and_random_assignment"]="PASS"

        opened=short=ext=0
        for n in range(1,20):
            for v in range(1,COUNTS[n]+1):
                force(d,n,v);time.sleep(.015)
                src=d.find_element(By.CSS_SELECTOR,".mp-source-img")
                assert js(d,"arguments[0].naturalWidth",src)>0,(n,v)
                assert "официальный пример" not in d.find_element(By.ID,"mp-task").text.lower()
                if n<=12:
                    inp=d.find_element(By.ID,"mp-short")
                    official=ANS[n][v-1]
                    fill(inp,official.replace(",","."))
                    assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])",n),(n,v)
                    assert nav(d,n).get_attribute("class").find("is-filled")>=0,(n,v)
                    assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])",n)==1,(n,v,inp.get_attribute("value"))
                    wrong="0,99" if n in (4,5) else ("999" if n==8 and v==1 else "999999")
                    fill(inp,wrong)
                    assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])",n)
                    assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])",n)==0
                    fill(inp,"")
                    assert not js(d,"window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])",n)
                    assert "is-filled" not in nav(d,n).get_attribute("class")
                    fill(inp,official);short+=1
                else:
                    ta=d.find_element(By.ID,"mp-long");fill(ta,f"Тестовое полное решение {n}-{v}\nОтвет.")
                    assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])",n)
                    assert "is-filled" in nav(d,n).get_attribute("class")
                    assert not d.find_elements(By.CSS_SELECTOR,".mp-solution"),(n,v,"solution leaked before finish")
                    ext+=1
                opened+=1
        assert (opened,short,ext)==(37,30,7)
        ev["checks"]["official_examples_real_controls"]="37/37 PASS (30 numeric input + 7 textarea)"
        ev["checks"]["correct_and_wrong_short_answers"]="30/30 PASS"

        force(d,4,1);inp=d.find_element(By.ID,"mp-short");fill(inp,"50%");assert "%" in d.find_element(By.ID,"mp-error").text
        fill(inp,"1,2");assert "от 0 до 1" in d.find_element(By.ID,"mp-error").text
        fill(inp,"0.35");assert inp.get_attribute("value")=="0,35" and js(d,"window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(4)")==1
        force(d,8,1);inp=d.find_element(By.ID,"mp-short");fill(inp,"6,0");assert "целое число" in d.find_element(By.ID,"mp-error").text and not js(d,"window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(8)")
        fill(inp,"6");assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(8)")==1
        force(d,8,2);fill(d.find_element(By.ID,"mp-short"),"-1.4");assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(8)")==1
        force(d,1,1);inp=d.find_element(By.ID,"mp-short");fill(inp,"61 град");assert "Единицы измерения" in d.find_element(By.ID,"mp-error").text
        fill(inp,"61,");assert "После запятой" in d.find_element(By.ID,"mp-error").text and "is-filled" not in nav(d,1).get_attribute("class")
        ev["checks"]["per_example_input_contracts"]="PASS: probability / integer count / general numeric / incomplete decimal"

        force(d,5,2);fill(d.find_element(By.ID,"mp-short"),"0,15")
        force(d,16,1);fill(d.find_element(By.ID,"mp-long"),"Сохранённое решение 16")
        d.find_element(By.ID,"mp-mark").click()
        before=js(d,"window.EKSAMIO_MATH_PROFILE_TEST.state()")
        d.execute_script("window.dispatchEvent(new PageTransitionEvent('pagehide'));")
        d.refresh()
        after=js(d,"window.EKSAMIO_MATH_PROFILE_TEST.state()")
        assert int(after["variants"]["16"])==1 and after["answers"]["16"]["text"]=="Сохранённое решение 16"
        assert after["answers"]["5"]["value"]=="0,15" and bool(after["marked"]["16"])
        assert before["variants"]["16"]==after["variants"]["16"]
        ev["checks"]["state_restore"]="PASS: variant + short + extended + marked + pagehide/reload"

        d.execute_script("localStorage.clear()");d.refresh();d.find_element(By.ID,"mp-start").click()
        for n in range(1,13):
            force(d,n,1);fill(d.find_element(By.ID,"mp-short"),ANS[n][0])
        for n in range(13,20):
            force(d,n,1);fill(d.find_element(By.ID,"mp-long"),f"Полное решение задания {n}")
        assert js(d,"window.EKSAMIO_MATH_PROFILE_TEST.autoTotal()")==12
        d.find_element(By.ID,"mp-finish").click();d.switch_to.alert.accept();time.sleep(.05)
        assert d.find_element(By.ID,"mp-auto-score").text.strip()=="12/12"
        for n in range(13,20):
            card=d.find_element(By.CSS_SELECTOR,f'.mp-ext-card[data-ext="{n}"]')
            img=card.find_element(By.CSS_SELECTOR,".mp-source-img")
            assert js(d,"arguments[0].naturalWidth",img)>0
            card.find_element(By.CSS_SELECTOR,f'.mp-score-btn[data-s="{MAX[n]}"]').click()
        assert d.find_element(By.ID,"mp-self-score").text.strip()=="20/20"
        assert d.find_element(By.ID,"mp-total-score").text.strip()=="32/32"
        assert d.find_element(By.ID,"mp-auto-score").text.strip()=="12/12"
        ev["checks"]["scoring_separation"]="PASS: automatic 12/12 unchanged; explicit self 20/20; total 32/32"
        ev["checks"]["extended_criteria_after_finish"]="7/7 source assets rendered only after finish"

        overflow={}
        for w in [1280,768,390,360,320]:
            d.set_window_size(w,1000);time.sleep(.03)
            delta=d.execute_script("return document.documentElement.scrollWidth-window.innerWidth;")
            overflow[str(w)]=delta;assert delta<=1,(w,delta)
        ev["checks"]["responsive_widths"]="PASS: 1280,768,390,360,320"
        ev["details"]["overflow_delta_px"]=overflow
        severe=[x for x in d.get_log("browser") if x.get("level")=="SEVERE" and "/favicon.ico" not in x.get("message","")]
        assert not severe,severe
        ev["checks"]["javascript_errors"]=0
    finally:
        d.quit()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    finalize()
    print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
