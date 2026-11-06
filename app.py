import streamlit as st
import pandas as pd


# 강의자료의 sidebar와 radio로 세 화면을 선택합니다.
st.sidebar.header("컴퓨팅 탐색 과제")
menu = st.sidebar.radio(
    "메뉴 선택", ["자기소개", "수업시간표", "가보고 싶은 장소"]
)


if menu == "자기소개":
    st.title("나의 소개 페이지")

    st.header("자기소개")
    st.text("안녕하세요. 제 이름은 최완수입니다.")
    st.write("서울대학교에서 물리천문학부와 수리과학부를 공부하고 있습니다.")
    st.markdown("저는 **수학**과 *그래프 이론*에 관심이 있습니다.")

    # 아래의 소개 문장들은 원하는 내용으로 바꾸세요.
    st.header("좋아하는 것")
    st.write("저는 수학 문제를 풀고 새로운 내용을 공부하는 것을 좋아합니다.")
    st.markdown("관심 있는 사이트는 [arXiv](https://arxiv.org)입니다.")

    st.header("앞으로의 목표")
    st.write("수학을 더 깊이 공부하고, 관심 있는 주제를 연구하고 싶습니다.")

    st.caption("간단한 파이썬 코드 예시")
    st.code("for i in range(3):\n    print('Hello, Streamlit!')", language="python")

    st.caption("피타고라스 정리")
    st.latex(r"a^2 + b^2 = c^2")


elif menu == "수업시간표":
    st.title("📚 나의 수업 시간표")

    # 아래 시간표는 강의자료를 참고한 예시입니다.
    # 실제 수업명과 교시로 수정하세요. 각 열의 항목 수는 같아야 합니다.
    timetable = pd.DataFrame({
        "요일": ["월", "화", "수", "목", "금"],
        "1교시": ["", "전공", "글쓰기", "수학", "컴퓨팅 탐색"],
        "2교시": ["", "전공", "글쓰기", "수학", "컴퓨팅 탐색"],
        "3교시": ["영어", "전공", "영어", "체육", "컴퓨팅 탐색"],
    })

    st.header("정적 시간표 (st.table)")
    st.table(timetable)

    # 실제 교수님과 강의실로 수정하세요.
    course_info = {
        "컴퓨팅 탐색": {"교수": "교수명 입력", "강의실": "강의실 입력"},
        "영어": {"교수": "교수명 입력", "강의실": "강의실 입력"},
        "전공": {"교수": "교수명 입력", "강의실": "강의실 입력"},
        "글쓰기": {"교수": "교수명 입력", "강의실": "강의실 입력"},
        "수학": {"교수": "교수명 입력", "강의실": "강의실 입력"},
        "체육": {"교수": "교수명 입력", "강의실": "강의실 입력"},
    }

    st.header("수업 정보 (st.json)")
    st.json(course_info)

    # 예시 학점입니다. 실제 수강 과목과 학점으로 수정하세요.
    credits = {
        "컴퓨팅 탐색": 3, "영어": 2, "전공": 3,
        "글쓰기": 2, "수학": 3, "체육": 1,
    }

    st.header("이번 학기 요약 (st.metric)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="수강 과목 수", value=len(credits))
    with col2:
        st.metric(label="총학점", value=sum(credits.values()))


elif menu == "가보고 싶은 장소":
    st.title("📍 가보고 싶은 장소")
    st.write("여행하며 각 지역의 풍경과 문화를 경험해 보고 싶습니다.")

    # 강의자료에 나온 도시와 좌표를 사용한 예시입니다.
    # 원하는 장소로 바꾸려면 장소명, 위도(lat), 경도(lon)를 함께 바꾸세요.
    places = pd.DataFrame({
        "장소": ["부산", "광주", "목포"],
        "lat": [35.1796, 35.1595, 34.8110],
        "lon": [129.0756, 126.8526, 126.3925],
    })

    st.header("여행지 지도")
    st.map(places)

    st.subheader("가보고 싶은 장소 목록")
    st.table(places)
