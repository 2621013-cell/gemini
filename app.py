import re
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from wordcloud import WordCloud

# 페이지 기본 설정
st.set_page_config(page_title="유튜브 영상 & 댓글 분석기", layout="wide")
st.title("📹 유튜브 영상 분석 및 댓글 워드클라우드")

# 사이드바에서 API 키 입력 받기
api_key = st.sidebar.text_input(
    "YouTube Data API v3 키를 입력하세요:", type="password"
)


# 유튜브 URL에서 Video ID 추출 함수
def extract_video_id(url):
    pattern = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/embed\/|\/v\/|youtu\.be\/|\/shorts\/)([^#\&\?]*)"
    match = re.search(pattern, url)
    if match:
        return match.group(1) or match.group(2)
    return None


# 유튜브 API 호출 객체 생성
def get_youtube_client(key):
    return build("youtube", "v3", developerKey=key)


if api_key:
    youtube = get_youtube_client(api_key)

    # 영상 링크 입력 받기
    video_url = st.text_input(
        "분석할 유튜브 영상 링크를 입력하세요:",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    if video_url:
        video_id = extract_video_id(video_url)

        if video_id:
            try:
                # 1. 영상 기본 정보 및 통계 가져오기
                video_response = (
                    youtube.videos()
                    .list(part="snippet,statistics", id=video_id)
                    .execute()
                )

                if video_response["items"]:
                    video_info = video_response["items"][0]
                    title = video_info["snippet"]["title"]
                    channel = video_info["snippet"]["channelTitle"]
                    stats = video_info["statistics"]

                    view_count = int(stats.get("viewCount", 0))
                    like_count = int(stats.get("likeCount", 0))
                    comment_count = int(stats.get("commentCount", 0))

                    st.subheader(f"📌 {title}")
                    st.caption(f"채널명: {channel}")

                    # 지표 표시 (3개 컬럼)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("조회수", f"{view_count:,} 회")
                    col2.metric("좋아요 수", f"{like_count:,} 개")
                    col3.metric("댓글 수", f"{comment_count:,} 개")

                    st.markdown("---")

                    # 2. 댓글 가져오기 (최대 100개)
                    with st.spinner("댓글 데이터를 수집 중입니다..."):
                        comment_response = (
                            youtube.commentThreads()
                            .list(
                                part="snippet",
                                videoId=video_id,
                                maxResults=100,
                                textFormat="plainText",
                            )
                            .execute()
                        )

                        comments = []
                        for item in comment_response.get("items", []):
                            comment = item["snippet"]["topLevelComment"][
                                "snippet"
                            ]["textDisplay"]
                            comments.append(comment)

                    # 3. 댓글 예시 보여주기
                    st.subheader("💬 주요 댓글 예시 (최신순)")
                    with st.expander("댓글 보기 (최대 10개)", expanded=True):
                        for i, comment in enumerate(comments[:10], 1):
                            st.write(f"**{i}.** {comment}")

                    # 4. 워드클라우드 생성
                    st.subheader("☁️ 댓글 워드클라우드")
                    if comments:
                        all_text = " ".join(comments)

                        # 한글 폰트 설정 (Windows/Mac 공통 지원용 예시 폰트 경로 지정 필요 가능)
                        # NanumGothic 또는 맑은고딕 사용
                        wordcloud = WordCloud(
                            font_path="c:/Windows/Fonts/malgun.ttf",  # Windows 맑은고딕 경로 (Mac은 /Library/Fonts/AppleGothic.ttf)
                            width=800,
                            height=400,
                            background_color="white",
                        ).generate(all_text)

                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)
                    else:
                        st.info("수집된 댓글이 없습니다.")

                else:
                    st.error(
                        "영상을 찾을 수 없습니다. URL을 다시 확인해주세요."
                    )

            except Exception as e:
                st.error(
                    f"에러가 발생했습니다. API 키나 URL을 확인해주세요: {e}"
                )
        else:
            st.warning("올바른 유튜브 링크 형식이 아닙니다.")
else:
    st.info("왼쪽 사이드바에 YouTube Data API 키를 입력해 주세요.")
