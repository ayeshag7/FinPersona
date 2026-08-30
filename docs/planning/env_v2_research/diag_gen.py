import numpy as np, pandas as pd, sys
sys.path.insert(0,'.')
from envs.synthetic_market import SyntheticMarketEnv
from scipy import stats
def acf(x,k): x=np.asarray(x); x=x-x.mean(); return np.corrcoef(x[:-k],x[k:])[0,1]
def summarize(scn, **kw):
    rows=[]
    for seed in range(20):
        e=SyntheticMarketEnv(scenario=scn,n_days=200,seed=seed,**kw); d=e.data
        p=d.price.values; v=d.fundamental_value.values
        r=np.diff(np.log(p)); rv=np.diff(np.log(v))
        mdd=(p/np.maximum.accumulate(p)-1).min()
        rows.append(dict(seed=seed,final_ret=p[-1]/p[0]-1,mdd=mdd,daily_sd=r.std(),ann_sd=r.std()*np.sqrt(252),
            kurt=stats.kurtosis(r),acf1=acf(r,1),acf1_abs=acf(np.abs(r),1),acf5_abs=acf(np.abs(r),5),
            val_sd=rv.std(),pv_min=(p/v).min(),pv_max=(p/v).max(),pv_end=(p/v)[-1],
            pv_acf1=acf(p/v,1),
            vol_absr_corr=np.corrcoef(np.abs(r),d.volume.values[1:])[0,1],
            sent_acf1=acf(d.news_sentiment.values,1),
            sent_ret_corr=np.corrcoef(d.news_sentiment.values[1:],r)[0,1],
            iv_mean=d.implied_volatility.mean(),iv_max=d.implied_volatility.max(),
            pe_min=d.reported_PE.min(),pe_max=d.reported_PE.max(),dy_mean=d.dividend_yield.mean(),
            pe_over_15_eq_pv=np.allclose(d.reported_PE.values, 15*p/v, atol=1e-6) ))
    df=pd.DataFrame(rows); print(scn,kw); print(df.drop(columns='seed').agg(['mean','min','max']).round(3).T.to_string()); print()
summarize('flat'); summarize('bull_trap')
for dlt in [0.85,0.92,0.95]: summarize('crash',crash_discount=dlt)
