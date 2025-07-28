import streamlit as st
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import calendar # 월 이름을 가져오기 위함

# --- API 설정 ---
# TMDB API 키: 영화 검색 및 상세 정보, 포스터 가져오기용
# 이 키는 사용자께서 제공해주신 TMDB API 키입니다.
TMDB_API_KEY = "72f47da81a7babbaa9b8cf7f9727a265" 
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_MOVIE_WEB_URL = "https://www.themoviedb.org/movie/" # TMDB 영화 페이지 기본 URL

# KOBIS (영화진흥위원회) API 설정: 한국 박스오피스 순위 가져오기용
# 이 키는 사용자께서 제공해주신 KOBIS API 키입니다.
KOBIS_API_KEY = "d65bf4b8942e90012247c40a2dec31e1" 
KOBIS_BASE_URL = "http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"


# --- 데이터베이스 설정 ---
DB_NAME = 'movies.db'

def init_db():
    """데이터베이스를 초기화하고 필요한 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 기존 user_watch_records 테이블이 있다면 삭제하고 재생성 (스키마 변경을 위해)
    # 실제 운영 환경에서는 ALTER TABLE을 사용해야 하지만, 여기서는 학습 목적상 DROP/CREATE 사용
    cursor.execute("DROP TABLE IF EXISTS user_watch_records")

    # 영화 정보 테이블 (TMDB에서 가져온 정보)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            original_title TEXT,
            release_date TEXT,
            genre_ids TEXT, -- 쉼표로 구분된 장르 ID
            overview TEXT,
            poster_path TEXT,
            director TEXT,
            actors TEXT,
            runtime INTEGER
        )
    ''')

    # 사용자 관람 기록 테이블 (재관람 의사 제거, 관람 장소 상세 추가)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_watch_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            watch_date TEXT NOT NULL,
            my_rating INTEGER, -- 1-5점
            my_review TEXT,
            watch_method TEXT, -- 극장, OTT/기타 (선택된 상위 카테고리)
            watch_method_detail TEXT, -- 동수원 메가박스, 넷플릭스 등 (상세 장소/서비스)
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    conn.commit()
    conn.close()
    st.success("데이터베이스가 초기화되었습니다. (기존 관람 기록은 삭제됨)") # 스키마 변경으로 인한 알림

# --- TMDB API 함수들 ---
def search_movies(query):
    """TMDB에서 영화를 검색합니다."""
    if not TMDB_API_KEY:
        st.error("TMDB API 키가 설정되지 않았습니다. 코드 상단의 `TMDB_API_KEY` 변수를 확인하세요.")
        return []
    
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "ko-KR" # 한국어 검색 결과 선호
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"영화 검색 중 오류 발생: {e}")
        return []

def get_movie_details(tmdb_id):
    """TMDB에서 특정 영화의 상세 정보를 가져옵니다."""
    if not TMDB_API_KEY:
        st.error("TMDB API 키가 설정되지 않았습니다. 코드 상단의 `TMDB_API_KEY` 변수를 확인하세요.")
        return None

    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "ko-KR",
        "append_to_response": "credits" # 감독, 배우 정보 포함
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        details = response.json()

        # 감독 정보 추출
        director = "정보 없음"
        for crew in details.get("credits", {}).get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name")
                break
        
        # 배우 정보 추출 (주연 3명 정도)
        actors = ", ".join([cast.get("name") for cast in details.get("credits", {}).get("cast", [])[:3]])
        if not actors:
            actors = "정보 없음"

        return {
            "tmdb_id": details.get("id"),
            "title": details.get("title"),
            "original_title": details.get("original_title"),
            "release_date": details.get("release_date"),
            "genre_ids": ",".join(str(g["id"]) for g in details.get("genres", [])),
            "overview": details.get("overview"),
            "poster_path": details.get("poster_path"),
            "director": director,
            "actors": actors,
            "runtime": details.get("runtime"),
            "tmdb_web_url": f"{TMDB_MOVIE_WEB_URL}{details.get('id')}" # TMDB 웹 URL 추가
        }
    except requests.exceptions.RequestException as e:
        st.error(f"영화 상세 정보 가져오는 중 오류 발생: {e}")
        return None

def get_genre_names(genre_ids_str):
    """TMDB 장르 ID를 장르 이름으로 변환합니다."""
    genre_map = {
        28: "액션", 12: "모험", 16: "애니메이션", 35: "코미디", 80: "범죄",
        99: "다큐멘터리", 18: "드라마", 10751: "가족", 14: "판타지", 36: "역사",
        27: "공포", 10402: "음악", 9648: "미스터리", 10749: "로맨스", 878: "SF",
        10770: "TV 영화", 53: "스릴러", 10752: "전쟁", 37: "서부"
    }
    if not genre_ids_str:
        return "N/A"
    
    ids = [int(x) for x in genre_ids_str.split(',') if x.strip().isdigit()]
    return ", ".join([genre_map.get(id, "알 수 없음") for id in ids])

def get_kobis_box_office_rankings():
    """KOBIS API에서 일일 박스오피스 순위를 가져옵니다."""
    if not KOBIS_API_KEY:
        st.error("KOBIS API 키가 설정되지 않았습니다. 한국 박스오피스 순위를 보려면 KOBIS API 키를 코드에 입력해주세요.")
        st.info("KOBIS API 키는 영화진흥위원회(KOBIS) 웹사이트에서 별도로 발급받아야 합니다. (TMDB 키와 다릅니다!)")
        return []

    # 어제 날짜 기준으로 박스오피스 순위 조회
    target_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    url = KOBIS_BASE_URL
    params = {
        "key": KOBIS_API_KEY,
        "targetDt": target_date
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        box_office_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        
        # TMDB의 포스터를 가져오기 위해 영화 제목으로 TMDB 검색을 시도
        movies_with_posters = []
        for movie in box_office_list:
            tmdb_search_results = search_movies(movie.get('movieNm')) 
            poster_path = None
            tmdb_id = None # TMDB ID도 함께 저장하여 웹 URL 생성에 사용
            if tmdb_search_results:
                poster_path = tmdb_search_results[0].get('poster_path')
                tmdb_id = tmdb_search_results[0].get('id')
            
            movies_with_posters.append({
                "rank": movie.get('rank'),
                "title": movie.get('movieNm'),
                "openDt": movie.get('openDt'),
                "audiAcc": movie.get('audiAcc'), # 누적 관객수
                "poster_path": poster_path,
                "tmdb_id": tmdb_id # TMDB ID 추가
            })
        return movies_with_posters
    except requests.exceptions.RequestException as e:
        st.error(f"KOBIS 박스오피스 순위 가져오는 중 오류 발생: {e}")
        st.info("KOBIS API 키가 유효한지, 또는 API 호출 제한에 걸리지 않았는지 확인해주세요.")
        return []

# --- 데이터베이스 CRUD 함수들 ---
def insert_movie_and_record(movie_details, watch_record):
    """영화 정보와 사용자 관람 기록을 DB에 저장합니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. movies 테이블에 영화 정보 저장 (이미 있으면 업데이트 또는 건너뛰기)
    cursor.execute('SELECT id FROM movies WHERE tmdb_id = ?', (movie_details['tmdb_id'],))
    movie_id_in_db = cursor.fetchone()

    if movie_id_in_db:
        movie_id = movie_id_in_db[0]
        # st.info(f"'{movie_details['title']}' 영화는 이미 DB에 있습니다. 기존 정보를 사용합니다.")
    else:
        cursor.execute('''
            INSERT INTO movies (tmdb_id, title, original_title, release_date, genre_ids, overview, poster_path, director, actors, runtime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            movie_details['tmdb_id'], movie_details['title'], movie_details['original_title'],
            movie_details['release_date'], movie_details['genre_ids'], movie_details['overview'],
            movie_details['poster_path'], movie_details['director'], movie_details['actors'],
            movie_details['runtime']
        ))
        movie_id = cursor.lastrowid
        st.success(f"새로운 영화 '{movie_details['title']}' 정보를 DB에 저장했습니다.")

    # 2. user_watch_records 테이블에 관람 기록 저장
    cursor.execute('''
        INSERT INTO user_watch_records (movie_id, watch_date, my_rating, my_review, watch_method, watch_method_detail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        movie_id, watch_record['watch_date'], watch_record['my_rating'],
        watch_record['my_review'], watch_record['watch_method'], watch_record['watch_method_detail']
    ))
    conn.commit()
    conn.close()
    st.success(f"'{movie_details['title']}' 관람 기록을 성공적으로 저장했습니다!")

def get_all_watch_records():
    """모든 관람 기록과 연결된 영화 정보를 가져옵니다."""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT
            r.record_id,
            m.title,
            m.original_title,
            m.poster_path,
            m.genre_ids,
            m.director,
            m.actors,
            m.runtime,
            m.tmdb_id,  -- TMDB ID도 함께 가져옴
            r.watch_date,
            r.my_rating,
            r.my_review,
            r.watch_method,
            r.watch_method_detail
        FROM user_watch_records r
        JOIN movies m ON r.movie_id = m.id
        ORDER BY r.watch_date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['watch_date'] = pd.to_datetime(df['watch_date'])
        df['year_month'] = df['watch_date'].dt.strftime('%Y년 %m월')
        df['genre_names'] = df['genre_ids'].apply(get_genre_names)
        df['day_of_week'] = df['watch_date'].dt.day_name(locale='ko_KR.UTF-8') # 요일 한글로
        # TMDB 웹 URL 컬럼 추가
        df['tmdb_web_url'] = df['tmdb_id'].apply(lambda x: f"{TMDB_MOVIE_WEB_URL}{x}" if x else "#")
    return df

def get_frequent_watch_details():
    """사용자가 자주 기록한 관람 장소/서비스 목록을 가져옵니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT watch_method_detail FROM user_watch_records WHERE watch_method_detail IS NOT NULL AND watch_method_detail != '' ORDER BY watch_method_detail")
    frequent_details = [row[0] for row in cursor.fetchall()]
    conn.close()
    return frequent_details

# --- Streamlit 앱 레이아웃 ---
st.set_page_config(
    page_title="나만의 영화 기록 및 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DB 초기화 (앱 시작 시 한 번만 실행)
# 스키마 변경이 있었으므로, 기존 DB를 삭제하고 새로 생성합니다.
# 실제 데이터가 있다면 ALTER TABLE 등을 사용해야 합니다.
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# --- 사이드바 메뉴 ---
st.sidebar.title("메뉴")
menu_selection = st.sidebar.radio(
    "",
    ["영화 기록하기", "나의 영화 목록", "연말/월말 결산", "박스오피스 순위"]
)

# --- 1. 영화 기록하기 페이지 ---
if menu_selection == "영화 기록하기":
    st.title("🎬 영화 기록하기")
    
    search_query = st.text_input("영화 제목을 검색하세요:", key="movie_search_input")
    
    if search_query:
        st.subheader(f"'{search_query}' 검색 결과")
        search_results = search_movies(search_query)

        if search_results:
            selected_movie = None
            for movie in search_results:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if movie['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                    else:
                        st.write("[이미지 없음]")
                with col2:
                    st.write(f"**{movie['title']}** ({movie['release_date'][:4] if movie['release_date'] else 'N/A'})")
                    if st.button(f"이 영화 기록하기", key=f"record_{movie['id']}"):
                        selected_movie = movie
                        break # 버튼 클릭 시 루프 종료

            if selected_movie:
                st.subheader(f"'{selected_movie['title']}' 관람 기록 입력")
                movie_details = get_movie_details(selected_movie['id'])
                
                if movie_details:
                    with st.form("watch_record_form"):
                        st.write(f"**영화 제목:** {movie_details['title']}")
                        st.write(f"**개봉일:** {movie_details['release_date']}")
                        st.write(f"**감독:** {movie_details['director']}")
                        st.write(f"**주연:** {movie_details['actors']}")
                        st.write(f"**장르:** {get_genre_names(movie_details['genre_ids'])}")
                        # TMDB 웹사이트 링크 추가
                        if movie_details.get('tmdb_web_url') and movie_details['tmdb_web_url'] != '#':
                            st.markdown(f"[TMDB에서 자세히 보기]({movie_details['tmdb_web_url']})", unsafe_allow_html=True)


                        watch_date = st.date_input("관람일", datetime.now(), key="watch_date_input")
                        my_rating = st.slider("나의 평점 (1-5점)", 1, 5, 3, key="rating_slider")
                        my_review = st.text_area("한 줄 감상평", key="review_text_area")
                        
                        # 관람 방식 선택 (라디오 버튼)
                        watch_method = st.radio("관람 방식", ["극장", "OTT/기타"], key="method_radio")
                        
                        # 자주 가는 장소 목록 가져오기
                        frequent_locations = get_frequent_watch_details()
                        location_options = ['새로운 장소 입력'] + frequent_locations
                        
                        selected_location_option = st.selectbox(
                            "관람 장소 선택", 
                            location_options, 
                            key="location_selectbox"
                        )

                        watch_method_detail = ""
                        if selected_location_option == '새로운 장소 입력':
                            watch_method_detail = st.text_input("새로운 관람 장소/서비스를 입력하세요 (예: 동수원 메가박스, 넷플릭스)", key="new_location_input")
                        else:
                            watch_method_detail = selected_location_option
                        
                        submitted = st.form_submit_button("기록 저장하기")
                        if submitted:
                            if not watch_method_detail:
                                st.warning("관람 장소/서비스를 입력해주세요.")
                            else:
                                watch_record = {
                                    "watch_date": watch_date.strftime('%Y-%m-%d'),
                                    "my_rating": my_rating,
                                    "my_review": my_review,
                                    "watch_method": watch_method,
                                    "watch_method_detail": watch_method_detail
                                }
                                insert_movie_and_record(movie_details, watch_record)
                                st.experimental_rerun() # 저장 후 페이지 새로고침
                else:
                    st.warning("영화 상세 정보를 가져올 수 없습니다.")
        else:
            st.info("검색 결과가 없습니다.")

# --- 2. 나의 영화 목록 페이지 ---
elif menu_selection == "나의 영화 목록":
    st.title("📚 나의 영화 목록")
    
    df_records = get_all_watch_records()

    if not df_records.empty:
        # 월별로 그룹핑하여 표시
        for year_month, group_df in df_records.groupby('year_month'):
            st.subheader(f"📅 {year_month}")
            
            # 각 영화를 카드 형태로 표시
            for index, row in group_df.iterrows():
                col1, col2 = st.columns([1, 4])
                with col1:
                    if row['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w300{row['poster_path']}", use_container_width=True)
                    else:
                        st.write("[이미지 없음]")
                with col2:
                    st.markdown(f"**제목:** {row['title']}")
                    st.markdown(f"**관람일:** {row['watch_date'].strftime('%Y년 %m월 %d일')} ({row['day_of_week']})")
                    st.markdown(f"**나의 평점:** {'⭐' * row['my_rating']}")
                    st.markdown(f"**한 줄 감상평:** {row['my_review']}")
                    st.markdown(f"**관람 장소:** {row['watch_method_detail']}") # 상세 정보만 표시하도록 변경
                    # TMDB 웹사이트 링크 추가
                    if row['tmdb_web_url'] and row['tmdb_web_url'] != '#':
                        st.markdown(f"[TMDB에서 자세히 보기]({row['tmdb_web_url']})", unsafe_allow_html=True)
                    st.markdown("---") # 구분선
    else:
        st.info("아직 기록된 영화가 없습니다. '영화 기록하기'에서 추가해주세요!")

# --- 3. 연말/월말 결산 페이지 ---
elif menu_selection == "연말/월말 결산":
    st.title("📊 연말/월말 결산 및 분석")

    df_records = get_all_watch_records()

    if not df_records.empty:
        # 연도/월 선택 필터
        all_years = sorted(df_records['watch_date'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("연도를 선택하세요", ['전체'] + all_years, key="select_year")

        if selected_year != '전체':
            df_filtered_year = df_records[df_records['watch_date'].dt.year == selected_year]
            all_months = sorted(df_filtered_year['watch_date'].dt.month.unique())
            month_names = ['전체'] + [calendar.month_name[m] for m in all_months]
            selected_month_idx = st.selectbox("월을 선택하세요", range(len(month_names)), format_func=lambda x: month_names[x], key="select_month")
            selected_month = all_months[selected_month_idx - 1] if selected_month_idx > 0 else '전체'
        else:
            df_filtered_year = df_records
            selected_month = '전체'

        if selected_month != '전체':
            df_display = df_filtered_year[df_filtered_year['watch_date'].dt.month == selected_month]
            st.subheader(f"{selected_year}년 {selected_month}월 결산")
        elif selected_year != '전체':
            df_display = df_filtered_year
            st.subheader(f"{selected_year}년 연간 결산")
        else:
            df_display = df_records
            st.subheader("전체 기간 결산")

        if not df_display.empty:
            st.markdown(f"총 관람 영화 수: **{len(df_display)}**편")
            st.markdown(f"평균 평점: **{df_display['my_rating'].mean():.2f}**점")

            # 1. 월별/연도별 관람 추이 (선택된 기간이 '전체'일 때만 의미 있음)
            if selected_year == '전체' and selected_month == '전체':
                st.subheader("월별 관람 영화 수 추이")
                monthly_counts = df_display.groupby(df_display['watch_date'].dt.to_period('M')).size().reset_index(name='count')
                monthly_counts['watch_date'] = monthly_counts['watch_date'].dt.strftime('%Y-%m')
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.lineplot(x='watch_date', y='count', data=monthly_counts, marker='o', ax=ax)
                ax.set_title('월별 관람 영화 수')
                ax.set_xlabel('연-월')
                ax.set_ylabel('영화 수')
                plt.xticks(rotation=45)
                st.pyplot(fig)
                st.markdown("---")

            # 2. 장르별 선호도
            st.subheader("장르별 선호도")
            all_genres = df_display['genre_names'].str.split(', ').explode()
            genre_counts = all_genres.value_counts().nlargest(10) # 상위 10개 장르
            if not genre_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie(genre_counts, labels=genre_counts.index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'})
                ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
                ax.set_title('가장 많이 본 장르')
                st.pyplot(fig)
            else:
                st.info("선택된 기간에 장르 데이터가 없습니다.")
            st.markdown("---")

            # 3. 가장 많이 본 감독
            st.subheader("가장 많이 본 감독")
            director_counts = df_display['director'].value_counts().nlargest(5) # 상위 5명
            if not director_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=director_counts.index, y=director_counts.values, ax=ax, palette='viridis')
                ax.set_title('가장 많이 본 감독')
                ax.set_xlabel('감독')
                ax.set_ylabel('관람 횟수')
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)
            else:
                st.info("선택된 기간에 감독 데이터가 없습니다.")
            st.markdown("---")

            # 4. 가장 많이 본 요일
            st.subheader("가장 많이 본 요일")
            day_of_week_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            day_counts = df_display['day_of_week'].value_counts().reindex(day_of_week_order, fill_value=0)
            if not day_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=day_counts.index, y=day_counts.values, ax=ax, palette='magma')
                ax.set_title('가장 많이 본 요일')
                ax.set_xlabel('요일')
                ax.set_ylabel('관람 횟수')
                st.pyplot(fig)
            else:
                st.info("선택된 기간에 요일 데이터가 없습니다.")
            st.markdown("---")

            # 5. 관람 방식별 통계
            st.subheader("관람 방식별 통계")
            method_counts = df_display['watch_method'].value_counts()
            if not method_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 5))
                sns.barplot(x=method_counts.index, y=method_counts.values, ax=ax, palette='cividis')
                ax.set_title('관람 방식별 영화 수')
                ax.set_xlabel('관람 방식')
                ax.set_ylabel('영화 수')
                st.pyplot(fig)
                
                # 상세 장소/서비스별 통계
                st.subheader("관람 장소/서비스 상세 통계")
                detail_counts = df_display['watch_method_detail'].value_counts().nlargest(10)
                if not detail_counts.empty:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x=detail_counts.index, y=detail_counts.values, ax=ax, palette='plasma')
                    ax.set_title('가장 많이 이용한 관람 장소/서비스')
                    ax.set_xlabel('장소/서비스')
                    ax.set_ylabel('영화 수')
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)
                else:
                    st.info("선택된 기간에 상세 관람 장소/서비스 데이터가 없습니다.")
            else:
                st.info("선택된 기간에 관람 방식 데이터가 없습니다.")
            st.markdown("---")


        else:
            st.info("선택된 기간에 해당하는 영화 기록이 없습니다.")
    else:
        st.info("아직 기록된 영화가 없습니다. '영화 기록하기'에서 추가해주세요!")

# --- 4. 박스오피스 순위 페이지 ---
elif menu_selection == "박스오피스 순위":
    st.title("🏆 한국 박스오피스 순위 (일일)")
    st.info("영화진흥위원회(KOBIS) API를 통해 어제 날짜 기준 일일 박스오피스 순위를 가져옵니다.")

    box_office_movies = get_kobis_box_office_rankings()

    if box_office_movies:
        # KOBIS API에서 데이터를 성공적으로 가져왔을 때만 순위를 표시
        for i, movie in enumerate(box_office_movies[:10]): # 상위 10개만 표시
            col1, col2, col3 = st.columns([0.5, 1, 4])
            with col1:
                st.header(f"{movie['rank']}위") # KOBIS 랭크 사용
            with col2:
                if movie['poster_path']:
                    st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                else:
                    st.write("[이미지 없음]")
            with col3:
                st.markdown(f"**제목:** {movie['title']}")
                st.markdown(f"**개봉일:** {movie['openDt'] if movie['openDt'] else 'N/A'}")
                st.markdown(f"**누적 관객수:** {int(movie['audiAcc']):,}명") # 누적 관객수 포맷팅
                
                # 네이버 영화 예매/정보 보기 버튼 추가
                naver_movie_search_url = f"https://search.naver.com/search.naver?query={movie['title']}+영화"
                st.link_button("네이버 영화에서 예매/정보 보기", naver_movie_search_url)

                # TMDB 웹사이트 링크 추가 (기존 링크 유지)
                if movie.get('tmdb_id'): # tmdb_id가 있을 때만 링크 생성
                    st.markdown(f"[TMDB에서 자세히 보기]({TMDB_MOVIE_WEB_URL}{movie['tmdb_id']})", unsafe_allow_html=True)
            st.markdown("---")
    else:
        # KOBIS API 호출 실패 시, 검색창 대신 경고 메시지만 표시
        st.empty() # 혹시 남아있을 수 있는 이전 UI 요소를 비웁니다.
        st.warning("박스오피스 순위를 가져올 수 없습니다. KOBIS API 키를 확인하거나 잠시 후 다시 시도해주세요.")
        st.info("KOBIS API 키는 영화진흥위원회(KOBIS) 웹사이트에서 별도로 발급받아야 합니다. (TMDB 키와 다릅니다!)")
