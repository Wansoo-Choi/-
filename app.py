from pathlib import Path

import pandas as pd
import streamlit as st


# 강의자료의 텍스트, 표, JSON, 지표, 지도, 이미지, 사이드바를 사용합니다.
st.set_page_config(page_title="최완수의 소개 페이지", page_icon="📖", layout="wide")
IMAGE_DIR = Path(__file__).resolve().parent

st.sidebar.header("컴퓨팅 탐색 과제")
menu = st.sidebar.radio("메뉴 선택", ["자기소개", "수업시간표", "가보고 싶은 장소"])
st.sidebar.caption("최완수 · 서울대학교")


if menu == "자기소개":
    st.title("나의 소개 페이지")
    st.header("자기소개")
    st.write("안녕하세요. 제 이름은 최완수입니다.")
    st.write("저는 서울대학교 물리천문학부 소속으로, 현재 수리과학부를 복수전공하고 있습니다.")
    st.write("현재 저는 수학과 이론 컴퓨터 과학에 큰 관심을 가지고 공부하고 있습니다.")

    st.header("관심 있는 것")
    st.write("저는 새로운 내용을 공부하고 흥미로운 수학 문제를 고민해 보는 것을 좋아합니다.")
    st.write("또 영화를 보거나 맛있는 음식을 먹는 것도 좋아하는 편입니다.")
    st.markdown("최근에는 연구 업무와 관련하여 [arXiv](https://arxiv.org)에 자주 방문하고 있습니다.")

    st.header("하고 싶은 것")
    st.write(
        "제가 이제 곧 대학원에 진학하게 될 것 같은데, 대학원 진학 이후에는 "
        "수학과 이론 컴퓨터 과학에 관련된 다양한 연구 주제들을 탐색하고, "
        "흥미로운 문제들을 발견해 선택한 문제에 대해 깊이 있는 연구를 진행해 보고 싶습니다."
    )

    # 강의자료의 코드 블록과 수식 출력 예제
    st.caption("간단한 파이썬 코드 예시")
    st.code("for i in range(3):\n    print('Hello, Streamlit!')", language="python")
    st.caption("피타고라스 정리")
    st.latex(r"a^2 + b^2 = c^2")


elif menu == "수업시간표":
    st.title("📚 나의 수업 시간표")
    st.caption("2026학년도 2학기")

    # 금요일 수업을 포함하여 실제 시작·종료 시각을 그대로 표시합니다.
    timetable = pd.DataFrame({
        "시간": ["09:30–10:45", "10:00–12:50", "11:00–12:15", "14:00–15:15"],
        "월": ["대수학 2", "", "", ""],
        "화": ["", "", "조합최적화", "해석학 2"],
        "수": ["대수학 2", "", "", ""],
        "목": ["", "", "조합최적화", "해석학 2"],
        "금": ["", "컴퓨팅 탐색", "", ""],
    }).set_index("시간")
    st.header("주간 시간표")
    st.table(timetable)

    courses = [
        {"과목": "대수학 2", "구분": "수리과학부 대학원 전공 과목", "학점": 3,
         "수업 시간": "월/수 09:30–10:45", "강의실": "28동 303호"},
        {"과목": "해석학 2", "구분": "수리과학부 대학원 전공 과목", "학점": 3,
         "수업 시간": "화/목 14:00–15:15", "강의실": "28동 303호"},
        {"과목": "조합최적화", "구분": "산업공학과 대학원 전공 과목", "학점": 3,
         "수업 시간": "화/목 11:00–12:15", "강의실": "39동 327호"},
        {"과목": "컴퓨팅 탐색: 실생활에서 활용하기", "구분": "학부 교양 과목", "학점": 3,
         "수업 시간": "금 10:00–12:50", "강의실": "26동 104호"},
    ]
    st.subheader("과목별 수업 정보")
    st.table(pd.DataFrame(courses))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("수강 과목 수", len(courses))
    with col2:
        st.metric("총학점", sum(course["학점"] for course in courses))

    # 표 아래의 자세한 JSON 정보는 필요할 때 펼쳐 볼 수 있습니다.
    with st.expander("수업 정보를 JSON으로 보기"):
        st.json({course["과목"]: {key: value for key, value in course.items()
                                  if key != "과목"} for course in courses})


elif menu == "가보고 싶은 장소":
    st.title("🍁 가보고 싶은 나라, 캐나다")
    st.write("캐나다의 도시를 여행하고, 호수와 숲, 빙하, 오로라 등 다양한 자연 풍경을 직접 보고 싶습니다.")

    # 좌표는 각 관광지 또는 도시의 대표 위치입니다.
    destinations = [
        {
            "장소": "몬트리올", "지역": "퀘벡주", "lat": 45.5075, "lon": -73.5540,
            "사진": "montreal.jpg", "사진 설명": "몬트리올 구항구에서 바라본 구시가지",
            "소개": "역사적인 건물과 거리가 남아 있는 올드 몬트리올과 구항구를 걸으며 도시의 분위기를 느껴 보고 싶습니다.",
            "사진 출처": "https://commons.wikimedia.org/wiki/File:Vieux-Port,_Montr%C3%A9al.JPG",
            "사진 저자": "Gilbert Bochenek", "이용 조건": "Public domain",
            "이용 조건 링크": "https://commons.wikimedia.org/wiki/File:Vieux-Port,_Montr%C3%A9al.JPG",
            "관광 안내": "https://www.mtl.org/en/city/about-montreal/neighbourhoods/old-montreal",
        },
        {
            "장소": "밴프 · 레이크 루이스", "지역": "앨버타주", "lat": 51.4167, "lon": -116.2167,
            "사진": "lake_louise.jpg", "사진 설명": "레이크 루이스와 빅토리아 빙하",
            "소개": "밴프 국립공원의 레이크 루이스에서 청록색 호수와 숲, 로키산맥과 빙하가 어우러진 풍경을 보고 싶습니다.",
            "사진 출처": "https://commons.wikimedia.org/wiki/File:Lake_Louise_and_Victoria_Glacier.jpg",
            "사진 저자": "Bob rulz", "이용 조건": "CC BY-SA 3.0",
            "이용 조건 링크": "https://creativecommons.org/licenses/by-sa/3.0/",
            "관광 안내": "https://www.banfflakelouise.com/experiences/lake-louise",
        },
        {
            "장소": "옐로나이프", "지역": "노스웨스트 준주", "lat": 62.4540, "lon": -114.3718,
            "사진": "yellowknife.jpg", "사진 설명": "옐로나이프에서 촬영한 오로라",
            "소개": "오로라 관측으로 유명한 옐로나이프에서 밤하늘에 펼쳐지는 오로라를 직접 보고 싶습니다.",
            "사진 출처": "https://commons.wikimedia.org/wiki/File:Aurora_at_Yellowknife,_Canada_2014.jpg",
            "사진 저자": "LG전자 (LGEPR)", "이용 조건": "CC BY 2.0",
            "이용 조건 링크": "https://creativecommons.org/licenses/by/2.0/",
            "관광 안내": "https://www.yellowknife.ca/weather-and-aurora-borealis",
        },
    ]

    selected = st.selectbox("지도에서 볼 장소", ["세 곳 모두"] + [d["장소"] for d in destinations])
    shown = destinations if selected == "세 곳 모두" else [d for d in destinations if d["장소"] == selected]
    points = pd.DataFrame([{key: d[key] for key in ["장소", "lat", "lon"]} for d in shown])
    if selected == "세 곳 모두":
        st.map(points, height=360)
    else:
        st.map(points, zoom=9, height=360)

    # 전체 보기에서는 사진을 세 열에 배치합니다.
    columns = st.columns(len(shown))
    for column, destination in zip(columns, shown):
        with column:
            st.subheader(destination["장소"])
            st.caption(destination["지역"])
            st.image(str(IMAGE_DIR / destination["사진"]),
                     caption=destination["사진 설명"], width="stretch")
            st.write(destination["소개"])
            st.caption(
                f"사진: {destination['사진 저자']} · "
                f"[{destination['이용 조건']}]({destination['이용 조건 링크']}) · "
                f"[원본]({destination['사진 출처']})"
            )
            st.markdown(f"[공식 관광 안내]({destination['관광 안내']})")
