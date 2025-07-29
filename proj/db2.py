import streamlit as st
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar
from collections import Counter
import json

# 차트 라이브러리 import 시도
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']  # 한글 폰트 설정
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    st.warning("⚠️ matplotlib/seaborn이 설치되지 않았습니다. 차트 기능이 제한됩니다.")

# API 키 설정
TMDB_API_KEY = "72f47da81a7babbaa9b8cf7f9727a265"
KOFIC_API_KEY = "d65bf4b8942e90012247c40a2dec31e1"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_MOVIE_WEB_URL = "https://www.themoviedb.org/movie/"
KOBIS_BASE_URL = "http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

# 데이터베이스 설정
DB_NAME = 'movies.db'

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 영화 정보 테이블 (상세 정보 포함)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            original_title TEXT,
            release_date TEXT,
            genre_ids TEXT,
            overview TEXT,
            poster_path TEXT,
            director TEXT,
            actors TEXT,
            runtime INTEGER
        )
    ''')
    
    # 사용자 관람 기록 테이블 (상세 정보 포함)
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
    
    # 보고싶어요 목록 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishlist_movies (
            wishlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            added_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# TMDB API 함수들
def search_movies(query):
    """TMDB에서 영화 검색"""
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "ko-KR"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"영화 검색 중 오류 발생: {e}")
        return []

def search_movies_by_director(director_name):
    """TMDB에서 감독으로 영화 검색"""
    # 먼저 감독 정보 검색
    person_url = f"{TMDB_BASE_URL}/search/person"
    person_params = {
        "api_key": TMDB_API_KEY,
        "query": director_name,
        "language": "ko-KR"
    }
    
    try:
        person_response = requests.get(person_url, params=person_params)
        person_response.raise_for_status()
        people = person_response.json().get("results", [])
        
        movies = []
        for person in people[:3]:  # 상위 3명의 인물만 확인
            if person.get("known_for_department") == "Directing":
                # 해당 감독의 영화 목록 가져오기
                credits_url = f"{TMDB_BASE_URL}/person/{person['id']}/movie_credits"
                credits_params = {
                    "api_key": TMDB_API_KEY,
                    "language": "ko-KR"
                }
                
                credits_response = requests.get(credits_url, params=credits_params)
                credits_response.raise_for_status()
                credits_data = credits_response.json()
                
                # 감독으로 참여한 영화들만 필터링
                director_movies = [
                    movie for movie in credits_data.get("crew", [])
                    if movie.get("job") == "Director"
                ]
                
                # 개봉일 기준으로 정렬 (최신순)
                director_movies.sort(key=lambda x: x.get("release_date", ""), reverse=True)
                movies.extend(director_movies[:10])  # 각 감독당 최대 10개
        
        # 중복 제거 (같은 영화 ID)
        seen_ids = set()
        unique_movies = []
        for movie in movies:
            if movie["id"] not in seen_ids:
                unique_movies.append(movie)
                seen_ids.add(movie["id"])
        
        return unique_movies[:20]  # 최대 20개 반환
        
    except requests.exceptions.RequestException as e:
        st.error(f"감독 검색 중 오류 발생: {e}")
        return []

def get_movie_details(tmdb_id):
    """TMDB에서 영화 상세 정보 가져오기"""
    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "ko-KR",
        "append_to_response": "credits"
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
        
        # 배우 정보 추출 (주연 3명)
        actors = ", ".join([cast.get("name") for cast in details.get("credits", {}).get("cast", [])[:3]])
        if not actors:
            actors = "정보 없음"
        
        # 한국어 제목 우선 사용, 없으면 원제 사용
        korean_title = details.get("title")
        original_title = details.get("original_title")
        
        # 한국어 제목이 원제와 같거나 없으면 원제 사용
        display_title = korean_title if korean_title and korean_title != original_title else original_title
        
        return {
            "tmdb_id": details.get("id"),
            "title": display_title,
            "original_title": original_title,
            "release_date": details.get("release_date"),
            "genre_ids": ",".join(str(g["id"]) for g in details.get("genres", [])),
            "overview": details.get("overview"),
            "poster_path": details.get("poster_path"),
            "director": director,
            "actors": actors,
            "runtime": details.get("runtime"),
            "tmdb_web_url": f"{TMDB_MOVIE_WEB_URL}{details.get('id')}"
        }
    except requests.exceptions.RequestException as e:
        st.error(f"영화 상세 정보 가져오는 중 오류 발생: {e}")
        return None

def get_genre_names(genre_ids_str):
    """TMDB 장르 ID를 장르 이름으로 변환"""
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

# KOFIC API - 박스오피스
def get_kobis_box_office(target_date=None):
    """KOBIS API에서 박스오피스 순위 가져오기"""
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    else:
        target_date = target_date.strftime('%Y%m%d')
    
    params = {
        "key": KOFIC_API_KEY,
        "targetDt": target_date
    }
    try:
        response = requests.get(KOBIS_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        box_office_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        
        # TMDB 포스터 정보 추가
        movies_with_posters = []
        for movie in box_office_list:
            tmdb_search_results = search_movies(movie.get('movieNm'))
            poster_path = None
            tmdb_id = None
            if tmdb_search_results:
                poster_path = tmdb_search_results[0].get('poster_path')
                tmdb_id = tmdb_search_results[0].get('id')
            
            movies_with_posters.append({
                "rank": movie.get('rank'),
                "title": movie.get('movieNm'),
                "openDt": movie.get('openDt'),
                "audiAcc": movie.get('audiAcc'),
                "poster_path": poster_path,
                "tmdb_id": tmdb_id
            })
        return movies_with_posters, target_date
    except requests.exceptions.RequestException as e:
        st.error(f"박스오피스 순위 가져오는 중 오류 발생: {e}")
        return [], target_date

# 데이터베이스 함수들
def insert_movie_and_record(movie_details, watch_record):
    """영화 정보와 관람 기록을 DB에 저장"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 영화 정보 저장 (중복 체크)
        cursor.execute('SELECT id FROM movies WHERE tmdb_id = ?', (movie_details['tmdb_id'],))
        movie_id_in_db = cursor.fetchone()
        
        if movie_id_in_db:
            movie_id = movie_id_in_db[0]
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
        
        # 중복 기록 체크 (같은 영화, 같은 날짜)
        cursor.execute('''
            SELECT record_id FROM user_watch_records 
            WHERE movie_id = ? AND watch_date = ?
        ''', (movie_id, watch_record['watch_date']))
        
        existing_record = cursor.fetchone()
        if existing_record:
            st.warning(f"⚠️ '{movie_details['title']}'는 {watch_record['watch_date']}에 이미 기록되어 있습니다!")
            st.info("💡 같은 영화를 다시 보셨다면 다른 날짜로 기록해주세요.")
            return
        
        # 관람 기록 저장
        cursor.execute('''
            INSERT INTO user_watch_records (movie_id, watch_date, my_rating, my_review, watch_method, watch_method_detail)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            movie_id, watch_record['watch_date'], watch_record['my_rating'],
            watch_record['my_review'], watch_record['watch_method'], watch_record['watch_method_detail']
        ))
        
        conn.commit()
        st.success(f"'{movie_details['title']}' 관람 기록을 저장했습니다!")
        
    except sqlite3.Error as e:
        st.error(f"❌ 데이터베이스 오류: {e}")
        conn.rollback()
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류: {e}")
    finally:
        conn.close()

def update_watch_record_review(record_id, new_review):
    """관람 기록의 감상평 업데이트"""
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

def delete_watch_record(record_id):
    """관람 기록 삭제"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM user_watch_records WHERE record_id = ?', (record_id,))
        conn.commit()
        st.success("관람 기록이 삭제되었습니다!")
    except sqlite3.Error as e:
        st.error(f"기록 삭제 중 오류 발생: {e}")
    finally:
        conn.close()

def get_all_watch_records():
    """모든 관람 기록과 영화 정보 가져오기"""
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
            m.tmdb_id,
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
        df['day_of_week'] = df['watch_date'].dt.strftime('%A')
        df['tmdb_web_url'] = df['tmdb_id'].apply(lambda x: f"{TMDB_MOVIE_WEB_URL}{x}" if x else "#")
    return df

def get_all_previous_locations():
    """이전에 입력했던 모든 관람 장소 목록 (사용 빈도순)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT watch_method_detail, COUNT(*) as count
        FROM user_watch_records 
        WHERE watch_method_detail IS NOT NULL AND watch_method_detail != '' 
        GROUP BY watch_method_detail
        ORDER BY count DESC, watch_method_detail
    """)
    locations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return locations

def determine_watch_method(location_detail):
    """관람 장소 텍스트를 보고 자동으로 방식 판단"""
    location_lower = location_detail.lower()
    
    # 영화관 키워드
    cinema_keywords = ['cgv', '메가박스', '롯데시네마', '영화관', '시네마', '극장']
    # OTT 키워드
    ott_keywords = ['넷플릭스', '왓챠', '티빙', '웨이브', '쿠팡플레이', '디즈니플러스', '아마존프라임', 'netflix', 'watcha', 'tving', 'wavve', 'disney', 'amazon', 'youtube', '유튜브']
    
    # 영화관 판단
    for keyword in cinema_keywords:
        if keyword in location_lower:
            return "영화관"
    
    # OTT 판단
    for keyword in ott_keywords:
        if keyword in location_lower:
            return "OTT"
    
    # 기본값은 기타
    return "기타"

def get_user_preferences():
    """사용자의 영화 취향 분석"""
    conn = sqlite3.connect(DB_NAME)
    
    # 전체 영화 수 계산
    total_movies_query = '''
        SELECT COUNT(*) as total_count
        FROM user_watch_records r
        JOIN movies m ON r.movie_id = m.id
    '''
    total_movies_df = pd.read_sql_query(total_movies_query, conn)
    total_movies = total_movies_df['total_count'].iloc[0] if not total_movies_df.empty else 0
    
    # 선호 장르 분석 (평점 4점 이상)
    query = '''
        SELECT m.genre_ids, r.my_rating
        FROM user_watch_records r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.my_rating >= 4 AND m.genre_ids IS NOT NULL
    '''
    df = pd.read_sql_query(query, conn)
    
    # 선호 감독 분석
    director_query = '''
        SELECT m.director, AVG(r.my_rating) as avg_rating, COUNT(*) as count
        FROM user_watch_records r
        JOIN movies m ON r.movie_id = m.id
        WHERE m.director IS NOT NULL AND m.director != '정보 없음'
        GROUP BY m.director
        HAVING avg_rating >= 4 AND count >= 2
        ORDER BY avg_rating DESC, count DESC
    '''
    directors_df = pd.read_sql_query(director_query, conn)
    
    conn.close()
    
    # 선호 장르 추출
    preferred_genres = []
    if not df.empty:
        for genre_ids in df['genre_ids']:
            if genre_ids:
                genres = genre_ids.split(',')
                preferred_genres.extend([int(g) for g in genres if g.strip().isdigit()])
    
    # 가장 선호하는 장르 TOP 3
    from collections import Counter
    genre_counter = Counter(preferred_genres)
    top_genres = [genre_id for genre_id, count in genre_counter.most_common(3)]
    
    # 선호 감독 TOP 3
    top_directors = directors_df['director'].head(3).tolist() if not directors_df.empty else []
    
    return {
        'preferred_genres': top_genres,
        'preferred_directors': top_directors,
        'total_movies': total_movies
    }

def get_tmdb_recommendations(preferences):
    """TMDB API를 사용한 영화 추천"""
    recommendations = []
    
    # 선호 장르 기반 추천
    if preferences['preferred_genres']:
        for genre_id in preferences['preferred_genres'][:2]:  # 상위 2개 장르만
            url = f"{TMDB_BASE_URL}/discover/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "ko-KR",
                "sort_by": "vote_average.desc",
                "vote_count.gte": 100,
                "with_genres": genre_id,
                "page": 1
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                results = response.json().get("results", [])
                recommendations.extend(results[:3])  # 각 장르당 3개씩
            except requests.exceptions.RequestException:
                continue
    
    # 인기 영화 추천 (취향 정보가 부족할 때)
    if len(recommendations) < 5:
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "ko-KR",
            "page": 1
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            recommendations.extend(results[:10])
        except requests.exceptions.RequestException:
            pass
    
    # 중복 제거 및 이미 본 영화 제외
    seen_movies = get_watched_movie_titles()
    unique_recommendations = []
    seen_ids = set()
    
    for movie in recommendations:
        if (movie['id'] not in seen_ids and 
            movie['title'] not in seen_movies and
            len(unique_recommendations) < 10):
            unique_recommendations.append(movie)
            seen_ids.add(movie['id'])
    
    return unique_recommendations

def get_watched_movie_titles():
    """이미 본 영화 제목 목록"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT title FROM movies")
    watched_titles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return watched_titles

def get_movies_by_period(start_date, end_date):
    """특정 기간의 영화 기록 가져오기"""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT
            r.record_id,
            m.title,
            m.director,
            m.genre_ids,
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

def add_to_wishlist(movie_details, notes=""):
    """보고싶어요 목록에 추가"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 영화 정보 저장 (중복 체크)
        cursor.execute('SELECT id FROM movies WHERE tmdb_id = ?', (movie_details['tmdb_id'],))
        movie_id_in_db = cursor.fetchone()
        
        if movie_id_in_db:
            movie_id = movie_id_in_db[0]
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
        
        # 이미 위시리스트에 있는지 확인
        cursor.execute('SELECT wishlist_id FROM wishlist_movies WHERE movie_id = ?', (movie_id,))
        if cursor.fetchone():
            st.warning(f"'{movie_details['title']}'는 이미 보고싶어요 목록에 있습니다!")
            return
        
        # 위시리스트에 추가
        cursor.execute('''
            INSERT INTO wishlist_movies (movie_id, added_date, notes)
            VALUES (?, ?, ?)
        ''', (movie_id, datetime.now().strftime('%Y-%m-%d'), notes))
        
        conn.commit()
        st.success(f"'{movie_details['title']}'를 보고싶어요 목록에 추가했습니다!")
        
    except sqlite3.Error as e:
        st.error(f"❌ 데이터베이스 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_wishlist_movies():
    """보고싶어요 목록 가져오기"""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT
            w.wishlist_id,
            m.title,
            m.original_title,
            m.poster_path,
            m.genre_ids,
            m.director,
            m.actors,
            m.runtime,
            m.tmdb_id,
            m.release_date,
            m.overview,
            w.added_date,
            w.notes
        FROM wishlist_movies w
        JOIN movies m ON w.movie_id = m.id
        ORDER BY w.added_date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['added_date'] = pd.to_datetime(df['added_date'])
        df['genre_names'] = df['genre_ids'].apply(get_genre_names)
        df['tmdb_web_url'] = df['tmdb_id'].apply(lambda x: f"{TMDB_MOVIE_WEB_URL}{x}" if x else "#")
    return df

def remove_from_wishlist(wishlist_id):
    """보고싶어요 목록에서 제거"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM wishlist_movies WHERE wishlist_id = ?', (wishlist_id,))
        conn.commit()
        st.success("보고싶어요 목록에서 제거했습니다!")
    except sqlite3.Error as e:
        st.error(f"제거 중 오류 발생: {e}")
    finally:
        conn.close()

# Streamlit 앱 설정
st.set_page_config(
    page_title="🎬 나만의 영화 데이터베이스",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DB 초기화
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# CSS 스타일링 - 깔끔한 디자인
st.markdown("""
<style>
    .movie-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .box-office-item {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin: 1.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .box-office-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .box-office-rank {
        background: #f8f9fa;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-weight: bold;
        text-align: left;
        font-size: 1.2rem;
        border-left: 4px solid #007bff;
    }
    .movie-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 6px;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    .section-divider {
        border-top: 2px solid #e9ecef;
        margin: 2rem 0;
    }
    .poster-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* 데이터프레임 스타일 개선 */
    .stDataFrame {
        font-family: 'Malgun Gothic', sans-serif;
    }
    .stDataFrame td {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }
    .stDataFrame th {
        background-color: #f8f9fa;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바 메뉴
st.sidebar.title("🎬 영화 DB 관리")

# 모든 메뉴를 한 번에 표시 (토글 없이)
st.sidebar.markdown("### 📋 메뉴")
if st.sidebar.button("📝 영화 기록하기", use_container_width=True):
    st.session_state.current_page = "영화 기록하기"
if st.sidebar.button("🏆 박스오피스 순위", use_container_width=True):
    st.session_state.current_page = "박스오피스 순위"
if st.sidebar.button("📚 나의 영화 목록", use_container_width=True):
    st.session_state.current_page = "나의 영화 목록"
if st.sidebar.button("💖 보고싶어요", use_container_width=True):
    st.session_state.current_page = "보고싶어요"

if st.sidebar.button("📅 월말 결산", use_container_width=True):
    st.session_state.current_page = "월말 결산"
if st.sidebar.button("🎊 연말 결산", use_container_width=True):
    st.session_state.current_page = "연말 결산"
if st.sidebar.button("🎯 영화 추천", use_container_width=True):
    st.session_state.current_page = "영화 추천"

# 현재 페이지 상태 관리
if 'current_page' not in st.session_state:
    st.session_state.current_page = "영화 기록하기"

menu = st.session_state.current_page

# 영화 기록하기 페이지
if menu == "영화 기록하기":
    st.title("📝 영화 기록하기")
    st.markdown("취향을 기록하고 추천 받으세요")
    
    # 보고싶어요 목록에서 선택된 영화가 있는 경우
    if 'selected_movie_for_record' in st.session_state:
        selected_movie = st.session_state.selected_movie_for_record
        st.info(f"� 보고싶어 요 목록에서 선택: {selected_movie['title']}")
        
        movie_details = get_movie_details(selected_movie['id'])
        if movie_details:
            with st.form("selected_movie_record_form"):
                st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                
                # 영화 정보 표시
                col1, col2 = st.columns([1, 2])
                with col1:
                    if movie_details['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w300{movie_details['poster_path']}")
                
                with col2:
                    st.write(f"**제목:** {movie_details['title']}")
                    st.write(f"**개봉일:** {movie_details['release_date']}")
                    st.write(f"**감독:** {movie_details['director']}")
                    st.write(f"**주연:** {movie_details['actors']}")
                    st.write(f"**장르:** {get_genre_names(movie_details['genre_ids'])}")
                    st.write(f"**러닝타임:** {movie_details['runtime']}분" if movie_details['runtime'] else "**러닝타임:** 정보 없음")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 관람 정보 입력
                col1, col2 = st.columns(2)
                with col1:
                    watch_date = st.date_input("📅 관람일", datetime.now())
                with col2:
                    my_rating = st.slider("⭐ 나의 평점 (0.5-5.0점)", 0.5, 5.0, 3.0, step=0.5)
                
                my_review = st.text_area("한 줄 감상평", placeholder="이 영화에 대한 감상을 적어주세요...")
                
                # 관람 장소 입력
                all_previous_locations = get_all_previous_locations()
                watch_method_detail = st.text_input(
                    "관람 장소", 
                    placeholder="예: CGV 동수원점, 넷플릭스, 집, 친구집"
                )
                
                if all_previous_locations:
                    st.write("💡 이전에 입력한 장소 중 선택:")
                    selected_location = st.selectbox(
                        "이전 장소 선택 (선택사항)", 
                        ["직접 입력"] + all_previous_locations[:10],
                        key="selected_location_select"
                    )
                    if selected_location != "직접 입력":
                        watch_method_detail = selected_location
                
                # 장소 유형 자동 판단
                if watch_method_detail:
                    watch_method = determine_watch_method(watch_method_detail)
                else:
                    watch_method = None
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 기록 저장하기", type="primary"):
                        if not watch_method_detail or watch_method_detail.strip() == "":
                            st.warning("관람 장소를 입력해주세요.")
                        else:
                            watch_record = {
                                "watch_date": watch_date.strftime('%Y-%m-%d'),
                                "my_rating": my_rating,
                                "my_review": my_review,
                                "watch_method": watch_method,
                                "watch_method_detail": watch_method_detail
                            }
                            insert_movie_and_record(movie_details, watch_record)
                            # 보고싶어요 목록에서 제거
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM wishlist_movies WHERE movie_id = (SELECT id FROM movies WHERE tmdb_id = ?)', (movie_details['tmdb_id'],))
                            conn.commit()
                            conn.close()
                            # 선택된 영화 정보 제거
                            del st.session_state.selected_movie_for_record
                            st.rerun()
                
                with col_cancel:
                    if st.form_submit_button("취소", type="secondary"):
                        del st.session_state.selected_movie_for_record
                        st.rerun()
        
        st.markdown("---")

    # 검색 옵션 선택
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 검색어를 입력하세요:", placeholder="예: 기생충, 봉준호, 크리스토퍼 놀란...")
    with col2:
        search_type = st.selectbox("검색 방식", ["전체 검색", "제목으로 검색", "감독으로 검색"])

    if search_query:
        if search_type == "전체 검색":
            st.markdown(f"### 🎯 '{search_query}' 전체 검색 결과")
            
            # 제목 검색 결과
            title_results = search_movies(search_query)
            # 감독 검색 결과
            director_results = search_movies_by_director(search_query)
            
            # 결과 합치기 (중복 제거)
            search_results = []
            seen_ids = set()
            
            # 제목 검색 결과를 먼저 추가 (더 정확한 결과)
            for movie in title_results:
                if movie['id'] not in seen_ids:
                    search_results.append(movie)
                    seen_ids.add(movie['id'])
            
            # 감독 검색 결과 추가
            for movie in director_results:
                if movie['id'] not in seen_ids:
                    search_results.append(movie)
                    seen_ids.add(movie['id'])
            
            # 결과 개수 표시
            if title_results and director_results:
                st.info(f"📽️ 제목 검색: {len(title_results)}개, 🎬 감독 검색: {len(director_results)}개 (중복 제거 후 총 {len(search_results)}개)")
            elif title_results:
                st.info(f"📽️ 제목 검색에서만 {len(title_results)}개 발견")
            elif director_results:
                st.info(f"🎬 감독 검색에서만 {len(director_results)}개 발견")
                
        elif search_type == "제목으로 검색":
            st.markdown(f"### 🎯 '{search_query}' 제목 검색 결과")
            search_results = search_movies(search_query)
        else:
            st.markdown(f"### 🎯 '{search_query}' 감독 검색 결과")
            search_results = search_movies_by_director(search_query)
        
        if search_results:
            # 검색 결과를 바로 스크롤 가능한 형태로 표시
            for i, movie in enumerate(search_results[:10]):
                with st.container():
                    st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        if movie['poster_path']:
                            st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                        else:
                            st.write("🎬 포스터 없음")
                    
                    with col2:
                        # 한국어 제목 우선 표시
                        title = movie['title']
                        original_title = movie.get('original_title', '')
                        
                        if original_title and title != original_title:
                            st.subheader(title)
                            st.caption(f"원제: {original_title}")
                        else:
                            st.subheader(title)
                        
                        st.write(f"📅 개봉년도: {movie['release_date'][:4] if movie['release_date'] else 'N/A'}")
                        st.write(f"📝 줄거리: {movie.get('overview', '정보 없음')[:100]}...")
                    
                    with col3:
                        if st.button("기록하기", key=f"record_{movie['id']}", type="primary"):
                            # 영화 기록 폼을 바로 아래에 표시
                            movie_details = get_movie_details(movie['id'])
                            if movie_details:
                                st.session_state[f'show_form_{movie["id"]}'] = True
                                st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 해당 영화의 기록 폼이 활성화된 경우 표시
                    if st.session_state.get(f'show_form_{movie["id"]}', False):
                        st.subheader(f"📝 '{movie['title']}' 관람 기록 입력")
                        movie_details = get_movie_details(movie['id'])
                        
                        if movie_details:
                            with st.form("watch_record_form"):
                                st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                                
                                # 영화 정보 표시
                                col1, col2 = st.columns([1, 2])
                                with col1:
                                    if movie_details['poster_path']:
                                        st.image(f"https://image.tmdb.org/t/p/w300{movie_details['poster_path']}")
                                
                                with col2:
                                    st.write(f"**제목:** {movie_details['title']}")
                                    st.write(f"**개봉일:** {movie_details['release_date']}")
                                    st.write(f"**감독:** {movie_details['director']}")
                                    st.write(f"**주연:** {movie_details['actors']}")
                                    st.write(f"**장르:** {get_genre_names(movie_details['genre_ids'])}")
                                    st.write(f"**러닝타임:** {movie_details['runtime']}분" if movie_details['runtime'] else "**러닝타임:** 정보 없음")
                                

                                
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # 관람 정보 입력
                                col1, col2 = st.columns(2)
                                with col1:
                                    watch_date = st.date_input("📅 관람일", datetime.now())
                                with col2:
                                    my_rating = st.slider("⭐ 나의 평점 (0.5-5.0점)", 0.5, 5.0, 3.0, step=0.5)
                                
                                my_review = st.text_area("한 줄 감상평", placeholder="이 영화에 대한 감상을 적어주세요...")
                                
                                # 관람 장소 입력
                                all_previous_locations = get_all_previous_locations()
                                
                                # 모든 경우에 텍스트 입력 필드 표시
                                watch_method_detail = st.text_input(
                                    "관람 장소", 
                                    placeholder="예: CGV 동수원점, 넷플릭스, 집, 친구집"
                                )
                                
                                # 이전 장소들을 선택 옵션으로 표시
                                if all_previous_locations:
                                    st.write("💡 이전에 입력한 장소 중 선택:")
                                    selected_location = st.selectbox(
                                        "이전 장소 선택 (선택사항)", 
                                        ["직접 입력"] + all_previous_locations[:10],
                                        key="location_select"
                                    )
                                    if selected_location != "직접 입력":
                                        watch_method_detail = selected_location
                                
                                # 장소 유형 자동 판단
                                if watch_method_detail:
                                    watch_method = determine_watch_method(watch_method_detail)
                                else:
                                    watch_method = None
                                
                                # 최종 저장 버튼
                                if st.form_submit_button("💾 기록 저장하기", type="primary"):
                                    if not watch_method_detail or watch_method_detail.strip() == "":
                                        st.warning("관람 장소를 입력해주세요.")
                                    else:
                                        watch_record = {
                                            "watch_date": watch_date.strftime('%Y-%m-%d'),
                                            "my_rating": my_rating,
                                            "my_review": my_review,
                                            "watch_method": watch_method,
                                            "watch_method_detail": watch_method_detail
                                        }
                                        insert_movie_and_record(movie_details, watch_record)
                                        # 폼 숨기기
                                        st.session_state[f'show_form_{movie["id"]}'] = False
                                        st.rerun()
                        else:
                            st.error("영화 상세 정보를 가져올 수 없습니다.")
        else:
            st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")

# 박스오피스 순위 페이지
elif menu == "박스오피스 순위":
    st.title("🏆 박스오피스 순위")
    st.markdown("잠시 기다려주세요")
    
    # 날짜 선택 기능 추가
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_date = st.date_input(
            "📅 박스오피스 날짜 선택", 
            value=datetime.now() - timedelta(days=1),
            max_value=datetime.now() - timedelta(days=1),
            help="박스오피스 데이터는 전날까지만 제공됩니다"
        )
    with col2:
        if st.button("🔄 새로고침", type="secondary"):
            st.rerun()
    
    box_office_movies, target_date_str = get_kobis_box_office(selected_date)
    
    if box_office_movies:
        # 선택된 날짜 표시
        display_date = datetime.strptime(target_date_str, '%Y%m%d').strftime('%Y년 %m월 %d일')
        st.subheader(f"📅 {display_date} 박스오피스 TOP 10")
        
        for movie in box_office_movies[:10]:
            with st.container():
                st.markdown('<div class="box-office-item">', unsafe_allow_html=True)
                
                st.markdown(f'<div class="box-office-rank">{movie["rank"]}위 - {movie["title"]}</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown('<div class="poster-container">', unsafe_allow_html=True)
                    if movie['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w500{movie['poster_path']}", use_container_width=True)
                    else:
                        st.markdown('<div style="text-align: center; padding: 2rem; background: #f0f0f0; border-radius: 8px;">🎬<br>포스터 없음</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="movie-info">', unsafe_allow_html=True)
                    st.markdown(f"**개봉일:** {movie['openDt'] if movie['openDt'] else '2025-07-23'}")
                    st.markdown(f"**누적 관객수:** {int(movie['audiAcc']):,}명")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 버튼들을 포스터 옆에 배치
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        naver_url = f"https://search.naver.com/search.naver?query={movie['title']}+예매하기"
                        st.link_button("🎫 예매하기", naver_url, use_container_width=True)
                    
                    with col_btn2:
                        watcha_url = f"https://pedia.watcha.com/ko-KR/search?query={movie['title']}"
                        st.link_button("ℹ️ 영화 정보", watcha_url, use_container_width=True)
                    
                    with col_btn3:
                        if movie['tmdb_id'] and st.button("보고싶어요 💖", key=f"wishlist_box_{movie['rank']}", use_container_width=True):
                            movie_details = get_movie_details(movie['tmdb_id'])
                            if movie_details:
                                add_to_wishlist(movie_details, notes="박스오피스에서 추가")
                                st.rerun()
                
                # 영화 기록 폼
                with st.expander(f"📝 '{movie['title']}' 기록하기"):
                    if movie['tmdb_id']:
                        movie_details = get_movie_details(movie['tmdb_id'])
                        if movie_details:
                            with st.form(f"box_office_record_{movie['rank']}"):
                                st.markdown(f"**🎬 제목:** {movie_details['title']}")
                                st.markdown(f"**🎭 감독:** {movie_details['director']}")
                                st.markdown(f"**⭐ 주연:** {movie_details['actors']}")
                                st.markdown(f"**🎪 장르:** {get_genre_names(movie_details['genre_ids'])}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    watch_date = st.date_input("📅 관람일", datetime.now(), key=f"box_date_{movie['rank']}")
                                with col2:
                                    my_rating = st.slider("⭐ 나의 평점 (0.5-5.0점)", 0.5, 5.0, 3.0, step=0.5, key=f"box_rating_{movie['rank']}")
                                
                                my_review = st.text_area("한 줄 감상평", key=f"box_review_{movie['rank']}", placeholder="이 영화에 대한 감상을 적어주세요...")
                                
                                # 관람 장소 입력
                                all_previous_locations = get_all_previous_locations()
                                
                                # 모든 경우에 텍스트 입력 필드 표시
                                watch_method_detail = st.text_input(
                                    "관람 장소", 
                                    placeholder="예: CGV 동수원점, 넷플릭스, 집, 친구집",
                                    key=f"box_location_input_{movie['rank']}"
                                )
                                
                                # 이전 장소들을 선택 옵션으로 표시
                                if all_previous_locations:
                                    st.write("💡 이전에 입력한 장소 중 선택:")
                                    selected_location = st.selectbox(
                                        "이전 장소 선택 (선택사항)", 
                                        ["직접 입력"] + all_previous_locations[:10],
                                        key=f"box_location_select_{movie['rank']}"
                                    )
                                    if selected_location != "직접 입력":
                                        watch_method_detail = selected_location
                                
                                # 장소 유형 자동 판단
                                if watch_method_detail:
                                    watch_method = determine_watch_method(watch_method_detail)
                                else:
                                    watch_method = None
                                
                                submitted = st.form_submit_button("💾 기록 저장하기", type="primary")
                                if submitted:
                                    if not watch_method_detail or watch_method_detail.strip() == "":
                                        st.warning("관람 장소를 입력해주세요.")
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
                        else:
                            st.warning("❌ 영화 상세 정보를 가져올 수 없습니다.")
                    else:
                        st.info("ℹ️ TMDB 정보가 없어 기록할 수 없습니다.")
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ 박스오피스 순위를 가져올 수 없습니다. API 키를 확인해주세요.")

# 나의 영화 목록
elif menu == "나의 영화 목록":
    st.title("📚 나의 영화 목록")
    st.markdown("지금까지 본 영화들을 확인해보세요!")

    df_records = get_all_watch_records()

    if not df_records.empty:
        # 월별로 그룹핑하여 표시
        for year_month, group_df in df_records.groupby('year_month'):
            st.subheader(f"📅 {year_month}")
            
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
                        st.subheader(row['title'])
                        st.write(f"**관람일:** {row['watch_date'].strftime('%Y년 %m월 %d일')} ({row['day_of_week']})")
                        rating = row['my_rating'] if row['my_rating'] else 0
                        # 0.5 단위 별점 표시
                        full_stars = int(rating)
                        half_star = 1 if (rating - full_stars) >= 0.5 else 0
                        star_display = '⭐' * full_stars + ('⭐' * half_star if half_star else '')
                        st.write(f"**나의 평점:** {star_display} ({rating}점)")
                        st.write(f"**감독:** {row['director']}")
                        st.write(f"**관람 장소:** {row['watch_method_detail']}")
                        
                        # 감상평 수정 기능
                        current_review = row['my_review'] if row['my_review'] else ""
                        new_review_key = f"review_{row['record_id']}"
                        updated_review = st.text_area("감상평", value=current_review, key=new_review_key, placeholder="감상평을 입력해주세요...")
                        
                        col_save, col_delete = st.columns([1, 1])
                        with col_save:
                            if st.button("감상평 저장", key=f"save_{row['record_id']}"):
                                if updated_review != current_review:
                                    update_watch_record_review(row['record_id'], updated_review)
                                    st.rerun()
                        
                        with col_delete:
                            if st.button("기록 삭제", key=f"delete_{row['record_id']}", type="secondary"):
                                if st.session_state.get(f"confirm_delete_{row['record_id']}", False):
                                    delete_watch_record(row['record_id'])
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{row['record_id']}"] = True
                                    st.warning("한 번 더 클릭하면 삭제됩니다!")
                                    st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("아직 기록된 영화가 없습니다. 메인 페이지에서 영화를 기록해보세요!")

# 월말 결산
elif menu == "월말 결산":
    st.title("📅 월말 결산")
    st.markdown("이달의 영화 시청 기록을 확인해보세요!")

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("📅 년도", range(2020, 2026), index=5)
    with col2:
        selected_month = st.selectbox("📅 월", range(1, 13), index=datetime.now().month-1)

    start_date = f"{selected_year}-{selected_month:02d}-01"
    if selected_month == 12:
        end_date = f"{selected_year+1}-01-01"
    else:
        end_date = f"{selected_year}-{selected_month+1:02d}-01"

    monthly_movies = get_movies_by_period(start_date, end_date)

    if not monthly_movies.empty:
        st.markdown(f"### 🎬 {selected_year}년 {selected_month}월 결산")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("이달의 영화 수", len(monthly_movies))
        with col2:
            st.metric("평균 평점", f"{monthly_movies['my_rating'].mean():.1f}")
        with col3:
            best_movie = monthly_movies.loc[monthly_movies['my_rating'].idxmax()]
            st.metric("이달의 베스트", best_movie['title'][:15])
        with col4:
            st.metric("최고 평점", monthly_movies['my_rating'].max())
        
        st.markdown("### 📋 이달의 영화 목록")
        # 컬럼명을 한글로 변경하고 표시 형식 개선
        display_df = monthly_movies[['title', 'director', 'genre_names', 'my_rating', 'watch_date', 'my_review']].copy()
        display_df.columns = ['영화 제목', '감독', '장르', '평점', '관람일', '감상평']
        display_df['관람일'] = pd.to_datetime(display_df['관람일']).dt.strftime('%m/%d')
        display_df['감상평'] = display_df['감상평'].fillna('').str[:30] + '...'  # 감상평 길이 제한
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        

# 연말 결산
elif menu == "연말 결산":
    st.title("🎊 연말 결산")
    st.markdown("올해의 영화 시청 기록을 총정리해보세요!")

    selected_year = st.selectbox("📅 년도 선택", range(2020, 2026), index=5)

    start_date = f"{selected_year}-01-01"
    end_date = f"{selected_year+1}-01-01"

    yearly_movies = get_movies_by_period(start_date, end_date)

    if not yearly_movies.empty:
        st.markdown(f"### 🎬 {selected_year}년 영화 결산")
        
        # 주요 지표들
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("올해 본 영화", f"{len(yearly_movies)}편")
        with col2:
            st.metric("평균 평점", f"{yearly_movies['my_rating'].mean():.1f}")
        with col3:
            hours = len(yearly_movies) * 2  # 평균 2시간으로 가정
            st.metric("영화 시청 시간", f"{hours}시간")
        with col4:
            genres = []
            for genre_list in yearly_movies['genre_names'].dropna():
                genres.extend([g.strip() for g in genre_list.split(', ')])
            most_genre = Counter(genres).most_common(1)[0][0] if genres else "없음"
            st.metric("최애 장르", most_genre)
        
        # 올해의 베스트 영화들
        st.subheader("🏆 올해의 베스트 영화")
        top_movies = yearly_movies.nlargest(5, 'my_rating')[['title', 'director', 'genre_names', 'my_rating', 'watch_date']].copy()
        top_movies.columns = ['영화 제목', '감독', '장르', '평점', '관람일']
        top_movies['관람일'] = pd.to_datetime(top_movies['관람일']).dt.strftime('%m/%d')
        st.dataframe(top_movies, use_container_width=True, hide_index=True)
        
        # 연간 장르 분석
        st.subheader("🎭 연간 장르 선호도")
        yearly_genres = yearly_movies['genre_names'].str.split(', ').explode()
        yearly_genre_counts = yearly_genres.value_counts().head(5)
        
        if not yearly_genre_counts.empty:
            if CHART_AVAILABLE:
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(yearly_genre_counts.index, yearly_genre_counts.values)
                ax.set_title('🎭 연간 장르 선호도', fontsize=16, pad=20)
                ax.set_xlabel('장르')
                ax.set_ylabel('영화 수')
                
                # x축 레이블을 가로로 표시
                plt.xticks(rotation=0)
                
                # 막대 위에 숫자 표시
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom')
                
                plt.tight_layout()
                st.pyplot(fig)
            else:
                # matplotlib이 없을 경우 데이터프레임으로 표시
                genre_df = pd.DataFrame({
                    '장르': yearly_genre_counts.index,
                    '영화 수': yearly_genre_counts.values
                })
                st.dataframe(genre_df, use_container_width=True, hide_index=True)
        
    else:
        st.info(f"📅 {selected_year}년에 시청한 영화가 없습니다.")

# 영화 추천
elif menu == "영화 추천":
    st.title("🎯 영화 추천 & 통계 분석")
    st.markdown("당신의 취향을 분석하고 맞춤 영화를 추천해드려요!")
    
    df_records = get_all_watch_records()
    
    if df_records.empty:
        st.info("📝 영화를 몇 편 기록하신 후에 추천을 받아보세요!")
        st.markdown("영화 기록하기 페이지에서 영화를 기록하면 취향 분석이 가능해집니다.")
    else:
        # 탭으로 구분
        tab1, tab2 = st.tabs(["📊 통계 분석", "🎬 영화 추천"])
        
        with tab1:
            st.subheader("📈 기본 통계")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-box">
                    <h3>{len(df_records)}</h3>
                    <p>총 영화 수</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-box">
                    <h3>{df_records['my_rating'].mean():.1f}</h3>
                    <p>평균 평점</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-box">
                    <h3>{df_records['my_rating'].max()}</h3>
                    <p>최고 평점</p>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                total_runtime = df_records['runtime'].sum() if df_records['runtime'].notna().any() else 0
                st.markdown(f"""
                <div class="metric-box">
                    <h3>{total_runtime}분</h3>
                    <p>총 시청 시간</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 장르별 선호도
            st.subheader("🎭 장르별 선호도")
            all_genres = df_records['genre_names'].str.split(', ').explode()
            genre_counts = all_genres.value_counts().head(5)
            
            if not genre_counts.empty:
                if CHART_AVAILABLE:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(genre_counts.index, genre_counts.values, color='skyblue')
                    ax.set_title('🎭 장르별 선호도', fontsize=16, pad=20)
                    ax.set_xlabel('장르')
                    ax.set_ylabel('영화 수')
                    
                    # x축 레이블을 가로로 표시
                    plt.xticks(rotation=0)
                    
                    # 막대 위에 숫자 표시
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    # matplotlib이 없을 경우 데이터프레임으로 표시
                    genre_df = pd.DataFrame({
                        '장르': genre_counts.index,
                        '영화 수': genre_counts.values
                    })
                    st.dataframe(genre_df, use_container_width=True, hide_index=True)
            
            # 관람 장소별 통계
            st.subheader("🏢 관람 장소별 통계")
            place_counts = df_records['watch_method_detail'].value_counts().head(5)
            
            if not place_counts.empty:
                if CHART_AVAILABLE:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(place_counts.index, place_counts.values, color='lightcoral')
                    ax.set_title('🏢 관람 장소별 통계', fontsize=16, pad=20)
                    ax.set_xlabel('관람 장소')
                    ax.set_ylabel('영화 수')
                    
                    # x축 레이블을 45도 각도로 표시 (장소명이 길 수 있으므로)
                    plt.xticks(rotation=45, ha='right')
                    
                    # 막대 위에 숫자 표시
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    # matplotlib이 없을 경우 데이터프레임으로 표시
                    place_df = pd.DataFrame({
                        '관람 장소': place_counts.index,
                        '영화 수': place_counts.values
                    })
                    st.dataframe(place_df, use_container_width=True, hide_index=True)
        
        with tab2:
            # 사용자 취향 분석
            preferences = get_user_preferences()
            # 취향 분석 결과 표시
            st.subheader("📊 당신의 영화 취향 분석")
        
            col1, col2 = st.columns(2)
            with col1:
                st.metric("기록한 영화 수", f"{preferences['total_movies']}편")
                
                if preferences['preferred_genres']:
                    st.write("**선호 장르:**")
                    for genre_id in preferences['preferred_genres']:
                        genre_name = get_genre_names(str(genre_id))
                        st.write(f"• {genre_name}")
            
            with col2:
                if preferences['preferred_directors']:
                    st.write("**선호 감독:**")
                    for director in preferences['preferred_directors']:
                        st.write(f"• {director}")
            
            st.markdown("---")
            
            # 추천 영화 가져오기
            st.subheader("🎬 맞춤 영화 추천")
            
            with st.spinner("취향에 맞는 영화를 찾고 있어요..."):
                recommendations = get_tmdb_recommendations(preferences)
            
            if recommendations:
                st.markdown(f"**{len(recommendations)}개의 추천 영화를 찾았어요!**")
                
                for i, movie in enumerate(recommendations, 1):
                    with st.container():
                        st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if movie.get('poster_path'):
                                st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}", use_container_width=True)
                            else:
                                st.write("🎬 포스터 없음")
                        
                        with col2:
                            # 한국어 제목 우선 표시, 원제가 다르면 함께 표시
                            title = movie['title']
                            original_title = movie.get('original_title', '')
                            
                            if original_title and title != original_title:
                                st.subheader(f"{i}. {title}")
                                st.caption(f"원제: {original_title}")
                            else:
                                st.subheader(f"{i}. {title}")
                            
                            st.write(f"**개봉년도:** {movie['release_date'][:4] if movie.get('release_date') else 'N/A'}")
                            st.write(f"**평점:** ⭐ {movie.get('vote_average', 0):.1f}/10")
                            st.write(f"**줄거리:** {movie.get('overview', '정보 없음')[:150]}...")
                            
                            # 보고싶어요 버튼
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button(f"보고싶어요",  key=f"interested_{movie['id']}"):
                                    # 영화 상세 정보 가져와서 위시리스트에 추가
                                    movie_details = get_movie_details(movie['id'])
                                    if movie_details:
                                        add_to_wishlist(movie_details, notes="추천 영화에서 추가")
                                        st.rerun()
                            
                            with col_btn2:
                                # 더 자세한 정보 링크
                                naver_search = f"https://search.naver.com/search.naver?query={movie['title']}+영화"
                                st.link_button("🔍 더 알아보기", naver_search)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("추천할 영화를 찾지 못했어요. 잠시 후 다시 시도해주세요.")

# 보고싶어요 페이지
elif menu == "보고싶어요":
    st.title("💖  보고싶어요")
    st.markdown("언젠가 꼭 봐야 할 영화들을 관리해보세요")
    
    # 새 영화 추가 섹션
    with st.expander("➕ 새 영화 추가하기"):
        search_query = st.text_input("영화 제목을 검색하세요:", placeholder="예: 인터스텔라, 기생충...")
        
        if search_query:
            search_results = search_movies(search_query)
            if search_results:
                for movie in search_results[:5]:  # 상위 5개만 표시
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        if movie['poster_path']:
                            st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}", use_container_width=True)
                    with col2:
                        st.write(f"**{movie['title']}**")
                        st.write(f"개봉: {movie['release_date'][:4] if movie['release_date'] else 'N/A'}")
                        st.write(f"{movie.get('overview', '정보 없음')[:100]}...")
                    with col3:
                        if st.button("추가", key=f"add_wishlist_{movie['id']}"):
                            movie_details = get_movie_details(movie['id'])
                            if movie_details:
                                add_to_wishlist(movie_details, notes="직접 추가")
                                st.rerun()
    
    # 보고싶어요 목록 표시
    wishlist_df = get_wishlist_movies()
    
    if not wishlist_df.empty:
        st.subheader(f"📋 보고싶어요 목록 ({len(wishlist_df)}편)")
        

        
        for _, row in wishlist_df.iterrows():
            with st.container():
                st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if row['poster_path']:
                        st.image(f"https://image.tmdb.org/t/p/w300{row['poster_path']}", use_container_width=True)
                    else:
                        st.write("🎬 포스터 없음")
                
                with col2:
                    st.subheader(row['title'])
                    st.write(f"**개봉일:** {row['release_date']}")
                    st.write(f"**감독:** {row['director']}")
                    st.write(f"**장르:** {row['genre_names']}")
                    st.write(f"**러닝타임:** {row['runtime']}분" if row['runtime'] else "**러닝타임:** 정보 없음")
                    
                    if row['notes']:
                        st.write(f"**메모:** {row['notes']}")
                    
                    st.write(f"**추가일:** {row['added_date'].strftime('%Y-%m-%d')}")
                    st.write(f"**줄거리:** {row['overview'][:200]}..." if row['overview'] else "**줄거리:** 정보 없음")
                
                with col3:
                    # 기록하기 버튼 (관람 완료)
                    if st.button("기록하기", key=f"record_wishlist_{row['wishlist_id']}", type="primary"):
                        # 영화 기록 페이지로 이동하면서 해당 영화 정보 전달
                        st.session_state.selected_movie_for_record = {
                            'id': row['tmdb_id'],
                            'title': row['title'],
                            'poster_path': row['poster_path']
                        }
                        st.session_state.current_page = "영화 기록하기"
                        st.rerun()
                    
                    # 제거 버튼
                    if st.button("제거", key=f"remove_wishlist_{row['wishlist_id']}", type="secondary"):
                        remove_from_wishlist(row['wishlist_id'])
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("아직 보고싶은 영화가 없습니다. 위에서 영화를 추가해보세요!")

# 푸터
st.sidebar.markdown("---")
st.sidebar.markdown("**🎬 나만의 영화 데이터베이스**")
st.sidebar.markdown("TMDB & KOBIS API 사용")

if __name__ == "__main__":
    pass