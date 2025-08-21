import os, time
import pandas as pd
import plotly.express as px
import requests
from dotenv import load_dotenv

load_dotenv("config/.env")

TMDB_KEY = os.getenv("TMDB_API_KEY")
OMDB_KEY = os.getenv("OMDB_API_KEY")

import streamlit as st
st.set_page_config(page_title="WBD Content Intelligence", layout="wide")
st.title("WBD Content Intelligence Dashboard")

st.markdown("""
This dashboard merges data from TMDB (metadata), OMDb (IMDb ratings), and Wikipedia Pageviews
to surface high-signal Warner Bros / HBO titles. Enter a company search (e.g., "Warner Bros", "HBO").
""")

company_query = st.text_input("Company search", value="Warner Bros")
max_titles = st.slider("Max titles", 10, 200, 60, 10)

if not TMDB_KEY or not OMDB_KEY:
    st.warning("Add TMDB_API_KEY and OMDB_API_KEY to config/.env and restart.")
    st.stop()

@st.cache_data
def tmdb_search_company(name: str):
    url = f"https://api.themoviedb.org/3/search/company?api_key={TMDB_KEY}&query={name}"
    return requests.get(url).json()

@st.cache_data
def tmdb_discover_titles(company_id: int, content_type="movie", page=1):
    url = f"https://api.themoviedb.org/3/discover/{content_type}?api_key={TMDB_KEY}&with_companies={company_id}&page={page}&sort_by=popularity.desc"
    return requests.get(url).json()

@st.cache_data
def tmdb_external_ids(content_type: str, tmdb_id: int):
    url = f"https://api.themoviedb.org/3/{content_type}/{tmdb_id}/external_ids?api_key={TMDB_KEY}"
    return requests.get(url).json()

@st.cache_data
def omdb_by_imdb_id(imdb_id: str):
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_KEY}"
    return requests.get(url).json()

@st.cache_data
def wiki_pageviews(title: str, start="20240101", end="20241231"):
    title_enc = title.replace(" ", "_")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{title_enc}/daily/{start}/{end}"
    r = requests.get(url)
    if r.status_code != 200:
        return []
    data = r.json().get("items", [])
    return [{"date": x["timestamp"][:8], "views": x["views"]} for x in data]

if st.button("Fetch data"):
    companies = tmdb_search_company(company_query).get("results", [])
    if not companies:
        st.error("No companies found.")
        st.stop()
    cid = companies[0]["id"]
    # gather a few pages of movies and TV
    titles = []
    for content_type in ["movie", "tv"]:
        page = 1
        while len(titles) < max_titles and page <= 5:
            data = tmdb_discover_titles(cid, content_type, page)
            for item in data.get("results", []):
                titles.append({"content_type": content_type, "tmdb_id": item["id"], "title": item.get("title") or item.get("name"), "popularity": item.get("popularity", 0)})
                if len(titles) >= max_titles:
                    break
            page += 1

    rows = []
    prog = st.progress(0)
    for i, t in enumerate(titles, 1):
        ext = tmdb_external_ids(t["content_type"], t["tmdb_id"])
        imdb_id = ext.get("imdb_id")
        rating = None
        if imdb_id:
            om = omdb_by_imdb_id(imdb_id)
            try:
                rating = float(om.get("imdbRating")) if om.get("imdbRating") not in [None, "N/A"] else None
            except Exception:
                rating = None
        # wiki views (last year static window for comparability)
        wv = wiki_pageviews(t["title"], start="20240101", end="20241231")
        views_total = sum([x["views"] for x in wv]) if wv else None
        rows.append({**t, "imdb_id": imdb_id, "imdb_rating": rating, "wiki_views_2024": views_total})
        prog.progress(i/len(titles))

    df = pd.DataFrame(rows)
    st.write("Raw data", df)

    # rating vs interest proxy
    df2 = df.dropna(subset=["imdb_rating", "wiki_views_2024"])
    if not df2.empty:
        fig = px.scatter(df2, x="imdb_rating", y="wiki_views_2024", hover_name="title",
                         color="content_type", size="popularity", title="Rating vs. Audience Interest (Wikipedia views)")
        st.plotly_chart(fig, use_container_width=True)

        top_eff = df2.copy()
        top_eff["rating_norm"] = (top_eff["imdb_rating"]-top_eff["imdb_rating"].mean())/top_eff["imdb_rating"].std()
        top_eff["views_norm"] = (top_eff["wiki_views_2024"]-top_eff["wiki_views_2024"].mean())/top_eff["wiki_views_2024"].std()
        top_eff["outperform_index"] = top_eff["views_norm"] - top_eff["rating_norm"]
        st.subheader("Top Outperformers (interest > rating)")
        st.dataframe(top_eff.sort_values("outperform_index", ascending=False).head(15))
    else:
        st.info("Not enough overlapping data for chart.")
