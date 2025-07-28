import streamlit as st
import pandas as pd
import sqlite3
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from collections import Counter
import json

# API 키 설정
TMDB_API_KEY = "72f47da81a7babbaa9b8cf7f9727a265"
KOFIC_API_KEY = "d65bf4b8942e90012247c40a2dec31e1"

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watched_movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        director TEXT,
        genre TEXT,
        release_year INTEGER,
        rating REAL,
        watch_date DATE,
        watch_time TEXT,
        review TEXT,
        tmdb_id INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()

# TMDB API 함수들
def search_movie_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ko-KR'
    }
    response = requests.get(url, params=params)
    return response.json()

def get_movie_details_tmdb(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ko-KR'
    }
    response = requests.get(url, params=params)
    return response.json()

# KOFIC API - 박스오피스
def get_box_office():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        'key': KOFIC_API_KEY,
        'targetDt': yesterday
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except:
        return None

# 데이터베이스 함수들
def add_movie_to_db(title, director, genre, release_year, rating, watch_date, watch_time, review, tmdb_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO watched_movies (title, director, genre, release_year, rating, watch_date, watch_time, review, tmdb_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, director, genre, release_year, rating, watch_date, watch_time, review, tmdb_id))
    
    conn.commit()
    conn.close()

def get_all_movies():
    conn = sqlite3.connect('movies.db')
    df = pd.read_sql_query("SELECT * FROM watched_movies ORDER BY watch_date DESC", conn)
    conn.close()
    return df

def get_movies_by_period(start_date, end_date):
    conn = sqlite3.connect('movies.db')
    df = pd.read_sql_query('''
    SELECT * FROM watched_movies 
    WHERE watch_date BETWEEN ? AND ?
    ORDER BY watch_date DESC
    ''', conn, params=(start_date, end_date))
    conn.close()
    return df

# Streamlit 앱
def main():
    st.set_page_config(page_title="🎬 영화 데이터베이스", layout="wide")
    
    # 사이드바
    st.sidebar.title("🎬 영화 DB 관리")
    menu = st.sidebar.selectbox("메뉴 선택", 
                               ["영화 추가", "내 영화 목록", "통계 & 분석", "월말 결산", "연말 결산", "박스오피스"])
    
    # 데이터베이스 초기화
    init_db()
    
    if menu == "영화 추가":
        st.title("🎬 새 영화 추가")
        
        # 영화 검색
        search_query = st.text_input("영화 제목 검색")
        if search_query:
            movies = search_movie_tmdb(search_query)
            if movies.get('results'):
                selected_movie = st.selectbox(
                    "검색 결과에서 선택",
                    movies['results'][:10],
                    format_func=lambda x: f"{x['title']} ({x.get('release_date', 'N/A')[:4] if x.get('release_date') else 'N/A'})"
                )
                
                if selected_movie:
                    details = get_movie_details_tmdb(selected_movie['id'])
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if selected_movie.get('poster_path'):
                            st.image(f"https://image.tmdb.org/t/p/w300{selected_movie['poster_path']}")
                    
                    with col2:
                        st.subheader(selected_movie['title'])
                        st.write(f"**개봉년도:** {selected_movie.get('release_date', 'N/A')[:4] if selected_movie.get('release_date') else 'N/A'}")
                        st.write(f"**장르:** {', '.join([g['name'] for g in details.get('genres', [])])}")
                        st.write(f"**줄거리:** {selected_movie.get('overview', '정보 없음')}")
                        
                        # 감독 정보 (크레딧 API 호출 필요하지만 간단히 처리)
                        director = st.text_input("감독", value="")
                        
                        # 시청 정보 입력
                        rating = st.slider("평점", 0.0, 10.0, 5.0, 0.5)
                        watch_date = st.date_input("시청 날짜", datetime.now())
                        watch_time = st.selectbox("시청 시간대", 
                                                ["새벽 (00-06)", "오전 (06-12)", "오후 (12-18)", "밤 (18-24)"])
                        review = st.text_area("한줄평")
                        
                        if st.button("영화 추가"):
                            add_movie_to_db(
                                selected_movie['title'],
                                director,
                                ', '.join([g['name'] for g in details.get('genres', [])]),
                                int(selected_movie.get('release_date', '0000')[:4]) if selected_movie.get('release_date') else 0,
                                rating,
                                watch_date,
                                watch_time,
                                review,
                                selected_movie['id']
                            )
                            st.success("영화가 추가되었습니다!")
                            st.rerun()
    
    elif menu == "내 영화 목록":
        st.title("📋 내가 본 영화들")
        
        movies_df = get_all_movies()
        if not movies_df.empty:
            st.dataframe(movies_df[['title', 'director', 'genre', 'rating', 'watch_date', 'review']], 
                        use_container_width=True)
            
            st.subheader("📊 빠른 통계")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 영화 수", len(movies_df))
            with col2:
                st.metric("평균 평점", f"{movies_df['rating'].mean():.1f}")
            with col3:
                st.metric("최고 평점", f"{movies_df['rating'].max():.1f}")
            with col4:
                st.metric("이번 달 시청", len(movies_df[movies_df['watch_date'].str.contains(datetime.now().strftime('%Y-%m'))]))
        else:
            st.info("아직 추가된 영화가 없습니다.")
    
    elif menu == "통계 & 분석":
        st.title("📊 영화 시청 통계")
        
        movies_df = get_all_movies()
        if not movies_df.empty:
            # 장르별 통계
            st.subheader("🎭 좋아하는 장르")
            genres = []
            for genre_list in movies_df['genre'].dropna():
                genres.extend([g.strip() for g in genre_list.split(',')])
            genre_counts = Counter(genres)
            
            if genre_counts:
                fig = px.bar(x=list(genre_counts.keys())[:10], y=list(genre_counts.values())[:10],
                           title="가장 많이 본 장르 TOP 10")
                st.plotly_chart(fig, use_container_width=True)
            
            # 감독별 통계
            st.subheader("🎬 좋아하는 감독")
            director_counts = movies_df['director'].value_counts().head(10)
            if not director_counts.empty:
                fig = px.bar(x=director_counts.values, y=director_counts.index, orientation='h',
                           title="가장 많이 본 감독 TOP 10")
                st.plotly_chart(fig, use_container_width=True)
            
            # 시청 요일 분석
            st.subheader("📅 시청 패턴 - 요일별")
            movies_df['watch_date'] = pd.to_datetime(movies_df['watch_date'])
            movies_df['weekday'] = movies_df['watch_date'].dt.day_name()
            weekday_counts = movies_df['weekday'].value_counts()
            
            fig = px.pie(values=weekday_counts.values, names=weekday_counts.index,
                        title="요일별 영화 시청 분포")
            st.plotly_chart(fig, use_container_width=True)
            
            # 시간대별 분석
            st.subheader("🕐 시청 패턴 - 시간대별")
            time_counts = movies_df['watch_time'].value_counts()
            fig = px.bar(x=time_counts.index, y=time_counts.values,
                        title="시간대별 영화 시청 패턴")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("통계를 보려면 먼저 영화를 추가해주세요.")
    
    elif menu == "월말 결산":
        st.title("📅 월말 결산")
        
        # 월 선택
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("년도", range(2020, 2026), index=5)
        with col2:
            selected_month = st.selectbox("월", range(1, 13), index=datetime.now().month-1)
        
        # 해당 월 데이터 가져오기
        start_date = f"{selected_year}-{selected_month:02d}-01"
        if selected_month == 12:
            end_date = f"{selected_year+1}-01-01"
        else:
            end_date = f"{selected_year}-{selected_month+1:02d}-01"
        
        monthly_movies = get_movies_by_period(start_date, end_date)
        
        if not monthly_movies.empty:
            st.subheader(f"🎬 {selected_year}년 {selected_month}월 결산")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("이달의 영화 수", len(monthly_movies))
            with col2:
                st.metric("평균 평점", f"{monthly_movies['rating'].mean():.1f}")
            with col3:
                best_movie = monthly_movies.loc[monthly_movies['rating'].idxmax()]
                st.metric("이달의 베스트", f"{best_movie['title'][:10]}...")
            with col4:
                st.metric("최고 평점", f"{monthly_movies['rating'].max():.1f}")
            
            # 상세 목록
            st.subheader("📋 이달의 영화 목록")
            st.dataframe(monthly_movies[['title', 'director', 'genre', 'rating', 'watch_date']], 
                        use_container_width=True)
        else:
            st.info(f"{selected_year}년 {selected_month}월에 시청한 영화가 없습니다.")
    
    elif menu == "연말 결산":
        st.title("🎊 연말 결산")
        
        selected_year = st.selectbox("년도 선택", range(2020, 2026), index=5)
        
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year+1}-01-01"
        
        yearly_movies = get_movies_by_period(start_date, end_date)
        
        if not yearly_movies.empty:
            st.subheader(f"🎬 {selected_year}년 영화 결산")
            
            # 주요 지표들
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("올해 본 영화", f"{len(yearly_movies)}편")
            with col2:
                st.metric("평균 평점", f"{yearly_movies['rating'].mean():.1f}")
            with col3:
                hours = len(yearly_movies) * 2  # 평균 2시간으로 가정
                st.metric("영화 시청 시간", f"{hours}시간")
            with col4:
                genres = []
                for genre_list in yearly_movies['genre'].dropna():
                    genres.extend([g.strip() for g in genre_list.split(',')])
                most_genre = Counter(genres).most_common(1)[0][0] if genres else "없음"
                st.metric("최애 장르", most_genre)
            
            # 월별 시청 패턴
            st.subheader("📊 월별 시청 패턴")
            yearly_movies['watch_date'] = pd.to_datetime(yearly_movies['watch_date'])
            monthly_counts = yearly_movies.groupby(yearly_movies['watch_date'].dt.month).size()
            
            fig = px.line(x=monthly_counts.index, y=monthly_counts.values,
                         title=f"{selected_year}년 월별 영화 시청 수")
            fig.update_xaxis(title="월")
            fig.update_yaxis(title="영화 수")
            st.plotly_chart(fig, use_container_width=True)
            
            # 베스트 영화들
            st.subheader("🏆 올해의 베스트 영화")
            top_movies = yearly_movies.nlargest(5, 'rating')[['title', 'director', 'rating', 'watch_date', 'review']]
            st.dataframe(top_movies, use_container_width=True)
            
        else:
            st.info(f"{selected_year}년에 시청한 영화가 없습니다.")
    
    elif menu == "박스오피스":
        st.title("🏆 박스오피스 순위")
        
        box_office_data = get_box_office()
        if box_office_data and 'boxOfficeResult' in box_office_data:
            daily_list = box_office_data['boxOfficeResult']['dailyBoxOfficeList']
            
            st.subheader(f"📅 {box_office_data['boxOfficeResult']['showRange']} 박스오피스")
            
            for movie in daily_list[:10]:
                with st.container():
                    col1, col2, col3 = st.columns([1, 6, 2])
                    with col1:
                        st.markdown(f"**{movie['rank']}위**")
                    with col2:
                        st.markdown(f"**{movie['movieNm']}**")
                        st.caption(f"누적관객: {int(movie['audiAcc']):,}명")
                    with col3:
                        st.metric("관객수", f"{int(movie['audiCnt']):,}명")
                    st.divider()
        else:
            st.error("박스오피스 데이터를 가져올 수 없습니다.")

if __name__ == "__main__":
    main()