"""Apply the frozen v3 classifier to disputed texts; no fitting or accuracy claim."""
from pathlib import Path
import sys,json,hashlib,platform
import numpy as np
import pandas as pd
import joblib,sklearn,jieba
import train_model as tm

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/uncertain_probe';OUT.mkdir(exist_ok=True)
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[ROOT/'output/v3/model.joblib',ROOT/'data/v3/sentences_all.csv',ROOT/'data/v3/dataset_v3.csv',ROOT/'output/v3/test_predictions.csv',ROOT/'output/v3/independent_predictions.csv']
before={str(p.relative_to(ROOT)):hashfile(p) for p in inputs}
bundle=joblib.load(inputs[0]);vec=bundle['vectorizer'];model=bundle['model']
assert not bundle['config']['use_stopwords']
assert list(model.classes_)==[0,1]
for word in bundle['config']['jieba_user_words']:jieba.add_word(word)
allrows=pd.read_csv(inputs[1]).fillna('');main=pd.read_csv(inputs[2])
probe=allrows[allrows.work_id.isin(['W17','W18','U01'])].copy().reset_index(drop=True)
assert len(probe)==59 and not set(probe.sent_id)&set(main.sent_id)

def apply(df):
    seg=tm.segment(df.text_normalized)
    x=vec.transform(seg)
    return x,model.predict(x),model.predict_proba(x),seg

verification={}
for name,path in [('test',inputs[3]),('chaoyi',inputs[4])]:
    expected=pd.read_csv(path)
    x,p,prob,_=apply(expected)
    match=[tm.LABEL_NAMES[int(v)] for v in p]==list(expected.period_pred)
    diff=float(np.max(abs(prob[:,1]-expected.prob_east.values)))
    assert match and diff<1e-10,(name,match,diff)
    verification[name]={'sentences':len(p),'all_saved_predictions_reproduced':match,'maximum_probability_difference':diff}

x,p,prob,seg=apply(probe)
analyzer=vec.build_analyzer();features=vec.get_feature_names_out();coef=model.coef_[0]
train=main[main.split=='train'];traintexts=set(train.text_normalized)
rows=[]
for i,row in probe.iterrows():
    xx=x.getrow(i);contrib=xx.data*coef[xx.indices]
    order=np.argsort(abs(contrib))[::-1][:8]
    toks=analyzer(seg[i]);covered=sum(t in vec.vocabulary_ for t in toks)
    rows.append({'sent_id':row.sent_id,'work_id':row.work_id,'work_title':row.work_title,'text_original':row.text_original,'text_normalized':row.text_normalized,'period_pred':tm.LABEL_NAMES[int(p[i])],'prob_west':float(prob[i,0]),'prob_east':float(prob[i,1]),'active_features':int(xx.nnz),'token_occurrences':len(toks),'covered_token_occurrences':covered,'vocabulary_coverage':covered/len(toks) if toks else 0,'original_include_full':str(row.include_full),'original_exclusion_reason':row.exclusion_reason,'exact_text_in_main_train':row.text_normalized in traintexts,'signed_word_contributions':json.dumps([{'word':str(features[xx.indices[j]]),'towards_east':float(contrib[j])} for j in order],ensure_ascii=False)})
pred=pd.DataFrame(rows);pred.to_csv(OUT/'predictions.csv',index=False,encoding='utf-8-sig')
summaries=[]
for wid,g in pred.groupby('work_id',sort=False):
    eligible=g[g.original_include_full.str.lower()=='true']
    for scope,subset in [('保存的全部句',g),('沿用原清理條件的句',eligible)]:
        summaries.append({'work_id':wid,'title':g.work_title.iloc[0],'scope':scope,'n':len(subset),'west':int((subset.period_pred=='西漢').sum()),'east':int((subset.period_pred=='東漢').sum()),'mean_prob_east':float(subset.prob_east.mean()) if len(subset) else None,'min_prob_east':float(subset.prob_east.min()) if len(subset) else None,'max_prob_east':float(subset.prob_east.max()) if len(subset) else None,'zero_feature_sentences':int((subset.active_features==0).sum()),'exact_training_text_matches':int(subset.exact_text_in_main_train.sum())})
pd.DataFrame(summaries).to_csv(OUT/'summary.csv',index=False,encoding='utf-8-sig')
assert all(hashfile(ROOT/n)==h for n,h in before.items())
payload={'model':'output/v3/model.joblib','mode':'inference_only_no_refit','serialized_sklearn_version':'1.9.1','runtime_version_check':'compare runtime sklearn version with serialized version; validate saved controls before use','gold_labels':'unknown; no accuracy or F1 computed','source_hashes':before,'runtime':{'python':platform.python_version(),'sklearn':sklearn.__version__,'jieba':jieba.__version__},'controls':verification,'summaries':summaries,'all_inputs_unchanged':True}
(OUT/'verification.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
lines=['# 疑難文本探測：固定模型的應用與限制','','本次只載入已保存的 v3 主模型，沿用其分詞詞表及 TF-IDF 轉換；不重新訓練、不增加標籤、不調整門檻。三篇共59句均未進入主樣本。已先重現233句正式測試及129句〈超奇〉的全部既有預測，機率最大差異低於1e-10。','','## 判別結果','','|篇目|統計範圍|句數|判西漢|判東漢|平均東漢模型分數|零特徵句|與訓練句全文相同|','|---|---|---:|---:|---:|---:|---:|---:|']
for r in summaries:lines.append(f"|{r['title']}|{r['scope']}|{r['n']}|{r['west']}|{r['east']}|{r['mean_prob_east']:.3f}|{r['zero_feature_sentences']}|{r['exact_training_text_matches']}|")
lines+=['','模型分數是二分類器的輸出，未經斷代機率校準；平均分數只是句分數的描述性摘要，不是整篇屬於某年代的機率。原清理條件只沿用 include_full 欄，沒有把 trainable 改成真。全部句結果保留供回查，正文宜以清理後結果為主。','','## 可檢驗與不可檢驗的問題','','1. 可觀察這些文本在固定兩漢分類器中的判別傾向、句間差異、詞彙覆蓋及具體詞語貢獻。低覆蓋或零特徵結果須結合模型截距解讀。','2. 兩篇舊題劉向書錄可與底本的疑偽按語對讀，但「疑宋人依託」是文獻線索，不作已確定的宋代真值。若仍多判西漢，不能據此恢復其西漢真實年代；模型可能識別到校書敘錄的用語。','3. 《毛詩序》不設本次考據真值；分布只能供選句回讀，不能把東漢票數當作衛宏作者歸屬證據。','4. 目前模型只可選西漢或東漢，沒有其他時期或拒判機制；無論分數高低，均不具直接辨偽能力。','5. 準確率及跨作者判別能力仍以已有確定標籤的測試與留出作者實驗檢驗。這三篇不計入準確率、F1或模型改進幅度。','','## 待回讀例句（依篇內西漢分數最高、東漢分數最高各取一句；非代表性抽樣）','']
for wid,g in pred.groupby('work_id',sort=False):
    for idx in dict.fromkeys([g.prob_east.idxmin(),g.prob_east.idxmax()]):
        rr=pred.loc[idx];lines += [f"- {rr.sent_id}：{rr.text_original}",f"  判{rr.period_pred}；東漢模型分數 {rr.prob_east:.3f}；有效特徵 {rr.active_features} 項；原清理保留={rr.original_include_full}。"]
(OUT/'findings.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps(summaries,ensure_ascii=False,indent=2))
