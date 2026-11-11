import streamlit as st
import requests
from kiwipiepy import Kiwi
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

# 페이지 기본 설정
st.set_page_config(
    page_title="유튜브 데이터 분석기",
    page_icon="🎬",
    layout="wide"
)

# Kiwi 형태소 분석기 캐싱 로드
@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

# 유튜브 동영상 ID 추출 함수
def extract_video_id(url):
    pattern = r'(?:v=|\/live\/|\/shorts\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 유튜브 댓글 수집 함수 (YouTube Data API v3)
def fetch_youtube_comments(video_id, api_key, max_results=100):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": max_results,
        "order": "relevance"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        comments = []
        for item in data.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
        return comments
    else:
        st.error(f"댓글을 불러오는 데 실패했습니다. (오류 코드: {response.status_code})")
        return []

# 명사 추출 및 데이터 정제 함수
def extract_nouns(comments):
    full_text = " ".join(comments)
    clean_text = re.sub(r'[^가-힣a-zA-Z\s]', '', full_text)
    tokens = kiwi.tokenize(clean_text)
    nouns = [token.form for token in tokens if token.tag.startswith('NN') and len(token.form) > 1]
    return " ".join(nouns)


# 메인 제목
st.title("🎬 유튜브 통합 데이터 분석기")
st.write("유튜브 링크를 입력하여 썸네일을 추출하거나 댓글 키워드를 분석해 보세요.")

# 사이드바 설정
api_key = st.sidebar.text_input("유튜브 Data API 키 입력", type="password")
font_path = st.sidebar.text_input("한글 폰트 경로", value="malgun.ttf")

# 탭 메뉴 구성
tab1, tab2 = st.tabs(["🖼️ 썸네일 추출기", "💬 댓글 분석 & 워드클라우드"])

# [탭 1] 썸네일 추출 기능
with tab1:
    st.header("유튜브 썸네일 추출")
    video_url_thumb = st.text_input(
        "유튜브 영상 링크를 입력하세요:",
        key="thumb_url",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    if video_url_thumb:
        video_id = extract_video_id(video_url_thumb)
        if video_id:
            maxres_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            st.image(maxres_url, caption="최고 화질 썸네일", use_container_width=True)
            st.markdown(f"👉 **[원본 이미지 고화질 링크 열기]({maxres_url})**")
        else:
            st.warning("올바른 유튜브 URL 형식이 아닙니다.")

# [탭 2] 댓글 분석 및 워드클라우드 기능
with tab2:
    st.header("유튜브 댓글 분석 & 워드클라우드")
    
    video_url_comment = st.text_input(
        "댓글을 분석할 유튜브 영상 링크를 입력하세요:",
        key="comment_url",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    if st.button("댓글 분석 시작"):
        if not api_key:
            st.warning("사이드바에 유튜브 Data API 키를 입력해야 댓글 수집이 가능합니다.")
        elif not video_url_comment:
            st.warning("분석할 유튜브 영상 링크를 입력해 주세요.")
        else:
            video_id = extract_video_id(video_url_comment)
            if video_id:
                with st.spinner("댓글 수집 중..."):
                    comments = fetch_youtube_comments(video_id, api_key)
                
                if comments:
                    st.success(f"총 {len(comments)}개의 댓글 수집 완료!")
                    
                    with st.spinner("형태소 분석 및 워드클라우드 생성 중..."):
                        processed_text = extract_nouns(comments)
                        
                        if processed_text.strip():
                            wc = WordCloud(
                                font_path=font_path,
                                background_color="white",
                                width=800,
                                height=400
                            ).generate(processed_text)
                            
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            
                            st.pyplot(fig)
                        else:
                            st.info("분석할 수 있는 의미 있는 명사 키워드가 부족합니다.")
            else:
                st.warning("올바른 유튜브 URL 형식이 아닙니다.")
