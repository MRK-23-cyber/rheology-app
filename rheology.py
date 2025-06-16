import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker # 축 눈금 포맷 변경을 위해 임포트
import io

# --- 코드 설정 ---
COLUMN_NAMES = {
    'frequency': 'Angular Frequency',
    'g_prime': 'Storage modulus',
    'g_double_prime': 'Loss modulus',
    'complex_viscosity': "Complex viscosity"
}
# -----------------

def create_rheology_plot(dataframes_with_names, x_col, y_col, title, x_label, y_label):
    """
    유변학 데이터를 받아 Matplotlib 그래프를 생성하는 함수.
    (최종 수정: 축 눈금 포맷을 강제로 변경하여 렌더링 오류 해결)
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_success_count = 0

    for df, name in dataframes_with_names:
        if df.empty:
            st.warning(f"파일 '{name}'에서 유효한 수치 데이터를 찾을 수 없어 그래프를 그릴 수 없습니다.")
            continue

        df.columns = [c.strip().lower() for c in df.columns]
        target_x_col_lower = x_col.lower()
        target_y_col_lower = y_col.lower()

        actual_x_col = next((c for c in df.columns if target_x_col_lower in c), None)
        actual_y_col = next((c for c in df.columns if target_y_col_lower in c), None)

        if actual_x_col and actual_y_col:
            ax.plot(df[actual_x_col], df[actual_y_col], marker='o', linestyle='-', label=name)
            plot_success_count += 1
        else:
            st.warning(f"파일 '{name}'에서 '{x_col}' 또는 '{y_col}'을(를) 포함하는 컬럼을 찾지 못했습니다.")
            return None, None
    
    if plot_success_count > 0:
        ax.set_xscale('log')
        ax.set_yscale('log')

        # --- ★★★★★ 오류 해결을 위한 핵심 코드 ★★★★★ ---
        # 축 눈금을 과학적 표기법(10^3)이 아닌 일반 숫자(1000)로 강제 변환
        ax.xaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        # ----------------------------------------------------

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold')
        ax.grid(True, which="both", ls="--", linewidth=0.5)
        ax.legend()
        
        # tight_layout()은 모든 요소가 그려진 후 호출되어야 함
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300)
        buf.seek(0)
        return fig, buf
    else:
        return None, None

# --- Streamlit 앱 UI 구성 (이하 코드는 이전과 동일) ---
st.set_page_config(layout="wide")
st.title("🔬 고분자 유변 물성 분석기 (Frequency Sweep)")
st.markdown("""
- **Polyester Elastomer**와 같은 고분자 샘플의 **Frequency Sweep** 데이터를 분석합니다.
- 여러 개의 **엑셀 파일**(.xlsx, .xls)을 업로드하면 **저장탄성률(G'), 손실탄성률(G''), 복합점도(η\*)** 그래프가 자동으로 생성됩니다.
- 그래프는 모든 샘플에 대해 **오버레이** 되어 손쉽게 비교할 수 있습니다.
- 각 그래프 아래의 **다운로드 버튼**을 눌러 이미지로 저장할 수 있습니다.
""")

st.sidebar.info("""
**앱 사용법**
1. 분석할 엑셀 파일들을 위 업로더에 드래그 앤 드롭하거나 선택하세요.
2. 그래프가 자동으로 생성됩니다.
3. 필요하면 그래프 아래의 다운로드 버튼을 클릭해 이미지를 저장하세요.

**파일 형식 안내**
이 앱은 아래 구조의 엑셀 파일을 기준으로 동작합니다.
- **두 번째 시트**에 데이터가 위치
- **두 번째 행**에 컬럼 이름(헤더)이 위치
- **세 번째 행**은 단위 정보 (자동으로 무시됨)
""")
st.sidebar.markdown("---")
st.sidebar.header("코드 설정 참고")
st.sidebar.caption("앱이 컬럼을 찾지 못할 경우, 아래 이름을 기준으로 코드 상단의 `COLUMN_NAMES`를 수정하세요.")
st.sidebar.json(COLUMN_NAMES)

uploaded_files = st.file_uploader(
    "RDS 데이터 엑셀 파일을 업로드하세요 (.xlsx, .xls)",
    accept_multiple_files=True,
    type=['xlsx', 'xls']
)

if uploaded_files:
    dataframes = []
    debug_info = []

    for uploaded_file in uploaded_files:
        try:
            file_name = uploaded_file.name
            engine = 'openpyxl' if file_name.lower().endswith('.xlsx') else 'xlrd'
            df_original = pd.read_excel(uploaded_file, engine=engine, sheet_name=1, header=1)
            df_processed = df_original.iloc[1:].reset_index(drop=True)
            for col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
            df_processed.dropna(inplace=True)
            dataframes.append((df_processed, file_name))
            debug_info.append({
                'name': file_name, 
                'original_columns': df_original.columns.tolist(), 
                'original_head': df_original.head(),
                'processed_head': df_processed.head(),
                'processed_dtypes': df_processed.dtypes.to_dict()
            })
        except Exception as e:
            st.error(f"'{uploaded_file.name}' 파일을 처리하는 중 오류가 발생했습니다: {e}")

    if dataframes:
        st.header("📈 분석 결과 그래프")
        
        st.subheader("1. Storage Modulus (G') vs. Frequency")
        fig_g_prime, buf_g_prime = create_rheology_plot(dataframes, COLUMN_NAMES['frequency'], COLUMN_NAMES['g_prime'], "Storage Modulus vs. Angular Frequency", "Angular Frequency (rad/s)", "Storage Modulus (Pa)")
        if fig_g_prime:
            st.pyplot(fig_g_prime)
            st.download_button("G' 그래프 다운로드 (PNG)", buf_g_prime, "storage_modulus.png", "image/png")

        st.subheader("2. Loss Modulus (G'') vs. Frequency")
        fig_g_double_prime, buf_g_double_prime = create_rheology_plot(dataframes, COLUMN_NAMES['frequency'], COLUMN_NAMES['g_double_prime'], "Loss Modulus vs. Angular Frequency", "Angular Frequency (rad/s)", "Loss Modulus (Pa)")
        if fig_g_double_prime:
            st.pyplot(fig_g_double_prime)
            st.download_button("G'' 그래프 다운로드 (PNG)", buf_g_double_prime, "loss_modulus.png", "image/png")

        st.subheader("3. Complex Viscosity vs. Frequency")
        fig_viscosity, buf_viscosity = create_rheology_plot(dataframes, COLUMN_NAMES['frequency'], COLUMN_NAMES['complex_viscosity'], "Complex Viscosity vs. Angular Frequency", "Angular Frequency (rad/s)", "Complex Viscosity (Pa.s)")
        if fig_viscosity:
            st.pyplot(fig_viscosity)
            st.download_button("복합점도 그래프 다운로드 (PNG)", buf_viscosity, "complex_viscosity.png", "image/png")

        with st.expander("파일 구조 및 데이터 처리 결과 확인 (디버깅 정보)"):
            for info in debug_info:
                st.subheader(f"📄 파일: {info['name']}")
                st.markdown("**1. 원본 파일에서 읽어온 컬럼 이름 목록:**")
                st.write(info['original_columns'])
                st.markdown("**2. 최종 처리된 데이터의 컬럼별 타입:**")
                st.json({k: str(v) for k, v in info['processed_dtypes'].items()})
                st.markdown("**3. 최종 처리된 데이터 미리보기:**")
                st.dataframe(info['processed_head'])
                st.markdown("---")