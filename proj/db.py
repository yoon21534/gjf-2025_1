import streamlit as st
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar
from collections import Counter # 연말 결산에서 최애 장르 계산용

# Matplotlib/Seaborn import with fallback and Korean font setting
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    # 한글 폰트 설정 (Mac: AppleGothic, Windows: Malgun Gothic)
    plt.rcParams['font.family'] = ['AppleGothic', 'Malgun Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    st.warning("⚠️ matplotlib/seaborn이 설치되지 않았습니다. 통계 차트 기능이 제한됩니다.")

# --- API 설정 ---
# TMDB API 키: 영화 검색 및 상세 정보, 포스터 가져오기용 (사용자 제공 키)
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

    # 데이터 손실 방지를 위해 DROP TABLE 제거.
    # 테이블이 없으면 생성하고, 있으면 건너뜁니다.
    # cursor.execute("DROP TABLE IF EXISTS user_watch_records") # <-- 이 줄을 제거합니다!

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

    # 사용자 관람 기록 테이블 (my_rating은 0.5점 단위를 위해 REAL 타입)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_watch_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            watch_date TEXT NOT NULL,
            my_rating REAL, 
            my_review TEXT,
            watch_method TEXT,
            watch_method_detail TEXT, 
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    conn.commit()
    conn.close()
    # 첫 실행 시에만 메시지 표시 (기존 데이터가 보존됨을 알림)
    st.info("데이터베이스가 초기화되거나 업데이트되었습니다. 기존 기록은 유지됩니다.") 

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
        "language": "ko-KR" # 한국어 검색 결과를 선호
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
        # KOBIS API는 포스터 URL을 직접 제공하지 않습니다.
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

def update_watch_record_review(record_id, new_review):
    """특정 관람 기록의 감상평을 업데이트합니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE user_watch_records SET my_review = ? WHERE record_id = ?', (new_review, record_id))
        conn.commit()
        st.success("감상평이 업데이트되었습니다!")
    except sqlite3.Error as e:
        st.error(f"감상평 업데이트 중 오류 발생: {e}")
    finally:
        conn.close()


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
        # 요일 한글로 변환 (시스템 로케일 설정에 따라 다를 수 있으므로 명시적으로 지정)
        df['day_of_week'] = df['watch_date'].dt.day_name(locale='ko_KR.UTF-8') 
        # TMDB 웹 URL 컬럼 추가
        df['tmdb_web_url'] = df['tmdb_id'].apply(lambda x: f"{TMDB_MOVIE_WEB_URL}{x}" if x else "#")
    return df

def get_frequent_watch_details_by_method(method_type):
    """지정된 관람 방식(극장/OTT)에 해당하는 자주 기록한 상세 장소/서비스 목록을 가져옵니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT watch_method_detail FROM user_watch_records WHERE watch_method = ? AND watch_method_detail IS NOT NULL AND watch_method_detail != '' ORDER BY watch_method_detail", (method_type,))
    frequent_details = [row[0] for row in cursor.fetchall()]
    conn.close()
    return frequent_details

def get_movies_by_period(start_date, end_date):
    """특정 기간의 영화 기록 가져오기"""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT
            r.record_id,
            m.title,
            m.director,
            m.genre_ids,
            m.runtime,
            r.watch_date,
            r.my_rating,
            r.my_review,
            r.watch_method_detail
        FROM user_watch_records r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.watch_date BETWEEN ? AND ?
        ORDER BY r.watch_date DESC
    '''
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    
    if not df.empty:
        df['watch_date'] = pd.to_datetime(df['watch_date'])
        df['genre_names'] = df['genre_ids'].apply(get_genre_names)
    return df

# --- Streamlit 앱 레이아웃 ---
st.set_page_config(
    page_title="🎬 나만의 영화 기록 및 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DB 초기화 (앱 시작 시 한 번만 실행)
# 'db_initialized' 세션 상태가 없으면 DB를 초기화합니다.
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Define menu options and their default index
MENU_OPTIONS = ["메인", "나의 영화 목록", "월말 결산", "연말 결산", "통계 & 분석"]
DEFAULT_MENU_INDEX = 0 # "메인"이 첫 번째 항목 (인덱스 0)

# --- 사이드바 메뉴 ---
st.sidebar.title("🎬 영화 DB 관리")
st.sidebar.markdown("### 📋 메뉴")
menu_selection = st.sidebar.radio(
    "",
    MENU_OPTIONS,
    index=DEFAULT_MENU_INDEX 
)

# --- 메인 페이지 (박스오피스 + 영화 기록) ---
if menu_selection == "메인":
    st.title("✨ 나의 영화 대시보드 ✨") # 통합된 페이지의 메인 제목
    st.markdown("영화를 기록하고 분석해보세요!")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- 박스오피스 순위 섹션 ---
    st.header("🏆 한국 박스오피스 순위 (일일)")
    st.info("영화진흥위원회(KOBIS) API를 통해 어제 날짜 기준 일일 박스오피스 순위를 가져옵니다.")

    box_office_movies = get_kobis_box_office_rankings()

    if box_office_movies:
        # 박스오피스 영화 목록을 반복하며 표시
        for i, movie in enumerate(box_office_movies[:10]): # 상위 10개만 표시
            with st.container():
                st.markdown(f'<div class="box-office-rank"><strong>{movie["rank"]}위 - {movie["title"]}</strong></div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 4]) # 포스터와 정보/버튼 영역
                with col1:
                    if movie['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                    else:
                        st.write("🎬 포스터 없음")
                with col2:
                    st.write(f"**개봉일:** {movie['openDt'] if movie['openDt'] else 'N/A'}")
                    st.write(f"**누적 관객수:** {int(movie['audiAcc']):,}명") # 누적 관객수 포맷팅
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        naver_ticket_search_url = f"https://search.naver.com/search.naver?query={movie['title']}+예매하기"
                        st.link_button("🎫 예매하기", naver_ticket_search_url) 
                    with col_btn2:
                        watcha_pedia_search_url = f"https://pedia.watcha.com/ko-KR/search?query={movie['title']}"
                        st.link_button("ℹ️ 영화 정보 보기", watcha_pedia_search_url) 

                # 박스오피스에서 바로 기록할 수 있는 칸 추가
                if movie.get('tmdb_id'): # TMDB ID가 있어야 상세 정보 가져오기 가능
                    with st.form(key=f"box_office_record_form_{movie['tmdb_id']}"): # 각 영화별 고유한 폼 키
                        st.markdown("---")
                        st.subheader("나의 기록으로 저장하기")
                        # 0.5점 단위 평점 슬라이더
                        box_office_rating = st.slider("나의 평점 (1-5점)", 1.0, 5.0, 3.0, step=0.5, format="%.1f", key=f"bo_rating_{movie['tmdb_id']}")
                        box_office_review = st.text_area("한 줄 감상평", key=f"bo_review_{movie['tmdb_id']}", placeholder="이 영화에 대한 감상을 적어주세요...")
                        
                        box_office_submitted = st.form_submit_button("내 기록으로 저장")
                        if box_office_submitted:
                            movie_details_from_tmdb = get_movie_details(movie['tmdb_id'])
                            if movie_details_from_tmdb:
                                watch_record = {
                                    "watch_date": datetime.now().strftime('%Y-%m-%d'), # 현재 날짜로 기록
                                    "my_rating": box_office_rating,
                                    "my_review": box_office_review,
                                    "watch_method": "기타", # 박스오피스에서 기록된 것이므로 '기타'로 분류
                                    "watch_method_detail": "박스오피스 확인 후 기록" # 상세 정보
                                }
                                insert_movie_and_record(movie_details_from_tmdb, watch_record)
                                st.rerun() # 저장 후 페이지 새로고침
                            else:
                                st.error("영화 상세 정보를 가져올 수 없어 기록할 수 없습니다.")
                else:
                    st.info("이 영화는 TMDB 정보가 없어 기록할 수 없습니다.")
                st.markdown("</div>", unsafe_allow_html=True) # movie-card 닫기 (이 div는 movie-card 안에 정의되지 않았으므로 제거)
            st.markdown("---") # 각 영화별 구분선 (각 컨테이너 아래에 그어짐)
    else:
        st.empty() 
        st.warning("박스오피스 순위를 가져올 수 없습니다. KOBIS API 키를 확인하거나 잠시 후 다시 시도해주세요.")
        st.info("KOBIS API 키는 영화진흥위원회(KOBIS) 웹사이트에서 별도로 발급받아야 합니다. (TMDB 키와 다릅니다!)")
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True) # 박스오피스 섹션과 영화 기록 섹션 사이의 구분선

    # --- 영화 기록 섹션 ---
    st.header("🎬 영화 기록하기 📝")
    
    search_query = st.text_input("영화 제목을 검색하세요:", placeholder="예: 인터스텔라, 기생충", key="main_movie_search_input") # 고유한 키 사용
    
    if search_query:
        st.subheader(f"'{search_query}' 검색 결과")
        search_results = search_movies(search_query)

        if search_results:
            selected_movie = None
            for movie in search_results[:5]: # 검색 결과 상위 5개만 표시
                with st.container():
                    st.markdown('<div class="movie-card">', unsafe_allow_html=True) # 카드 스타일 시작
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if movie['poster_path']:
                            st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                        else:
                            st.write("🎬 포스터 없음")
                    with col2:
                        st.write(f"**제목:** {movie['title']}")
                        st.write(f"**개봉년도:** {movie['release_date'][:4] if movie['release_date'] else 'N/A'}")
                        st.write(f"**줄거리:** {movie.get('overview', '정보 없음')[:100]}...")
                        if st.button(f"이 영화 기록하기", key=f"main_record_{movie['id']}"): # 고유한 키 사용
                            selected_movie = movie
                            break # 버튼 클릭 시 루프 종료
                    st.markdown('</div>', unsafe_allow_html=True) # 카드 스타일 닫기

            if selected_movie:
                st.subheader(f"📝 '{selected_movie['title']}' 관람 기록 입력")
                movie_details = get_movie_details(selected_movie['id'])
                
                if movie_details:
                    with st.form("main_watch_record_form"): # 고유한 키 사용
                        st.markdown('<div class="movie-card">', unsafe_allow_html=True) # 폼 내부에도 카드 스타일 적용
                        st.write(f"**영화 제목:** {movie_details['title']}")
                        st.write(f"**개봉일:** {movie_details['release_date']}")
                        st.write(f"**감독:** {movie_details['director']}")
                        st.write(f"**주연:** {movie_details['actors']}")
                        st.write(f"**장르:** {get_genre_names(movie_details['genre_ids'])}")
                        # TMDB 웹사이트 링크 추가
                        if movie_details.get('tmdb_web_url') and movie_details['tmdb_web_url'] != '#':
                            st.markdown(f"[TMDB에서 자세히 보기]({movie_details['tmdb_web_url']})", unsafe_allow_html=True)


                        watch_date = st.date_input("📅 관람일", datetime.now(), key="main_watch_date_input") # 고유한 키 사용
                        my_rating = st.slider("⭐ 나의 평점 (1-5점)", 1.0, 5.0, 3.0, step=0.5, format="%.1f", key="main_rating_slider") # 고유한 키 사용
                        my_review = st.text_area("한 줄 감상평", key="main_review_text_area", placeholder="이 영화에 대한 감상을 적어주세요...") # 고유한 키 사용
                        
                        watch_method = st.radio("🎪 관람 방식", ["극장", "OTT/기타"], key="main_method_radio") # 고유한 키 사용
                        
                        watch_method_detail = "" 

                        if watch_method == "극장":
                            frequent_theaters = get_frequent_watch_details_by_method("극장")
                            theater_options = ['새로운 극장 입력'] + frequent_theaters
                            
                            selected_theater_option = st.selectbox(
                                "🏢 극장 이름 선택",
                                theater_options,
                                key="main_theater_selectbox" # 고유한 키 사용
                            )
                            if selected_theater_option == '새로운 극장 입력':
                                watch_method_detail = st.text_input("새로운 극장 이름을 입력하세요 (예: 동수원 메가박스)", key="main_new_theater_input") # 고유한 키 사용
                            else:
                                watch_method_detail = selected_theater_option
                        elif watch_method == "OTT/기타":
                            frequent_ott_etc = get_frequent_watch_details_by_method("OTT/기타")
                            ott_etc_options = ['새로운 서비스/장소 입력'] + frequent_ott_etc
                            
                            selected_ott_etc_option = st.selectbox(
                                "📺 OTT 서비스 또는 기타 장소 선택",
                                ott_etc_options,
                                key="main_ott_etc_selectbox" # 고유한 키 사용
                            )
                            if selected_ott_etc_option == '새로운 서비스/장소 입력':
                                watch_method_detail = st.text_input("새로운 OTT 서비스 또는 기타 장소를 입력하세요 (예: 넷플릭스, 집)", key="main_new_ott_etc_input") # 고유한 키 사용
                            else:
                                watch_method_detail = selected_ott_etc_option
                        
                        submitted = st.form_submit_button("💾 기록 저장하기", key="main_save_record_button") # 고유한 키 사용
                        if submitted:
                            if not watch_method_detail:
                                st.warning("⚠️ 관람 장소/서비스를 입력해주세요.")
                            else:
                                watch_record = {
                                    "watch_date": watch_date.strftime('%Y-%m-%d'),
                                    "my_rating": my_rating,
                                    "my_review": my_review,
                                    "watch_method": watch_method,
                                    "watch_method_detail": watch_method_detail
                                }
                                insert_movie_and_record(movie_details, watch_record)
                                st.rerun() 
                        st.markdown('</div>', unsafe_allow_html=True) # movie-card 닫기
                else:
                    st.warning("영화 상세 정보를 가져올 수 없습니다.")
        else:
            st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")

# --- 2. 나의 영화 목록 페이지 ---
elif menu_selection == "나의 영화 목록":
    st.title("📚 나의 영화 목록 🎬") # 이모티콘 추가
    st.markdown("지금까지 본 영화들을 확인하고 관리해보세요!")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    df_records = get_all_watch_records()

    if not df_records.empty:
        # --- 필터링 및 검색 섹션 ---
        st.subheader("🔍 내 기록 검색 및 필터링")
        search_title = st.text_input("제목으로 검색", key="list_search_title", placeholder="영화 제목을 입력하세요...")

        # 필터링을 위한 고유 값 가져오기
        all_genres_in_records = df_records['genre_names'].str.split(', ').explode().unique().tolist()
        all_genres_in_records = [g for g in all_genres_in_records if g and g != 'N/A'] # 유효하지 않은 값 제거
        all_genres_in_records.sort()

        all_directors_in_records = df_records['director'].unique().tolist()
        all_directors_in_records = [d for d in all_directors_in_records if d and d != '정보 없음'] # 유효하지 않은 값 제거
        all_directors_in_records.sort()

        all_actors_in_records = df_records['actors'].str.split(', ').explode().unique().tolist()
        all_actors_in_records = [a for a in all_actors_in_records if a and a != '정보 없음'] # 유효하지 않은 값 제거
        all_actors_in_records.sort()

        col_filter1, col_filter2, col_filter3 = st.columns(3)
        with col_filter1:
            selected_genres = st.multiselect("장르 선택", all_genres_in_records, key="list_filter_genre")
        with col_filter2:
            selected_directors = st.multiselect("감독 선택", all_directors_in_records, key="list_filter_director")
        with col_filter3:
            selected_actors = st.multiselect("배우 선택", all_actors_in_records, key="list_filter_actor")
        
        filtered_df = df_records.copy()

        # 제목 검색 적용
        if search_title:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_title, case=False, na=False)]
        
        # 장르 필터 적용
        if selected_genres:
            filtered_df = filtered_df[filtered_df['genre_names'].apply(lambda x: any(genre in x for genre in selected_genres))]
        
        # 감독 필터 적용
        if selected_directors:
            filtered_df = filtered_df[filtered_df['director'].isin(selected_directors)]

        # 배우 필터 적용
        if selected_actors:
            filtered_df = filtered_df[filtered_df['actors'].apply(lambda x: any(actor in x for actor in selected_actors))]

        st.markdown("---") # 구분선
        
        if not filtered_df.empty:
            # 월별로 그룹핑하여 표시
            for year_month, group_df in filtered_df.groupby('year_month'):
                st.subheader(f"📅 {year_month}")
                
                # 각 영화를 카드 형태로 표시
                for index, row in group_df.iterrows():
                    with st.container():
                        st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if row['poster_path']:
                                st.image(f"https://image.tmdb.org/t/p/w300{row['poster_path']}", use_container_width=True)
                            else:
                                st.write("🎬 포스터 없음")
                        with col2:
                            st.markdown(f"**제목:** {row['title']}")
                            st.markdown(f"**관람일:** {row['watch_date'].strftime('%Y년 %m월 %d일')} ({row['day_of_week']})")
                            # 평점을 별 아이콘으로만 표시
                            st.markdown(f"**나의 평점:** {'⭐' * int(row['my_rating'])}") 
                            st.markdown(f"**관람 장소:** {row['watch_method_detail']}") # 상세 정보만 표시
                            
                            # 감상평 입력/수정 칸
                            current_review = row['my_review'] if row['my_review'] else ""
                            # Streamlit의 key는 고유해야 하므로 record_id를 사용하여 고유하게 만듭니다.
                            new_review_key = f"review_text_area_{row['record_id']}" 
                            updated_review = st.text_area("감상평", value=current_review, key=new_review_key, placeholder="감상평을 입력해주세요...")
                            
                            # 감상평 저장 버튼
                            save_button_key = f"save_review_button_{row['record_id']}"
                            # 버튼 클릭 시 감상평 업데이트 로직
                            if st.button("감상평 저장", key=save_button_key):
                                if updated_review != current_review: # 변경 사항이 있을 때만 저장
                                    update_watch_record_review(row['record_id'], updated_review)
                                    st.rerun() # 저장 후 페이지 새로고침
                                else:
                                    st.info("변경할 감상평이 없습니다.")

                            # TMDB 웹사이트 링크 추가
                            if row['tmdb_web_url'] and row['tmdb_web_url'] != '#':
                                st.markdown(f"[TMDB에서 자세히 보기]({row['tmdb_web_url']})", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True) # movie-card 닫기
                    st.markdown("---") # 각 영화별 구분선
        else:
            st.info("선택된 필터에 해당하는 영화 기록이 없습니다.")
    else:
        st.info("아직 기록된 영화가 없습니다. '메인' 페이지에서 영화를 기록해주세요!")

# --- 3. 월말 결산 페이지 ---
elif menu_selection == "월말 결산":
    st.title("📅 월말 결산")
    st.markdown("이달의 영화 시청 기록을 확인해보세요!")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # 현재 연도를 기본 선택으로 설정
        selected_year = st.selectbox("📅 년도", range(2020, datetime.now().year + 1), index=len(range(2020, datetime.now().year + 1)) - 1) 
    with col2:
        # 현재 월을 기본 선택으로 설정
        selected_month = st.selectbox("📅 월", range(1, 13), index=datetime.now().month - 1) 

    start_date = f"{selected_year}-{selected_month:02d}-01"
    # 다음 달 1일로 설정하여 해당 월 전체를 포함하도록 함
    if selected_month == 12:
        end_date = f"{selected_year+1}-01-01"
    else:
        end_date = f"{selected_year}-{selected_month+1:02d}-01"

    monthly_movies = get_movies_by_period(start_date, end_date)

    if not monthly_movies.empty:
        st.markdown(f"### 🎬 {selected_year}년 {selected_month}월 결산")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎬</h3>
                <h2>{len(monthly_movies)}</h2>
                <p>이달의 영화 수</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>⭐</h3>
                <h2>{monthly_movies['my_rating'].mean():.1f}</h2>
                <p>평균 평점</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            best_movie = monthly_movies.loc[monthly_movies['my_rating'].idxmax()]
            # 제목이 너무 길 경우 자르기
            display_title = best_movie['title']
            if len(display_title) > 10:
                display_title = display_title[:10] + "..."
            st.markdown(f"""
            <div class="metric-card">
                <h3>🏆</h3>
                <h2>{display_title}</h2>
                <p>이달의 베스트</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌟</h3>
                <h2>{monthly_movies['my_rating'].max():.1f}</h2>
                <p>최고 평점</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📋 이달의 영화 목록")
        # 데이터프레임 컬럼 순서 및 이름 조정
        st.dataframe(monthly_movies[['title', 'director', 'genre_names', 'my_rating', 'watch_date', 'my_review']].rename(columns={'title': '제목', 'director': '감독', 'genre_names': '장르', 'my_rating': '평점', 'watch_date': '관람일', 'my_review': '감상평'}), 
                     use_container_width=True)
        
        # 이달의 장르 분석
        if CHART_AVAILABLE:
            st.markdown("### 🎭 이달의 장르 분포")
            monthly_genres = monthly_movies['genre_names'].str.split(', ').explode()
            # N/A 또는 빈 문자열 장르 제거
            monthly_genres = monthly_genres[monthly_genres != 'N/A'].dropna()
            monthly_genre_counts = monthly_genres.value_counts()
            
            if not monthly_genre_counts.empty:
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.pie(monthly_genre_counts.values, labels=monthly_genre_counts.index, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'🎭 {selected_year}년 {selected_month}월 장르 분포', fontsize=16, pad=20)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("장르 데이터가 없습니다.")
        else:
            st.info("차트 기능을 이용하려면 matplotlib/seaborn 라이브러리를 설치해주세요.")
    else:
        st.info(f"📅 {selected_year}년 {selected_month}월에 시청한 영화가 없습니다.")

# --- 4. 연말 결산 페이지 ---
elif menu_selection == "연말 결산":
    st.title("🎊 연말 결산")
    st.markdown("올해의 영화 시청 기록을 총정리해보세요!")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # 현재 연도를 기본 선택으로 설정
    selected_year = st.selectbox("📅 년도 선택", range(2020, datetime.now().year + 1), index=len(range(2020, datetime.now().year + 1)) - 1)

    start_date = f"{selected_year}-01-01"
    end_date = f"{selected_year+1}-01-01"

    yearly_movies = get_movies_by_period(start_date, end_date)

    if not yearly_movies.empty:
        st.markdown(f"### 🎬 {selected_year}년 영화 결산")
        
        # 주요 지표들
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎬</h3>
                <h2>{len(yearly_movies)}편</h2>
                <p>올해 본 영화</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>⭐</h3>
                <h2>{yearly_movies['my_rating'].mean():.1f}</h2>
                <p>평균 평점</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            total_runtime = yearly_movies['runtime'].sum() if yearly_movies['runtime'].notna().any() else 0
            # 시간을 일수로 변환하여 표시 (선택 사항)
            total_days = round(total_runtime / 60 / 24, 1) 
            st.markdown(f"""
            <div class="metric-card">
                <h3>⏰</h3>
                <h2>{total_days}일</h2>
                <p>총 시청 시간</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            genres = []
            for genre_list in yearly_movies['genre_names'].dropna():
                genres.extend([g.strip() for g in genre_list.split(', ')])
            # N/A 또는 빈 문자열 장르 제거
            genres = [g for g in genres if g and g != 'N/A']
            most_genre = Counter(genres).most_common(1)[0][0] if genres else "없음"
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎭</h3>
                <h2>{most_genre}</h2>
                <p>최애 장르</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 월별 시청 패턴
        if CHART_AVAILABLE:
            st.markdown("### 📊 월별 시청 패턴")
            monthly_counts = yearly_movies.groupby(yearly_movies['watch_date'].dt.month).size()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            # 월 숫자 대신 월 이름으로 표시
            months_korean = [f"{m}월" for m in monthly_counts.index]
            sns.lineplot(x=months_korean, y=monthly_counts.values, marker='o', ax=ax)
            ax.set_title(f'📊 {selected_year}년 월별 영화 시청 수', fontsize=16, pad=20)
            ax.set_xlabel('월', fontsize=12)
            ax.set_ylabel('영화 수', fontsize=12)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("차트 기능을 이용하려면 matplotlib/seaborn 라이브러리를 설치해주세요.")
        
        # 올해의 베스트 영화들
        st.markdown("### 🏆 올해의 베스트 영화")
        # 제목이 길 경우 자르기 (데이터프레임 표시용)
        top_movies_display = yearly_movies.nlargest(10, 'my_rating').copy()
        top_movies_display['title_short'] = top_movies_display['title'].apply(lambda x: x[:20] + "..." if len(x) > 20 else x)
        st.dataframe(top_movies_display[['title_short', 'director', 'genre_names', 'my_rating', 'watch_date', 'my_review']].rename(columns={'title_short': '제목', 'director': '감독', 'genre_names': '장르', 'my_rating': '평점', 'watch_date': '관람일', 'my_review': '감상평'}), use_container_width=True)
        
        # 연간 장르 분석
        if CHART_AVAILABLE:
            st.markdown("### 🎭 연간 장르 선호도")
            yearly_genres = yearly_movies['genre_names'].str.split(', ').explode()
            # N/A 또는 빈 문자열 장르 제거
            yearly_genres = yearly_genres[yearly_genres != 'N/A'].dropna()
            yearly_genre_counts = yearly_genres.value_counts().head(8)
            
            if not yearly_genre_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.pie(yearly_genre_counts.values, labels=yearly_genre_counts.index, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'🎭 {selected_year}년 가장 많이 본 장르', fontsize=16, pad=20)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("선택된 기간에 장르 데이터가 없습니다.")
        else:
            st.info("차트 기능을 이용하려면 matplotlib/seaborn 라이브러리를 설치해주세요.")
        
    else:
        st.info(f"📅 {selected_year}년에 시청한 영화가 없습니다.")

# --- 5. 통계 & 분석 페이지 (전체 기록 기반) ---
elif menu_selection == "통계 & 분석":
    st.title("📊 영화 시청 통계 & 분석")
    st.markdown("나의 모든 영화 기록을 다양한 차트로 분석해보세요!")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    df_records = get_all_watch_records()

    if not df_records.empty:
        # 기본 통계
        st.subheader("📈 기본 통계")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎬</h3>
                <h2>{len(df_records)}</h2>
                <p>총 영화 수</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>⭐</h3>
                <h2>{df_records['my_rating'].mean():.1f}</h2>
                <p>평균 평점</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌟</h3>
                <h2>{df_records['my_rating'].max():.1f}</h2>
                <p>최고 평점</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            total_runtime = df_records['runtime'].sum() if df_records['runtime'].notna().any() else 0
            total_days = round(total_runtime / 60 / 24, 1) # 시간을 일수로 변환
            st.markdown(f"""
            <div class="metric-card">
                <h3>⏰</h3>
                <h2>{total_days}일</h2>
                <p>총 시청 시간</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        if CHART_AVAILABLE:
            # 장르별 선호도
            st.subheader("🎭 장르별 선호도")
            all_genres = df_records['genre_names'].str.split(', ').explode()
            all_genres = all_genres[all_genres != 'N/A'].dropna() # 유효하지 않은 값 제거
            genre_counts = all_genres.value_counts().head(10)
            
            if not genre_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x=genre_counts.values, y=genre_counts.index, ax=ax, palette='viridis')
                ax.set_title('가장 많이 본 장르 TOP 10', fontsize=14)
                ax.set_xlabel('영화 수')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("장르 데이터가 없습니다.")
            st.markdown("---")
            
            # 감독별 통계
            st.subheader("🎬 감독별 통계")
            director_counts = df_records['director'].value_counts().head(10)
            director_counts = director_counts[director_counts.index != '정보 없음'] # '정보 없음' 감독 제거
            if not director_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x=director_counts.values, y=director_counts.index, ax=ax, palette='plasma')
                ax.set_title('가장 많이 본 감독 TOP 10', fontsize=14)
                ax.set_xlabel('영화 수')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("감독 데이터가 없습니다.")
            st.markdown("---")
            
            # 관람 장소별 통계
            st.subheader("🏢 관람 장소별 통계")
            place_counts = df_records['watch_method_detail'].value_counts().head(10)
            place_counts = place_counts[place_counts.index != '박스오피스 확인 후 기록'] # '박스오피스 확인 후 기록' 장소 제거
            if not place_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x=place_counts.values, y=place_counts.index, ax=ax, palette='magma')
                ax.set_title('가장 많이 이용한 관람 장소 TOP 10', fontsize=14)
                ax.set_xlabel('영화 수')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("관람 장소 데이터가 없습니다.")
            st.markdown("---")

            # 요일별 관람 통계
            st.subheader("🗓️ 요일별 관람 통계")
            day_of_week_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            day_counts = df_records['day_of_week'].value_counts().reindex(day_of_week_order, fill_value=0)
            if not day_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=day_counts.index, y=day_counts.values, ax=ax, palette='cividis')
                ax.set_title('가장 많이 본 요일', fontsize=14)
                ax.set_xlabel('요일')
                ax.set_ylabel('관람 횟수')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("요일별 관람 데이터가 없습니다.")
            st.markdown("---")

        else:
            st.info("차트 기능을 이용하려면 matplotlib/seaborn 라이브러리를 설치해주세요.")
        
    else:
        st.info("통계를 보려면 먼저 영화를 추가해주세요!")

# --- 푸터 ---
st.sidebar.markdown("---")
st.sidebar.markdown("**🎬 나만의 영화 데이터베이스**")
st.sidebar.markdown("TMDB & KOBIS API 사용")
