import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

def generate_ott_churn(n=6000):
    plans = rng.choice(['Basic','Standard','Premium'], size=n, p=[0.4,0.4,0.2])
    ad_supported = rng.choice([0,1], size=n, p=[0.6,0.4])
    tenure_months = rng.integers(1, 48, size=n)
    weekly_watch_hrs = np.round(rng.gamma(shape=2.2, scale=1.9, size=n), 2)
    rewatch_rate = np.round(rng.uniform(0, 0.6, size=n), 2)
    originals_share = np.round(rng.uniform(0, 1.0, size=n), 2)
    promo_exposures = rng.integers(0, 10, size=n)
    price_sensitivity = np.round(rng.uniform(0, 1.0, size=n), 2)
    concurrent_streams = np.where(plans=='Premium', 4, np.where(plans=='Standard', 2, 1))

    z = (
        -0.02*tenure_months
        -0.28*weekly_watch_hrs
        -0.75*rewatch_rate
        -0.55*originals_share
        -0.12*promo_exposures
        +0.72*price_sensitivity
        +0.2*(plans=='Basic').astype(int)
        +0.12*ad_supported
        -0.05*concurrent_streams
        + rng.normal(0, 0.7, size=n)
    )
    prob = 1/(1+np.exp(-z))
    churned = (prob>0.5).astype(int)

    df = pd.DataFrame({
        'plan': plans, 'ad_supported': ad_supported, 'tenure_months': tenure_months,
        'weekly_watch_hrs': weekly_watch_hrs, 'rewatch_rate': rewatch_rate,
        'originals_share': originals_share, 'promo_exposures': promo_exposures,
        'price_sensitivity': price_sensitivity, 'concurrent_streams': concurrent_streams,
        'churned': churned
    })
    return df

if __name__ == "__main__":
    df = generate_ott_churn(7000)
    df.to_csv("data/ott_churn.csv", index=False)
    print("Wrote data/ott_churn.csv with", len(df), "rows.")
