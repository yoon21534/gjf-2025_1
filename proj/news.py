import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin, urlparse, parse_qs
import io
import json

class NaverEconomicNewsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://news.naver.com/'
        }
        self.base_url = "https://news.naver.com"
        
        self.press_political_stance = {
            "조선일보": "보수", "중앙일보": "보수", "동아일보": "보수",
            "한국경제": "보수", "매일경제": "보수", "서울경제": "보수",
            "한겨레": "진보", "경향신문": "진보", "오마이뉴스": "진보", "프레시안": "진보",
            "연합뉴스": "중도", "뉴스1": "중도", "뉴시스": "중도",
            "KBS": "중도", "MBC": "중도", "SBS": "중도", "YTN": "중도",
            "JTBC": "중도-진보", "채널A": "보수", "TV조선": "보수", "MBN": "보수",
            "파이낸셜뉴스": "중도", "이데일리": "중도", "아시아경제": "중도",
            "헤럴드경제": "중도", "뉴스핌": "중도", "머니투데이": "중도"
        }
        
    def get_economic_news_list(self, target_date=None, max_pages=1):
        """네이버 경제뉴스 목록 가져오기 - 단순하고 안정적인 방식"""
        if target_date is None:
            target_date = datetime.now()
            
        all_news = []
        
        # 가장 기본적인 네이버 경제 뉴스 URL들만 사용
        base_urls = [
            "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101",
            "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=101"
        ]
        
        for page in range(1, max_pages + 1):
            page_news = []
            
            for base_url in base_urls:
                try:
                    # 페이지 파라미터 추가
                    if page > 1:
                        url = f"{base_url}&page={page}"
                    else:
                        url = base_url
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    
                    if response.status_code != 200:
                        continue
                        
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 가장 일반적인 네이버 뉴스 구조 셀렉터들
                    selectors_to_try = [
                        'ul.type06_headline li',
                        'ul.type06 li',
                        '.newsflash_body li',
                        '.list_body ul li',
                        'li dt a',
                        'a[href*="news.naver.com/main/read"]'
                    ]
                    
                    articles_found = []
                    for selector in selectors_to_try:
                        elements = soup.select(selector)
                        if elements and len(elements) > 0:
                            articles_found = elements
                            break
                    
                    if not articles_found:
                        # 마지막 수단: 모든 네이버 뉴스 링크 수집
                        all_links = soup.find_all('a', href=re.compile(r'news\.naver\.com/main/read'))
                        if all_links:
                            articles_found = [link.parent for link in all_links if link.parent]
                    
                    # 기사 정보 추출
                    for element in articles_found[:15]:  # 최대 15개만
                        try:
                            article_info = self._extract_simple_article_info(element)
                            if article_info:
                                page_news.append(article_info)
                        except Exception as e:
                            continue
                    
                    if page_news:
                        break
                    
                    time.sleep(1)
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"네트워크 오류: {str(e)}")
                    continue
                except Exception as e:
                    st.error(f"파싱 오류: {str(e)}")
                    continue
            
            all_news.extend(page_news)
            time.sleep(2)  # 페이지 간 딜레이
        
        # 중복 제거
        unique_news = []
        seen_urls = set()
        for news in all_news:
            if news['link'] not in seen_urls:
                seen_urls.add(news['link'])
                unique_news.append(news)
        
        return unique_news
    
    def _extract_simple_article_info(self, element):
        """단순하고 안정적인 기사 정보 추출"""
        try:
            # 링크 찾기
            link_tag = element.find('a') if element.name != 'a' else element
            if not link_tag or not link_tag.get('href'):
                return None
            
            href = link_tag.get('href')
            
            # URL 정규화
            if href.startswith('//'):
                link = 'https:' + href
            elif href.startswith('/'):
                link = self.base_url + href
            else:
                link = href
            
            # 네이버 뉴스 링크 검증
            if 'news.naver.com' not in link:
                return None
            
            # 제목 추출 - 여러 방법 시도
            title = ""
            if link_tag.get_text().strip():
                title = link_tag.get_text().strip()
            else:
                # 부모 요소에서 제목 찾기
                parent = element.parent if element.parent else element
                title_candidates = parent.find_all(['dt', 'h3', 'h4', 'span'])
                for candidate in title_candidates:
                    text = candidate.get_text().strip()
                    if len(text) > 10 and len(text) < 200:
                        title = text
                        break
            
            if not title or len(title) < 5:
                return None
            
            # 제목 정리
            title = re.sub(r'\s+', ' ', title).strip()
            title = re.sub(r'^[^\w가-힣]*', '', title)
            
            return {
                'title': title,
                'link': link,
                'press': "정보없음",
                'pub_time': "시간정보없음",
                'political_stance': "미분류"
            }
            
        except Exception as e:
            return None
    
    def filter_by_political_stance(self, news_list, allowed_stances):
        if "전체" in allowed_stances:
            return news_list
        return [news for news in news_list if news.get('political_stance', '미분류') in allowed_stances]
    
    def filter_by_keyword(self, news_list, keyword):
        if not keyword:
            return news_list
        keyword_lower = keyword.lower()
        return [news for news in news_list if keyword_lower in news['title'].lower()]
    
    def extract_article_content(self, article_url):
        """기사 본문 추출 - 안정적인 방식"""
        try:
            if not article_url or 'news.naver.com' not in article_url:
                return self._create_error_result("잘못된 URL", article_url)
            
            response = requests.get(article_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return self._create_error_result(f"HTTP {response.status_code} 오류", article_url)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 본문 추출 - 기본적인 셀렉터들만 사용
            content_selectors = [
                '#dic_area',
                '#articleBodyContents',
                '._article_body_contents',
                '.go_trans._article_content'
            ]
            
            content_area = None
            for selector in content_selectors:
                content_area = soup.select_one(selector)
                if content_area:
                    break
            
            if not content_area:
                return self._create_error_result("본문을 찾을 수 없음", article_url)
            
            # 불필요한 태그 제거
            for tag in content_area.select('script, style, .ad, .advertisement'):
                tag.decompose()
            
            content = content_area.get_text().strip()
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'\s+', ' ', content)
            
            if len(content) < 50:
                return self._create_error_result("본문이 너무 짧음", article_url)
            
            # 메타데이터 추출
            title = self._extract_title(soup)
            press = self._extract_press(soup)
            pub_time = self._extract_time(soup)
            
            return {
                'title': title,
                'content': content,
                'press': press,
                'pub_time': pub_time,
                'url': article_url
            }
            
        except Exception as e:
            return self._create_error_result(f"추출 오류: {str(e)}", article_url)
    
    def _extract_title(self, soup):
        selectors = ['#title_area span', '.media_end_head_headline', 'h2.end_tit', 'h1']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return "제목 없음"
    
    def _extract_press(self, soup):
        selectors = ['.media_end_head_top_logo img', '.press_logo img']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get('alt', '')
        return "언론사 정보 없음"
    
    def _extract_time(self, soup):
        selectors = ['.media_end_head_info_datestamp_time', '.t11']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return "시간 정보 없음"
    
    def _create_error_result(self, error_msg, url):
        return {
            'title': "추출 실패",
            'content': f"기사 추출 중 오류가 발생했습니다: {error_msg}",
            'press': "오류",
            'pub_time': "오류",
            'url': url
        }
    
    def extract_keywords(self, content, title):
        economic_keywords = [
            '금리', '인플레이션', '물가', 'GDP', '성장률', '실업률', '환율',
            '주식', '코스피', '코스닥', '부동산', '아파트', '전세', '매매',
            '수출', '수입', '무역', '경상수지', '국채', '회사채', '기준금리',
            '한국은행', '기업실적', '매출', '영업이익', '순이익', '투자',
            '소비', '내수', '경기', '침체', '회복', '상승', '하락', '반도체',
            '자동차', '철강', '조선', '석유화학', '바이오', 'IT', '통신'
        ]
        
        text = title + " " + content
        found_keywords = []
        
        for keyword in economic_keywords:
            if keyword in text:
                found_keywords.append(f"#{keyword}")
        
        return found_keywords[:8]
    
    def generate_summary(self, content):
        if not content or len(content) < 50:
            return "요약 생성 실패"
            
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
        if not sentences:
            return "요약 생성 실패"
        
        summary = sentences[0]
        if len(summary) > 150:
            summary = summary[:147] + "..."
        
        return summary

def main():
    st.set_page_config(
        page_title="📈 네이버 경제뉴스 크롤러",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 네이버 경제뉴스 크롤러")
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        selected_date = st.date_input(
            "📅 날짜",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            min_value=datetime.now().date() - timedelta(days=7)
        )
        
        num_articles = st.slider("📰 기사 수", 1, 10, 3)
        max_pages = st.slider("📄 페이지 수", 1, 3, 1)
        
        political_filter = st.multiselect(
            "🎯 정치성향",
            ["전체", "보수", "중도", "진보", "중도-진보", "미분류"],
            default=["전체"]
        )
        
        keyword_search = st.text_input("🔍 키워드", placeholder="예: 금리, 반도체")
        
        st.markdown("---") # 설정과 노트 사이 구분선
        
        # 나의 스크랩 노트 섹션 (사이드바로 이동)
        st.header("📝 나의 스크랩 노트")
        if 'feedback_notes' not in st.session_state:
            st.session_state['feedback_notes'] = {} # 피드백 노트 세션 상태 초기화
            
        if st.session_state['feedback_notes']:
            for url, feedback_data in st.session_state['feedback_notes'].items():
                if feedback_data.get('one_line_review') or \
                   feedback_data.get('unknown_terms') or \
                   feedback_data.get('research_topics'):
                    
                    with st.expander(f"📖 {feedback_data.get('article_title', '제목 없음')}에 대한 나의 피드백", expanded=False):
                        st.markdown(f"**한줄평**: {feedback_data.get('one_line_review', '없음')}")
                        st.markdown(f"**모르는 용어**: {feedback_data.get('unknown_terms', '없음')}")
                        st.markdown(f"**더 찾아본 것**: {feedback_data.get('research_topics', '없음')}")
                        st.markdown(f"[원문 보기]({url})")
                        st.markdown("---")
        else:
            st.info("아직 작성된 노트가 없습니다. 기사를 스크랩하고 피드백을 작성해 보세요!")
        
        st.markdown("---") # 노트 섹션 아래 구분선
    
    # 메인
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🚀 뉴스 스크랩 시작", type="primary", use_container_width=True):
            scraper = NaverEconomicNewsScraper()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            target_date = datetime.combine(selected_date, datetime.min.time())
            status_text.text("뉴스 목록 수집 중...")
            
            news_list = scraper.get_economic_news_list(target_date, max_pages)
            
            if not news_list:
                st.error("뉴스 목록을 가져올 수 없습니다.")
                status_text.empty()
                progress_bar.empty()
                return
            
            # 필터링
            filtered_news = scraper.filter_by_political_stance(news_list, political_filter)
            if keyword_search:
                filtered_news = scraper.filter_by_keyword(filtered_news, keyword_search)
            
            if not filtered_news:
                st.warning("조건에 맞는 기사가 없습니다.")
                status_text.empty()
                progress_bar.empty()
                return
            
            st.success(f"총 {len(filtered_news)}개 기사 발견")
            
            selected_news = filtered_news[:num_articles]
            results = []
            
            # 피드백 저장을 위한 세션 상태 초기화/로드 (이미 사이드바에서 초기화됨)
            # if 'feedback_notes' not in st.session_state:
            #     st.session_state['feedback_notes'] = {} # {article_url: {review, terms, research}}
            
            for i, news in enumerate(selected_news):
                progress = (i + 1) / len(selected_news)
                progress_bar.progress(progress)
                status_text.text(f"[{i+1}/{len(selected_news)}] 기사 추출 중...")
                
                article_data = scraper.extract_article_content(news['link'])
                if article_data:
                    article_data['political_stance'] = news.get('political_stance', '미분류')
                    article_data['keywords'] = scraper.extract_keywords(article_data['content'], article_data['title'])
                    article_data['summary'] = scraper.generate_summary(article_data['content'])
                    results.append(article_data)
                
                time.sleep(1)
            
            status_text.text("완료!")
            progress_bar.progress(1.0)
            st.session_state['results'] = results
            st.session_state['scrape_date'] = selected_date
    
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            if 'results' in st.session_state:
                del st.session_state['results']
            # 세션 상태의 피드백 노트도 초기화
            if 'feedback_notes' in st.session_state:
                del st.session_state['feedback_notes']
            st.rerun()
    
    # 결과 다운로드 (전체 다운로드)
    if 'results' in st.session_state and st.session_state['results']:
        scrape_date = st.session_state.get('scrape_date', datetime.now().date())
        date_str = scrape_date.strftime('%Y-%m-%d') if hasattr(scrape_date, 'strftime') else str(scrape_date)
        
        all_content = f"# 📈 경제뉴스 스크랩 결과\n\n"
        all_content += f"**날짜**: {date_str}\n"
        all_content += f"**기사 수**: {len(st.session_state['results'])}개\n\n"
        all_content += "---\n\n"
        
        for i, article in enumerate(st.session_state['results']):
            # 피드백은 세션 상태에서 가져오기
            feedback_data = st.session_state['feedback_notes'].get(article['url'], {})
            one_line_review_session = feedback_data.get('one_line_review', '')
            unknown_terms_session = feedback_data.get('unknown_terms', '')
            research_topics_session = feedback_data.get('research_topics', '')

            all_content += f"## {i+1}. {article['title']}\n\n"
            all_content += f"- **언론사**: {article['press']}\n"
            all_content += f"- **시간**: {article['pub_time']}\n"
            all_content += f"- **URL**: {article['url']}\n\n"
            all_content += f"**요약**: {article.get('summary', '')}\n\n"
            all_content += f"**본문**:\n{article['content']}\n\n"
            all_content += f"### 🧠 셀프 피드백 \n"
            all_content += f"- **한줄평**: {one_line_review_session}\n"
            all_content += f"- **모르는 용어**: {unknown_terms_session}\n"
            all_content += f"- **더 찾아본 것**: {research_topics_session}\n\n"
            all_content += "---\n\n"
        
        st.download_button(
            label="📥 전체 다운로드",
            data=all_content,
            file_name=f"경제뉴스_{date_str}.md",
            mime="text/markdown"
        )
    
    # 초기 실행 시 안내 메시지 (사용법 포함)
    if 'results' not in st.session_state:
        st.info("뉴스 스크랩 시작 버튼을 클릭하세요.")
        
        with st.expander("📖 앱 사용법", expanded=False):
            st.markdown("""
            ### 📝 사용 방법
            1. **날짜 선택**: 크롤링할 날짜를 선택하세요
            2. **기사 수 설정**: 1-10개 사이에서 원하는 기사 수를 선택하세요
            3. **정치성향 필터**: 원하는 언론사 성향을 선택하세요
            4. **키워드 검색**: 특정 키워드가 포함된 기사만 보고 싶다면 입력하세요
            5. **스크랩 시작**: 버튼을 클릭하여 뉴스를 수집하세요
            
            ### 🎯 주요 기능
            - 언론사별 정치성향 분류
            - 키워드 기반 필터링
            - **나의 스크랩 노트 **
            - 구글 문서 호환 Markdown 다운로드
            """)
    
    # 결과 표시
    if 'results' in st.session_state and st.session_state['results']:
        st.markdown("---")
        st.header("📄 결과")
        
        results = st.session_state['results']
        scraper = NaverEconomicNewsScraper()
        
        for i, article_data in enumerate(results):
            # 피드백을 세션 상태에서 관리
            # 초기값은 세션 상태에 저장된 값이 있다면 사용, 없다면 빈 문자열
            # st.session_state['feedback_notes'] 딕셔너리에서 해당 기사의 피드백을 가져옴
            current_feedback = st.session_state['feedback_notes'].get(article_data['url'], {})
            review_default = current_feedback.get('one_line_review', '')
            terms_default = current_feedback.get('unknown_terms', '')
            research_default = current_feedback.get('research_topics', '')

            with st.expander(f"📰 {i+1}. {article_data['title']}", expanded=(i==0)):
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**언론사**: {article_data['press']}")
                with col2:
                    st.markdown(f"**시간**: {article_data['pub_time']}")
                with col3:
                    st.link_button("🔗 원문", article_data['url'])
                
                st.divider()
                
                # 분석
                keywords = article_data.get('keywords', [])
                summary = article_data.get('summary', '')
                
                st.subheader("🎯 분석")
                st.markdown(f"**요약**: {summary}")
                if keywords:
                    st.markdown(f"**키워드**: {' '.join(keywords)}")
                
                st.divider()
                
                # 본문
                st.subheader("📄 본문")
                st.markdown(article_data['content'])
                
                st.divider()
                
                # 셀프 피드백 폼 (세션 저장 기능)
                st.subheader("🧠 셀프 피드백")
                with st.form(f"feedback_form_{i}"):
                    one_line_review = st.text_input("한줄평", value=review_default, key=f"review_input_{i}")
                    unknown_terms = st.text_input("모르는 용어", value=terms_default, key=f"terms_input_{i}")
                    research_topics = st.text_input("더 찾아본 것", value=research_default, key=f"research_input_{i}")
                    
                    submit_button = st.form_submit_button("💾 스크랩 ")

                    if submit_button:
                        # 폼 제출 시 세션 상태 업데이트 (feedback_notes 딕셔너리에 저장)
                        st.session_state['feedback_notes'][article_data['url']] = {
                            'one_line_review': one_line_review,
                            'unknown_terms': unknown_terms,
                            'research_topics': research_topics,
                            'article_title': article_data['title'],
                            'article_url': article_data['url']
                        }
                        st.success("저장되었습니다!")
                
                # 폼 외부에 다운로드 버튼 배치
                # 다운로드 템플릿에 현재 세션에 저장된 피드백 내용 반영
                # st.session_state['feedback_notes']에서 최신 내용을 가져옴
                download_feedback = st.session_state['feedback_notes'].get(article_data['url'], {})
                download_template = f"""# 경제뉴스 스크랩

## 📊 기본 정보
- **언론사**: {article_data['press']}
- **기사 제목**: {article_data['title']}
- **발행일시**: {article_data['pub_time']}
- **기사 URL**: {article_data['url']}
- **카테고리**: 경제

## 🎯 핵심 분석 
- **한줄 요약**: {summary}
- **키워드**: {' '.join(keywords)}

## 📄 본문 
{article_data['content']}

## 🧠 셀프 피드백
- **한줄평**: {download_feedback.get('one_line_review', '')}
- **모르는 용어**: {download_feedback.get('unknown_terms', '')}
- **더 찾아본 것**: {download_feedback.get('research_topics', '')}

## 🏷️ 태그 시스템
`#정책` `#금리` `#주식` `#부동산` `#환율` `#기업실적` `#국제경제`

---
*스크랩 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
                st.download_button(
                    label=f"📥 기사 {i+1} 구글 문서용 개별 다운로드",
                    data=download_template,
                    file_name=f"경제뉴스_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    key=f"download_individual_{i}"
                )

if __name__ == "__main__":
    main()
