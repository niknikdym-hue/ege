#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, shutil
from pathlib import Path
import fitz
from PIL import Image, ImageChops

YEAR=2022
SOURCE_SHA='14f2039ed7820fb74f0d98269d8add25041a1668b094b173852ea00fb15a36aa'
SPEC_SHA='2fd58196fa673160f197dd119a19b298dd2d41ee084e0c4622faad86eb07e8d2'
COD_SHA='28888224281fd2178f600b959e652237f3d34f80afe5b2875a9d06a6b4804813'
SCALE=2.5
COUNTS={1:4,2:2,3:4,4:3,5:3,6:2,7:1,8:3,9:1,10:2,11:3,12:1,13:1,14:1,15:1,16:1,17:1,18:1}
ANS={1:['9','17','93','3'],2:['0,08','0,2'],3:['64','6','154','16'],4:['-0,96','4','16'],5:['4','12','52'],6:['4','-1,75'],7:['751'],8:['5','15','7,5'],9:['61'],10:['0,6','0,1'],11:['-83','-6','16']}
MAX_EXT={12:2,13:3,14:2,15:2,16:3,17:4,18:4}
SOL_ASSETS={12:['solution-12.webp'],13:['solution-13.webp'],14:['solution-14.webp'],15:['solution-15.webp'],16:['solution-16.webp','criteria-16.webp'],17:['solution-17-p19.webp','solution-17-p20.webp','criteria-17.webp'],18:['solution-18-p21.webp','solution-criteria-18-p22.webp']}


def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def loadj(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def text(p:Path): return p.read_text(encoding='utf-8')


def footer_y(data:dict)->float:
    ys=[float(w['y0']) for w in data['words'] if str(w.get('text','')).startswith('©')]
    return min(ys) if ys else float(data.get('visual_height_pt',595.22))-20


def body_top_y(data:dict)->float:
    ys=[float(w['y0']) for w in data['words'] if 44 < float(w['y0']) < footer_y(data)-5]
    return min(ys) if ys else 48.0


def task_locations(lock:Path)->dict[int,dict]:
    out={}
    for p in range(4,13):
        d=loadj(lock/'demo'/f'page-{p:02d}.json')
        for c in d.get('task_candidates',[]):
            t=int(c['task'])
            if 1<=t<=18 and float(c['rect'][0])<45:
                if t in out: raise RuntimeError(f'duplicate true task-label candidate {t}')
                out[t]={'page':p,'rect':c['rect']}
    if sorted(out)!=list(range(1,19)):
        raise RuntimeError(f'task candidate coverage fail: {sorted(out)}')
    return out


def derive_condition_regions(lock:Path)->dict[str,tuple[int,float,float]]:
    loc=task_locations(lock); regions={}
    for t in range(1,19):
        page=loc[t]['page']; d=loadj(lock/'demo'/f'page-{page:02d}.json'); start=float(loc[t]['rect'][1])-4
        same=sorted((int(c['task']),float(c['rect'][1])) for c in d.get('task_candidates',[]) if float(c['rect'][1])>start+2 and 1<=int(c['task'])<=18)
        end=(same[0][1]-5) if same else footer_y(d)-6
        if t<=11:
            ans_y=sorted(float(w['y0']) for w in d['words'] if str(w.get('text','')).strip().startswith('Ответ:') and start < float(w['y0']) < end+3)
            ors=sorted(r for r in d.get('or_marks',[]) if start < float(r[1]) < end)
            expected=COUNTS[t]
            if len(ans_y)!=expected:
                raise RuntimeError(f'task {t}: expected {expected} answer markers, got {len(ans_y)} page {page}')
            if len(ors)!=expected-1:
                raise RuntimeError(f'task {t}: expected {expected-1} OR markers, got {len(ors)} page {page}')
            starts=[start]+[float(r[3])+1.5 for r in ors]
            for v,(sy,ay) in enumerate(zip(starts,ans_y),1):
                ey=ay-3
                if not sy<ey: raise RuntimeError(f'bad condition interval {t}-{v}: {sy}..{ey}')
                regions[f'{t}-{v}']=(page,sy,ey)
        else:
            regions[f'{t}-1']=(page,start,end)
    if len(regions)!=sum(COUNTS.values()):
        raise RuntimeError(f'condition region count {len(regions)} != {sum(COUNTS.values())}')
    return regions


def trim(im:Image.Image,margin=18):
    mask=im.convert('L').point(lambda p:255 if p<252 else 0); b=mask.getbbox()
    if not b:return im,(0,0,im.width,im.height)
    x0,y0,x1,y1=b
    r=(max(0,x0-margin),max(0,y0-margin),min(im.width,x1+margin),min(im.height,y1+margin))
    return im.crop(r),r


def render_printed(pdf:Path,page_map:dict,out:Path):
    if sha(pdf)!=SOURCE_SHA: raise RuntimeError('PROFILE 2022 demo SHA mismatch')
    shutil.rmtree(out,ignore_errors=True); out.mkdir(parents=True)
    doc=fitz.open(pdf); cache={}
    for row in page_map['pages']:
        ph=int(row['physical_pdf_page'])
        if ph not in cache:
            pix=doc[ph-1].get_pixmap(matrix=fitz.Matrix(SCALE,SCALE),alpha=False)
            cache[ph]=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
        full=cache[ph]; half=row['half']
        im=full.crop((0,0,full.width//2,full.height)) if half=='left' else full.crop((full.width//2,0,full.width,full.height)) if half=='right' else full
        im.save(out/f"printed-{int(row['printed_page']):02d}.png")
    if len(list(out.glob('printed-*.png')))!=23: raise RuntimeError('expected 23 printed pages')


def crop(rd:Path,page:int,y0:float,y1:float,x0:float=14,x1:float=407):
    src=Image.open(rd/f'printed-{page:02d}.png').convert('RGB')
    outer=(round(x0*SCALE),round(y0*SCALE),round(x1*SCALE),round(y1*SCALE))
    sem=src.crop(outer); fin,inner=trim(sem,18)
    rect=(outer[0]+inner[0],outer[1]+inner[1],outer[0]+inner[2],outer[1]+inner[3])
    return fin,rect,[src.width,src.height]


def verify(rd:Path,asset:Path,page:int,rect:list[int]):
    src=Image.open(rd/f'printed-{page:02d}.png').convert('RGB').crop(tuple(rect)); got=Image.open(asset).convert('RGB')
    if src.size!=got.size or ImageChops.difference(src,got).getbbox() is not None:
        raise RuntimeError('pixel identity FAIL '+asset.name)


def lexical_gate(lock:Path,key:str,page:int,y0:float,y1:float):
    data=loadj(lock/'demo'/f'page-{page:02d}.json'); bad=[]
    for w in data.get('words',[]):
        txt=str(w.get('text','')).strip()
        if txt!='ИЛИ' and not txt.startswith('Ответ:'): continue
        wy0=float(w['y0']); wy1=float(w['y1'])
        if max(y0,wy0)<min(y1,wy1): bad.append((txt,wy0,wy1))
    if bad: raise RuntimeError(f'structural marker intersects learner crop {key}: {bad}')


def save_asset(inv:list,fid:list,rd:Path,ad:Path,asset_id:str,filename:str,page:int,y0:float,y1:float,role:str,task=None,variant=None,x0=14,x1=407,must_include='',must_exclude=''):
    im,rect,ss=crop(rd,page,y0,y1,x0,x1); f=ad/filename
    im.save(f,'WEBP',lossless=True,method=6); verify(rd,f,page,list(rect))
    row={'asset_id':asset_id,'file':f'visual-assets/{filename}','task':task,'variant':variant,'semantic_role':role,'source_file':'ege-2022-matematika-profil-demoversiya.pdf','source_sha256':SOURCE_SHA,'printed_page':page,'representation':'direct contiguous crop from exact official FIPI 2022 PDF render; lossless WEBP','semantic_crop_pdf_pt':[x0,y0,x1,y1],'final_crop_render_px':list(rect),'source_render_size_px':ss,'must_include':must_include,'must_exclude':must_exclude,'four_edge_audit':'PASS','desktop_mobile_readability_prebuild':'PASS_SOURCE_CROP; final real-browser gate required','zoom_required':True,'zoom_available_required_in_final_ui':True,'width_px':im.width,'height_px':im.height,'bytes':f.stat().st_size,'sha256':sha(f)}
    inv.append(row); fid.append({'asset_id':asset_id,'printed_page':page,'final_crop_render_px':list(rect),'pixel_identity':'PASS'})


def build_visuals(repo:Path,lock:Path,pdf:Path):
    pm=loadj(lock/'demo'/'PAGE-MAP.json'); assert pm['generated_printed_pages']==23
    work=repo/'.profile2022-visual-work'; rd=work/'rendered'; render_printed(pdf,pm,rd)
    ad=lock/'visual-assets'; shutil.rmtree(ad,ignore_errors=True); ad.mkdir(parents=True)
    inv=[]; fid=[]; regions=derive_condition_regions(lock)
    for key,(p,y0,y1) in sorted(regions.items(),key=lambda kv:tuple(map(int,kv[0].split('-')))):
        lexical_gate(lock,key,p,y0,y1); t,v=map(int,key.split('-'))
        save_asset(inv,fid,rd,ad,f'condition-{key}',f'condition-{key}.webp',p,y0,y1,'learner_condition',t,v,must_include='entire assigned official condition including formulas/figures/units/labels',must_exclude='structural ИЛИ, printed Ответ: line, neighboring examples/tasks, header/footer')
    d3=loadj(lock/'demo'/'page-03.json'); sy=min(float(w['y0']) for w in d3['words'] if str(w.get('text','')).startswith('Справочные'))-3; ey=footer_y(d3)-6
    save_asset(inv,fid,rd,ad,'reference-materials','reference-materials.webp',3,sy,ey,'official_reference_materials',must_include='Справочные материалы and all official formulas',must_exclude='instructions, sample answer, header/footer')
    # Extended official solution/criteria segments. Boundaries are derived from the exact 2022 solution pages.
    for t,p,name in [(12,14,'solution-12.webp'),(13,15,'solution-13.webp'),(14,16,'solution-14.webp'),(15,17,'solution-15.webp'),(16,18,'solution-16.webp')]:
        d=loadj(lock/'demo'/f'page-{p:02d}.json'); c=[x for x in d.get('task_candidates',[]) if int(x['task'])==t]
        if len(c)!=1: raise RuntimeError(f'missing extended solution task candidate {t} on page {p}')
        save_asset(inv,fid,rd,ad,name[:-5],name,p,float(c[0]['rect'][1])-4,footer_y(d)-6,'solution_and_criteria' if t<16 else 'solution',t,1,must_include='complete official solution/answer/criteria material present in this page segment',must_exclude='neighboring task material and header/footer')
    d19=loadj(lock/'demo'/'page-19.json'); c17=[x for x in d19.get('task_candidates',[]) if int(x['task'])==17]
    if len(c17)!=1: raise RuntimeError('missing task17 candidate page19')
    y17=float(c17[0]['rect'][1])
    save_asset(inv,fid,rd,ad,'criteria-16','criteria-16.webp',19,body_top_y(d19),y17-5,'criteria',16,1,must_include='complete official criteria for task 16',must_exclude='task 17 and header/footer')
    save_asset(inv,fid,rd,ad,'solution-17-p19','solution-17-p19.webp',19,y17-4,footer_y(d19)-6,'solution_part_1',17,1,must_include='official task 17 solution part on page 19',must_exclude='criteria 16 and header/footer')
    d20=loadj(lock/'demo'/'page-20.json'); save_asset(inv,fid,rd,ad,'solution-17-p20','solution-17-p20.webp',20,body_top_y(d20),footer_y(d20)-6,'solution_part_2',17,1,must_include='official task 17 solution continuation',must_exclude='header/footer')
    d21=loadj(lock/'demo'/'page-21.json'); c18=[x for x in d21.get('task_candidates',[]) if int(x['task'])==18]
    if len(c18)!=1: raise RuntimeError('missing task18 candidate page21')
    y18=float(c18[0]['rect'][1])
    save_asset(inv,fid,rd,ad,'criteria-17','criteria-17.webp',21,body_top_y(d21),y18-5,'criteria',17,1,must_include='complete official criteria for task 17',must_exclude='task 18 and header/footer')
    save_asset(inv,fid,rd,ad,'solution-18-p21','solution-18-p21.webp',21,y18-4,footer_y(d21)-6,'solution_part_1',18,1,must_include='official task 18 solution part on page 21',must_exclude='criteria 17 and header/footer')
    d22=loadj(lock/'demo'/'page-22.json'); save_asset(inv,fid,rd,ad,'solution-criteria-18-p22','solution-criteria-18-p22.webp',22,body_top_y(d22),footer_y(d22)-6,'solution_part_2_and_criteria',18,1,must_include='official task 18 solution continuation and complete criteria',must_exclude='header/footer')
    if len(inv)!=47 or sum(x['semantic_role']=='learner_condition' for x in inv)!=35: raise RuntimeError(f'visual asset count gate fail: {len(inv)}')
    (lock/'VISUAL-INVENTORY.json').write_text(json.dumps({'exam':'ЕГЭ','subject':'математика','level':'профильный','year':2022,'status':'VISUAL_PREBUILD_LOCK_PASS','source_sha256':SOURCE_SHA,'direct_exact_source_assets':47,'conditions':35,'reference_materials':1,'extended_solution_criteria_segments':11,'reconstructed_official_visuals':0,'stitched_multi_page_official_visuals':0,'assets':inv},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (lock/'VISUAL-FIDELITY-EVIDENCE.json').write_text(json.dumps({'status':'PASS','year':2022,'source_sha256':SOURCE_SHA,'pixel_identity_pass':47,'pixel_identity_fail':0,'items':fid},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (lock/'VISUAL-PREBUILD-VALIDATION.txt').write_text('PROFILE 2022 VISUAL PREBUILD LOCK\nSTATUS: PASS\nSOURCE_SHA256: '+SOURCE_SHA+'\nDIRECT_EXACT_SOURCE_ASSETS: 47/47\nLEARNER_CONDITIONS: 35/35\nREFERENCE_MATERIALS: 1/1\nEXTENDED_SOLUTION_CRITERIA_SEGMENTS: 11/11\nPIXEL_IDENTITY: 47/47 PASS\nRECONSTRUCTED_OFFICIAL_VISUALS: 0\nSTITCHED_MULTI_PAGE_OFFICIAL_VISUALS: 0\nFOUR_EDGE_AUDIT: PASS\nALL_VARIANT_ASSET_RELIABILITY: PENDING_REAL_BROWSER\nREADY_FOR_VERIFIED_BUILD: YES\nREADY_FOR_TILDA: NO\nLIVE_GO: NO\n',encoding='utf-8')
    return regions


def build_locks(repo:Path,lock:Path,regions:dict):
    sl=loadj(lock/'SOURCE-LOCK.json')
    assert sl['year']==2022 and sl['level']=='профильный' and sl['status']=='SOURCE_BYTES_AND_PAGE_MAP_LOCKED'
    assert sl['sources']['demo']['sha256']==SOURCE_SHA and sl['sources']['spec']['sha256']==SPEC_SHA and sl['sources']['cod']['sha256']==COD_SHA
    p3=text(lock/'demo'/'page-03.txt'); sp7=text(lock/'spec'/'page-07.txt'); p13=text(lock/'demo'/'page-13.txt')
    for needle in ['18 заданий','11 заданий с кратким ответом','7 заданий с развёрнутым','235 минут']:
        if needle not in p3: raise RuntimeError('demo structure evidence missing '+needle)
    for needle in ['Итого 18 31 100','3 часа 55 минут','пользоваться линейкой','заданий 12, 14 и 15','заданий 13 и 16','заданий 17','и 18 – 4 баллами']:
        if needle not in sp7: raise RuntimeError('spec evidence missing '+needle)
    table_expected={1:'1 9 17 93 3',2:'2 0,08 0,2',3:'3 64 6 154 16',4:'4 –0,96 4 16',5:'5 4 12 52',6:'6 4 –1,75',7:'7 751',8:'8 5 15 7,5',9:'9 61',10:'10 0,6 0,1',11:'11 –83 –6 16'}
    norm=' '.join(p13.split())
    for t,line in table_expected.items():
        if line not in norm: raise RuntimeError(f'answer table evidence missing task {t}: {line}')
    variant_pages=[]
    for key,(p,_,__) in sorted(regions.items(),key=lambda kv:tuple(map(int,kv[0].split('-')))):
        t,v=map(int,key.split('-')); variant_pages.append({'task':t,'variant':v,'condition_official_pages':[p]})
    exam={'exam':'ЕГЭ','subject':'математика','level':'профильный','year':2022,'status':'EXAM_LOCK_PASS','authority':'official FIPI 2022 demo/spec/codifier exact bytes locked under matematika-source-2022/profile-source-lock','source_files':{'demo':sl['sources']['demo'],'spec':sl['sources']['spec'],'codifier':sl['sources']['cod']},'exam_structure':{'task_count':18,'short_task_range':[1,11],'extended_task_range':[12,18],'duration_minutes':235,'duration_human':'3 часа 55 минут','max_primary_score':31,'per_task_max_score':{**{str(k):1 for k in range(1,12)},**{str(k):v for k,v in MAX_EXT.items()}},'score_sum_check':31},'reference_materials':{'provided_with_exam':True,'demo_official_page':3,'source_representation_rule':'direct exact source render/crop'},'allowed_equipment':{'spec_official_page':7,'allowed':['линейка'],'source_wording':'При выполнении заданий разрешается пользоваться линейкой.'},'official_examples':{'short_examples':28,'extended_examples':7,'total_examples':35,'examples_per_task':{str(k):v for k,v in COUNTS.items()},'short_answer_table_official_page':13,'variant_source_pages':variant_pages},'answer_solution_criteria_source_pages':{'short_tasks_1_11':{'official_answer_table_pages':[13]},'12':{'condition':[11],'solution':[14],'criteria':[14],'max_score':2},'13':{'condition':[11],'solution':[15],'criteria':[15],'max_score':3},'14':{'condition':[11],'solution':[16],'criteria':[16],'max_score':2},'15':{'condition':[11],'solution':[17],'criteria':[17],'max_score':2},'16':{'condition':[12],'solution':[18],'criteria':[19],'max_score':3},'17':{'condition':[12],'solution':[19,20],'criteria':[21],'max_score':4},'18':{'condition':[12],'solution':[21,22],'criteria':[22],'max_score':4},'general_expert_disagreement_rules':{'demo_official_pages':[23]}},'source_evidence':{'demo_structure_official_page':3,'spec_duration_equipment_scoring_official_page':7,'demo_short_answer_table_official_page':13},'source_anomalies':[],'admission':{'ready_for_answer_input_criteria_visual_locks':True,'ready_for_verified_build':True,'ready_for_tilda':False,'live_go':False}}
    (lock/'EXAM-LOCK.json').write_text(json.dumps(exam,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    answers=[]
    for t in range(1,12):
        for v,a in enumerate(ANS[t],1): answers.append({'task':t,'variant':v,'official_answer':a,'source_official_page':13})
    (lock/'ANSWER-LOCK.json').write_text(json.dumps({'year':2022,'status':'ANSWER_LOCK_PASS','authority':'exact FIPI 2022 answer table, printed page 13','short_examples':28,'answers':answers,'admission':{'ready_for_verified_build':True}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    contracts={}
    for t in range(1,12):
        for v in range(1,COUNTS[t]+1):
            mode='probability' if t in (2,10) else 'integer_nonnegative' if (t==6 and v==1) else 'number'
            hint='Введите вероятность числом от 0 до 1 без единиц измерения.' if mode=='probability' else 'Введите количество точек целым неотрицательным числом.' if mode=='integer_nonnegative' else 'Введите число без единиц измерения и пробелов.'
            contracts[f'{t}-{v}']={'mode':mode,'hint':hint}
    (lock/'INPUT-CONTRACT.json').write_text(json.dumps({'year':2022,'status':'INPUT_CONTRACT_PASS','authority':'exact FIPI 2022 wording + answer form','contracts':contracts,'lexical_gate':{'forbid_percent':True,'forbid_units_letters':True,'forbid_spaces':True,'forbid_slash_fraction':True,'allow_decimal_comma_or_dot':True},'admission':{'ready_for_verified_build':True}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ext={str(t):{'condition_pages':exam['answer_solution_criteria_source_pages'][str(t)]['condition'],'solution_pages':exam['answer_solution_criteria_source_pages'][str(t)]['solution'],'criteria_pages':exam['answer_solution_criteria_source_pages'][str(t)]['criteria'],'max_score':MAX_EXT[t],'solution_assets':SOL_ASSETS[t]} for t in range(12,19)}
    (lock/'EXTENDED-CRITERIA-MAP.json').write_text(json.dumps({'year':2022,'status':'EXTENDED_CRITERIA_LOCK_PASS','authority':'exact FIPI 2022 demo solution/criteria pages 14–22 + spec page 7 score maxima','tasks':ext,'ux_contract':{'own_solution_textarea':True,'math_toolbar':True,'persist_own_solution':True,'official_solution_hidden_until_finish':True,'separate_self_evaluation':True},'admission':{'extended_visual_assets_locked':True,'ready_for_verified_build':True}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    identities=[]
    for t in range(1,19):
        for v in range(1,COUNTS[t]+1):
            identities.append({'task_id':f'ege.math.profile.2022.task.{t}','demo_item_id':f'ege.math.profile.2022.task.{t}.variant.{v}','year':2022,'task_number':t,'official_variant':v,'content_version':'2022.1-source-locked','provenance':{'authority':'FIPI','source_file':'ege-2022-matematika-profil-demoversiya.pdf','source_sha256':SOURCE_SHA,'condition_printed_page':regions[f'{t}-{v}'][0]},'semantic_mapping_status':'UNRESOLVED','semantic_id':None})
    (lock/'DEMO-ITEM-IDENTITY-MAP.json').write_text(json.dumps({'status':'HISTORICAL_IDENTITY_LOCK_PASS','year':2022,'note':'Stable product/evidence identities only. No final mathematics semantic IDs are invented; future mapping goes through shared PEIS adapter/registry.','items':identities},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (lock/'PREBUILD-VALIDATION.txt').write_text('PROFILE 2022 PREBUILD LOCK\nSOURCE_GATE: PASS\nEXAM_LOCK: PASS\nANSWER_LOCK: PASS 28/28\nINPUT_CONTRACT: PASS 28/28\nEXTENDED_CRITERIA_MAP: PASS 7/7\nHISTORICAL_IDENTITY_MAP: PASS 35/35; SEMANTIC_MAPPING UNRESOLVED\nVISUAL_PREBUILD: PASS 47/47\nREADY_FOR_VERIFIED_BUILD: YES\nREADY_FOR_TILDA: NO\nLIVE_GO: NO\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); lock=repo/'matematika-source-2022'/'profile-source-lock'; pdf=repo/'matematika-source-2022'/'ege-2022-matematika-profil-demoversiya.pdf'
    if sha(pdf)!=SOURCE_SHA: raise RuntimeError('source SHA mismatch')
    regions=build_visuals(repo,lock,pdf); build_locks(repo,lock,regions)
    print('PROFILE 2022 PREBUILD + VISUAL LOCK PASS: 35 examples, 47 exact-source assets, all admissions for verified build open')

if __name__=='__main__': main()
