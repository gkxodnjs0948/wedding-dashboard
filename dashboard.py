import streamlit as st
import pandas as pd
import altair as alt
import os

# 1. 페이지 설정
st.set_page_config(page_title="결혼준비 대시보드", page_icon="💍", layout="wide")

# 2. 파일 경로 설정
EXCEL_FILE = '260118 결혼준비.xlsx'
SAVE_FILE = 'dashboard_working_data.csv'
TARGET_SAVE_FILE = 'target_budget_data.csv'

# 3. 데이터 로드 함수
def load_main_data():
    if os.path.exists(SAVE_FILE):
        df = pd.read_csv(SAVE_FILE)
    else:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name='예산', skiprows=3)
            if '대분류' in df.columns: df['대분류'] = df['대분류'].ffill()
            if '비고' in df.columns: df.rename(columns={'비고': '진행상황'}, inplace=True)
        except:
            df = pd.DataFrame(columns=['대분류', '소분류', '예산', '진행상황', '메모/링크'])

    target_cols = ['대분류', '소분류', '예산', '진행상황', '메모/링크']
    for col in target_cols:
        if col not in df.columns: df[col] = 0 if col == '예산' else ""
    
    df = df[target_cols].fillna("")
    df['예산'] = pd.to_numeric(df['예산'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    return df

def load_target_data():
    if os.path.exists(TARGET_SAVE_FILE):
        return pd.read_csv(TARGET_SAVE_FILE).iloc[0].to_dict()
    else:
        try:
            origin = pd.read_excel(EXCEL_FILE, sheet_name='예산', skiprows=3)
            return {
                "전체": int(origin['전체 예산'].dropna().iloc[0]),
                "결혼식": int(origin['결혼식'].dropna().iloc[0]),
                "신혼집": int(origin['집'].dropna().iloc[0])
            }
        except:
            return {"전체": 50000000, "결혼식": 35000000, "신혼집": 15000000}

# 세션 상태 초기화
if 'main_df' not in st.session_state: st.session_state.main_df = load_main_data()
if 'targets' not in st.session_state: st.session_state.targets = load_target_data()

# 4. 상단 타이틀
st.subheader("💍 태원 해든 결혼준비")
st.markdown("**웨딩 데이: 2027년 3월 6일💖**")
st.divider()

# --- 5. 데이터 수정 섹션 ---
with st.expander("✏️ 데이터 및 목표 예산 수정", expanded=False):
    # (1) 목표 예산 수정
    st.write("#### 🎯 목표 예산 설정")
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        new_total = st.number_input("전체 목표 예산", value=int(st.session_state.targets['전체']), step=1000000)
    with t_col2:
        new_wedding = st.number_input("결혼식 목표 예산", value=int(st.session_state.targets['결혼식']), step=1000000)
    with t_col3:
        new_house = st.number_input("신혼집 목표 예산", value=int(st.session_state.targets['신혼집']), step=1000000)
    
    if new_total != st.session_state.targets['전체'] or new_wedding != st.session_state.targets['결혼식'] or new_house != st.session_state.targets['신혼집']:
        st.session_state.targets = {"전체": new_total, "결혼식": new_wedding, "신혼집": new_house}
        pd.DataFrame([st.session_state.targets]).to_csv(TARGET_SAVE_FILE, index=False)
        st.toast("목표 예산이 저장되었습니다!")

    st.divider()

    # (2) 세부 항목 수정 표
    st.write("#### 📋 세부 항목 관리")
    # 🚨 삭제 방법 안내 추가
    st.caption("💡 **항목 삭제 방법:** 지우려는 줄을 클릭한 후 키보드의 **Delete** 또는 **Backspace** 키를 누르세요.")
    
    edited_df = st.data_editor(
        st.session_state.main_df, 
        num_rows="dynamic",  # 👈 이 설정이 '삭제'와 '추가'를 가능하게 합니다.
        use_container_width=True, 
        key="data_editor"
    )

    if not edited_df.equals(st.session_state.main_df):
        # 데이터 정제
        edited_df['예산'] = pd.to_numeric(edited_df['예산'], errors='coerce').fillna(0)
        for col in ['대분류', '소분류', '진행상황', '메모/링크']:
            edited_df[col] = edited_df[col].fillna("").astype(str).replace(['nan', 'None'], "")
        
        st.session_state.main_df = edited_df
        edited_df.to_csv(SAVE_FILE, index=False, encoding='utf-8-sig')
        st.toast("변경사항이 자동으로 저장되었습니다!")

# --- 6. 총 예산 요약 ---
st.write("### 💰 총 예산 요약")
current_wedding_sum = edited_df['예산'].astype(float).sum()
t = st.session_state.targets

col1, col2, col3 = st.columns(3)
col1.metric("전체 예산 (목표)", f"{int(t['전체']):,} 원")
col2.metric("결혼식 예산 (목표)", f"{int(t['결혼식']):,} 원", delta=f"기획: {int(current_wedding_sum):,} 원", delta_color="off")
col3.metric("신혼집 예산 (목표)", f"{int(t['신혼집']):,} 원")
st.divider()

# --- 7. 예산 세부 구성 ---
st.write("### 📋 예산 세부 구성")
# 실제 데이터가 있는 카테고리만 추출
categories = [c for c in edited_df['대분류'].unique() if str(c).strip() != ""]

for cat in categories:
    cat_df = edited_df[edited_df['대분류'] == cat]
    cat_sum = cat_df['예산'].astype(float).sum()
    with st.expander(f"🏷️ **{cat}** (총 {int(cat_sum):,} 원)", expanded=True):
        for _, row in cat_df.iterrows():
            sub = str(row['소분류']).strip()
            if sub == "" or sub == "nan": continue
            cost, status, memo = int(float(row['예산'])), str(row['진행상황']).strip(), str(row['메모/링크']).strip()
            
            status_badge = ""
            if status and status.lower() != 'nan':
                if "완료" in status: bg, txt = "#E8F5E9", "#2E7D32"
                elif "선택" in status and "x" in status.lower(): bg, txt = "#FFF3E0", "#EF6C00"
                elif "진행" in status: bg, txt = "#E3F2FD", "#1565C0"
                else: bg, txt = "#F5F5F5", "#616161"
                status_badge = f"&nbsp; <span style='background-color:{bg}; color:{txt}; padding:2px 8px; border-radius:5px; font-size:12px; font-weight:bold;'>{status}</span>"
            
            memo_html = f"<br><span style='color:gray; font-size:13px; margin-left:15px;'>↳ {memo}</span>" if memo and memo.lower() != 'nan' else ""
            st.markdown(f"- **{sub}** : {cost:,} 원 {status_badge}{memo_html}", unsafe_allow_html=True)

st.divider()

# --- 8. 그래프 ---
st.write("### 📊 예산 비중 그래프")
summary = edited_df[edited_df['대분류'] != ""].groupby('대분류', as_index=False)['예산'].sum()
if not summary.empty:
    chart = alt.Chart(summary).mark_bar(color='#FF4B4B').encode(
        x=alt.X('대분류:N', axis=alt.Axis(labelAngle=0), sort='-y'),
        y='예산:Q'
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)