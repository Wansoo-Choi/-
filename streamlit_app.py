"""중간프로젝트의 2026년 10월 TODO 리스트를 옮긴 Streamlit 웹앱."""

import calendar
import html
import json

import streamlit as st

YEAR, MONTH, MAX_TASKS = 2026, 10, 10
RED, BLUE, GREEN = "#b42318", "#2456a6", "#287447"

# 원본 프로그램에 표시되던 사용 방법은 파일 생성 시 여기에 그대로 넣습니다.
HELP_TEXT = "<입력 창 사용 방법>\n\n- 처음에 뜨는 입력 창에 10월 중 할 일들의 제목과 시작일·마감일(1~31)을 입력합니다.\n- 입력 완료를 누르면 달력 창이 뜹니다.\n\n<달력 창 사용 방법>\n\n- 달력의 각 날짜 칸마다 그날 해야 할 일들 중 5개가 표시되며, 만약 해당 날에 6개 이상의 할 일들이 있는 경우 5개의 표시된 일 아래에 ... 기호가 추가로 표시됩니다.\n- 마감 기한이 2일 이내인 급한 일들은 빨간색으로 표시되며, 각 날짜 칸에 표시되는 5개 일들도 이 빨간색의 급한 일들이 우선시되어 표시됩니다.\n- 각 날짜 칸의 상세 보기 버튼을 누르면 해당 날짜의 모든 미완료 일을 확인 가능하며, 이 미완료 일들도 급한 일(빨간색)과 덜 급한 일(검은색)로 나뉘어 표시됩니다.\n- 달력 창 하단의 목록에서 처음에 적은 일들의 완료 처리·완료 취소 처리를 할 수 있습니다. 완료된 일들은 달력에 표시되지 않습니다.\n\n<입력 창 수정 방법>\n\n- 입력 수정 버튼을 눌러 처음에 입력한 일들을 수정할 수 있습니다. 만약 수정 버튼을 누른 후 한 일의 세 칸을 전부 지우면 해당 일이 삭제됩니다.\n- 달력 페이지에서 완료 처리한 일은 입력 페이지에서 제목이나 기간을 수정해도 완료 상태가 유지됩니다.\n\n<저장 및 불러오기>\n\n- 파일 메뉴를 통해 적은 내역을 저장하거나, 이전에 저장한 내역을 다시 불러올 수 있습니다."


def empty_tasks():
    return [["", 0, 0, False] for _ in range(MAX_TASKS)]


def check_task(title, start, end, done):
    """원본과 동일한 제목·기간·완료 여부 검사."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("할 일의 제목을 입력해주세요.")
    if len(title) > 60 or any(char in title for char in "\n\r\t"):
        raise ValueError("제목은 줄바꿈 없이 60자 이내로 입력해주세요.")
    if type(start) is not int or type(end) is not int:
        raise ValueError("시작일과 마감일에는 정수를 입력해주세요.")
    if not 1 <= start <= end <= 31:
        raise ValueError("날짜는 1~31이며, 시작일이 마감일보다 늦을 수 없습니다.")
    if type(done) is not bool:
        raise ValueError("완료 여부 형식이 올바르지 않습니다.")


def read_inputs(rows, old_tasks):
    """전부 검사를 통과한 경우에만 새 목록을 반환합니다."""
    result = []
    for i, row in enumerate(rows):
        title, start_text, end_text = [value.strip() for value in row]
        if not title and not start_text and not end_text:
            result.append(["", 0, 0, False])
            continue
        try:
            if not title or not start_text or not end_text:
                raise ValueError("제목, 시작일, 마감일을 모두 입력해주세요.")
            try:
                start, end = int(start_text), int(end_text)
            except ValueError:
                raise ValueError("시작일과 마감일에는 정수를 입력해주세요.") from None
            done = old_tasks[i][3]
            check_task(title, start, end, done)
        except ValueError as error:
            raise ValueError(f"{i + 1}번 행: {error}") from None
        result.append([title, start, end, done])
    return result


def tasks_on_day(tasks, day):
    urgent, other = [], []
    for task in tasks:
        if task[0] and not task[3] and task[1] <= day <= task[2]:
            (urgent if task[2] - day <= 2 else other).append(task)
    return urgent + other


def validate_file(data):
    if not isinstance(data, dict) or data.get("year") != YEAR or data.get("month") != MONTH:
        raise ValueError("2026년 10월 TODO 데이터 파일을 선택해주세요.")
    rows = data.get("tasks")
    if not isinstance(rows, list) or len(rows) > MAX_TASKS:
        raise ValueError("할 일은 최대 10개까지 불러올 수 있습니다.")
    result = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError("할 일 데이터의 형식이 올바르지 않습니다.")
        title, start, end, done = row
        if title == "" and type(start) is int and start == 0 and type(end) is int and end == 0 and done is False:
            result.append(["", 0, 0, False])
        else:
            check_task(title, start, end, done)
            result.append([title.strip(), start, end, done])
    return result + empty_tasks()[: MAX_TASKS - len(result)]


def serialize(tasks):
    return json.dumps({"year": YEAR, "month": MONTH, "tasks": tasks}, ensure_ascii=False, indent=2)


def initialize():
    state = st.session_state
    if "tasks" not in state:
        state.tasks = empty_tasks()
        state.page = "input"
        state.saved_json = serialize(state.tasks)
        state.edit_version = 0
    if "notice" in state:
        st.success(state.pop("notice"))


def mark_downloaded():
    st.session_state.saved_json = serialize(st.session_state.tasks)


def apply_import(tasks):
    st.session_state.tasks = tasks
    st.session_state.saved_json = serialize(tasks)
    st.session_state.page = "calendar"
    st.session_state.edit_version += 1
    st.session_state.pop("pending_import", None)
    st.session_state.notice = "저장된 할 일과 완료 여부를 불러왔습니다."


def render_files():
    with st.sidebar:
        st.header("파일")
        st.download_button(
            "저장하기 · JSON 다운로드",
            data=serialize(st.session_state.tasks).encode("utf-8"),
            file_name="october_tasks.json", mime="application/json",
            on_click=mark_downloaded, width="stretch",
        )
        st.caption("입력 창에서 수정 중인 내용은 먼저 ‘입력 완료’ 또는 ‘입력 내용 저장 준비’를 눌러 적용하세요.")
        uploaded = st.file_uploader(
            "불러오기 · JSON 파일 선택", type=["json"],
            on_change=lambda: st.session_state.pop("pending_import", None),
        )
        if st.button("선택한 파일 불러오기", disabled=uploaded is None, width="stretch"):
            st.session_state.pop("pending_import", None)
            try:
                tasks = validate_file(json.loads(uploaded.getvalue().decode("utf-8-sig")))
            except (ValueError, UnicodeError, RecursionError) as error:
                st.error(f"파일을 불러올 수 없습니다.\n\n{error}")
            else:
                # 입력 중인 내용도 사라질 수 있으므로 불러오기는 항상 먼저 확인합니다.
                st.session_state.pending_import = tasks

        if "pending_import" in st.session_state:
            st.warning("현재 목록과 입력 중인 내용이 선택한 파일로 교체됩니다. 보관하려면 먼저 내용을 적용하고 JSON을 다운로드하세요.")
            if st.button("교체하여 불러오기", type="primary", width="stretch"):
                apply_import(st.session_state.pending_import)
                st.rerun()
            if st.button("불러오기 취소", width="stretch"):
                st.session_state.pop("pending_import")
                st.rerun()

        if serialize(st.session_state.tasks) != st.session_state.saved_json:
            st.caption("● 마지막으로 불러오거나 다운로드한 뒤 변경된 내용이 있습니다.")
        st.info("이 웹앱은 서버에 일정을 영구 저장하지 않습니다. 새로고침하거나 탭을 닫기 전에 JSON을 다운로드하고, 다음에 접속하면 불러오세요.")


def render_input():
    st.subheader("2026년 10월 동안 할 일을 최대 10개까지 입력하세요.")
    st.write("- 할 일의 이름을 60자 이내로, 시작/마감 날짜는 10월의 일자(1~31)로 입력해 주세요.\n"
             "- ex: 시험 공부를 10월 5일부터 10일까지 진행해야 할 때 → 시험 공부 / 5 / 10 으로 입력")
    with st.form("task_inputs", enter_to_submit=False):
        rows = []
        for i, (title, start, end, _) in enumerate(st.session_state.tasks):
            cols = st.columns([0.5, 5, 1.5, 1.5])
            cols[0].write(f"**{i + 1}**")
            prefix = f"edit_{st.session_state.edit_version}_{i}"
            new_title = cols[1].text_input(f"{i + 1}번 할 일의 제목", value=title, key=f"{prefix}_title", placeholder="할 일의 제목 (60자 이내)", label_visibility="collapsed")
            new_start = cols[2].text_input(f"{i + 1}번 시작일", value=str(start) if title else "", key=f"{prefix}_start", placeholder="시작일", label_visibility="collapsed")
            new_end = cols[3].text_input(f"{i + 1}번 마감일", value=str(end) if title else "", key=f"{prefix}_end", placeholder="마감일", label_visibility="collapsed")
            rows.append([new_title, new_start, new_end])
        show = st.form_submit_button("입력 완료 → 달력 보기", type="primary")
        save = st.form_submit_button("입력 내용 저장 준비")
    st.caption("한 행의 제목·시작일·마감일을 모두 지우고 입력 완료를 누르면 해당 일이 삭제됩니다.")
    if show or save:
        try:
            new_tasks = read_inputs(rows, st.session_state.tasks)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.tasks = new_tasks
            if show:
                st.session_state.page = "calendar"
            else:
                st.session_state.notice = "입력 내용을 적용했습니다. 왼쪽 ‘저장하기 · JSON 다운로드’를 눌러 파일로 보관하세요."
            st.rerun()


@st.dialog("날짜별 할 일", width="large")
def show_day(day):
    daily = tasks_on_day(st.session_state.tasks, day)
    urgent = [task for task in daily if task[2] - day <= 2]
    other = [task for task in daily if task[2] - day >= 3]
    st.subheader(f"10월 {day}일 · 미완료 {len(daily)}개")
    for group, heading, note, color in [
        (urgent, "급하게 해야 할 일", "해당 날짜 기준으로 마감까지 0~2일 남은 일", RED),
        (other, "상대적으로 덜 급한 일", "해당 날짜 기준으로 마감까지 3일 이상 남은 일", "var(--text-color)"),
    ]:
        st.markdown(f"#### {heading} ({len(group)}개)")
        st.caption(note)
        for i, (title, start, end, _) in enumerate(group, 1):
            remaining = end - day
            mark = "해당 날짜에 마감" if remaining == 0 else f"마감 {remaining}일 전"
            st.markdown(f'<p style="color:{color}">{i}. {html.escape(title)} [{mark}]<br>기간: 10/{start} ~ 10/{end}</p>', unsafe_allow_html=True)
        if not group:
            st.write("해당하는 할 일이 없습니다.")
    if st.button("닫기"):
        st.rerun()


def render_calendar():
    if st.button("← 입력 수정"):
        st.session_state.page = "input"
        st.session_state.edit_version += 1
        st.rerun()
    st.markdown(f'<p style="color:{RED}">빨간색으로 표시된 일들은 해당 날짜로부터 마감까지가 2일 이내인 일들을 의미합니다.</p>', unsafe_allow_html=True)
    clicked_day = None
    for col, label in zip(st.columns(7), ["일", "월", "화", "수", "목", "금", "토"]):
        col.markdown(f"**{label}**")
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(YEAR, MONTH):
        for col, day in zip(st.columns(7), week):
            with col:
                with st.container(border=True, height=280):
                    if day == 0:
                        continue
                    st.markdown(f"**{day}**")
                    daily = tasks_on_day(st.session_state.tasks, day)
                    if st.button(f"상세 보기 ({len(daily)})", key=f"day_{day}", width="stretch"):
                        clicked_day = day
                    for title, _, end, _ in daily[:5]:
                        short = title[:10] + "…" if len(title) > 10 else title
                        color = RED if end - day <= 2 else "var(--text-color)"
                        st.markdown(f'<div style="color:{color};font-size:0.88rem;line-height:1.6">• {html.escape(short)}</div>', unsafe_allow_html=True)
                    if len(daily) > 5:
                        st.write("...")

    st.subheader("전체 할 일들 목록")
    st.write("- 완료 처리 버튼을 누른 일들은 완료된 일로 처리되어 달력에 표시되지 않습니다.")
    st.write("- 완료 취소 버튼을 누른 일들은 다시 미완료 상태로 처리됩니다.\n"
             "- 달력 페이지에서 완료 처리한 일은 입력 페이지에서 제목이나 기간을 수정해도 완료 상태가 유지됩니다.")
    total = sum(bool(task[0]) for task in st.session_state.tasks)
    completed = sum(bool(task[0]) and task[3] for task in st.session_state.tasks)
    st.write(f"전체 {total}개 · 완료 {completed}개 · 미완료 {total - completed}개")
    for i, (title, start, end, done) in enumerate(st.session_state.tasks):
        if not title:
            continue
        cols = st.columns([5, 2, 2])
        color, label = (GREEN, "완료") if done else ("var(--text-color)", "미완료")
        cols[0].markdown(f'<p style="color:{color}">[{label}] {html.escape(title)}</p>', unsafe_allow_html=True)
        cols[1].write(f"10/{start} ~ 10/{end}")
        if cols[2].button("완료 취소" if done else "완료 처리", key=f"done_{i}", width="stretch"):
            st.session_state.tasks[i][3] = not done
            st.rerun()
    if total == 0:
        st.info("등록된 할 일이 없습니다. '입력 수정'에서 추가하세요.")
    if clicked_day is not None:
        show_day(clicked_day)


def main():
    st.set_page_config(page_title="2026년 10월 TODO 리스트", page_icon="📅", layout="wide")
    st.title("2026년 10월 달력형 TODO 리스트")
    st.write("2026년 10월 동안 각 날짜별로 해야 할 일들을 관리해 주는 달력형 TODO 리스트입니다.")
    st.caption("날짜는 모두 2026년 10월이며 시작일과 마감일에 1~31을 입력합니다. 양 끝 날짜를 포함해 미완료 일정을 표시합니다.")
    st.caption("빨간색은 '각 달력 날짜'에서 마감까지 0~2일 남았다는 뜻입니다. 오늘 날짜를 기준으로 한 강조가 아니며, 마감일 이후에는 표시하지 않습니다.")
    initialize()
    render_files()
    with st.expander("사용 방법 · 기존 TODO 프로그램의 설명"):
        st.text(HELP_TEXT, width="stretch")
        st.info("웹 버전에서는 원본 설명의 ‘파일 메뉴’를 왼쪽 파일 영역으로 옮겼습니다. 저장은 JSON 다운로드, 불러오기는 JSON 업로드로 진행합니다. 프로그램 종료 대신 브라우저 탭을 닫되, 먼저 파일을 다운로드하세요.")
    if st.session_state.page == "input":
        render_input()
    else:
        render_calendar()


if __name__ == "__main__":
    main()
