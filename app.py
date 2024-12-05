# app.py
import streamlit as st
import json
from models import Patient, Solution, InfusionMix
from calculation import calculate_infusion
from pydantic import ValidationError
import logging
import os
import pandas as pd
import io

# ユーティリティ関数をインポート
from utils import setup_logging

# ログの設定
setup_logging()

# ログ出力
logger = logging.getLogger()

# ページの設定
st.set_page_config(
    page_title="TPN 配合計算アプリケーション",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSSの適用（オプション）
st.markdown(
    """
    <style>
    .main {
        background-color: #F0F2F6;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
    }
    .warning {
        color: #FF0000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 輸液製剤のデータをロード
def load_solutions(file_path='data/solutions.json'):
    try:
        # スクリプトのディレクトリを基準に絶対パスを作成
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            solutions_data = json.load(f)
        solutions = [Solution(**sol) for sol in solutions_data]
        logger.debug("製剤データのロードに成功しました。")
        return solutions
    except FileNotFoundError:
        logger.error(f"製剤データファイルが見つかりません: {file_path}")
        st.error(f"製剤データファイルが見つかりません: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"製剤データファイルのJSON解析エラー: {e}")
        st.error(f"製剤データファイルのJSON解析エラー: {e}")
        return []

# Streamlit Appのメイン関数
def main():
    st.title("TPN 配合計算アプリケーション")
    st.markdown("---")
    
    # 輸液製剤のロード
    solutions = load_solutions()
    
    if not solutions:
        st.stop()  # 製剤データがロードできない場合、アプリを停止
    
    # 患者情報と製剤選択のフォーム
    with st.form(key='infusion_form'):
        st.header("患者情報の入力")
        col1, col2 = st.columns(2)
        
        with col1:
            weight = st.number_input("体重 (kg)", min_value=0.1, max_value=10.0, value=1.33, step=0.01)
            twi = st.number_input("TWI (mL/kg/day)", min_value=50.0, max_value=200.0, value=110.0, step=1.0)
            
            gir_included = st.checkbox("GIRを条件に含める", value=True)
            gir = st.number_input("GIR (mg/kg/min)", min_value=4.0, max_value=10.0, value=7.0, step=0.1, disabled=not gir_included)
        
        with col2:
            amino_acid_included = st.checkbox("アミノ酸量を条件に含める", value=True)
            amino_acid = st.number_input("アミノ酸量 (g/kg/day)", min_value=2.0, max_value=4.0, value=3.0, step=0.1, disabled=not amino_acid_included)
            
            na_included = st.checkbox("Na量を条件に含める", value=True)
            na = st.number_input("Na量 (mEq/kg/day)", min_value=2.0, max_value=4.0, value=2.5, step=0.1, disabled=not na_included)
            
            k_included = st.checkbox("K量を条件に含める", value=True)
            k = st.number_input("K量 (mEq/kg/day)", min_value=1.0, max_value=3.0, value=1.5, step=0.1, disabled=not k_included)
            
            p_included = st.checkbox("P量を条件に含める", value=True)
            p = st.number_input("P量 (mmol/kg/day)", min_value=1.0, max_value=3.0, value=1.5, step=0.1, disabled=not p_included)
        
        st.header("輸液製剤の選択")
        selected_solution_name = st.selectbox("ベース製剤を選択してください", [sol.name for sol in solutions])
        selected_solution = next((sol for sol in solutions if sol.name == selected_solution_name), None)
        
        submit_button = st.form_submit_button(label='配合を計算')
    
    if submit_button:
        with st.spinner('計算中...'):
            try:
                # Patientオブジェクトの作成
                patient = Patient(
                    weight=weight,
                    twi=twi,
                    gir=gir if gir_included else None,
                    gir_included=gir_included,
                    amino_acid=amino_acid if amino_acid_included else None,
                    amino_acid_included=amino_acid_included,
                    na=na if na_included else None,
                    na_included=na_included,
                    k=k if k_included else None,
                    k_included=k_included,
                    p=p if p_included else None,
                    p_included=p_included
                )
                logger.debug(f"患者データ: {patient}")
                
                logger.debug(f"選択された製剤: {selected_solution}")
                
                # 計算の実行
                infusion_mix = calculate_infusion(patient, selected_solution)
                logger.debug(f"計算結果: {infusion_mix}")
                
                # 計算結果をセッションステートに保存
                st.session_state['infusion_mix'] = infusion_mix
                
            except ValidationError as e:
                st.error("入力値に誤りがあります。再度確認してください。")
                logger.error(f"ValidationError: {e}")
            except ValueError as ve:
                st.error(str(ve))
                logger.error(f"ValueError: {ve}")
            except Exception as e:
                st.error("計算中にエラーが発生しました。詳細はログを確認してください。")
                logger.error(f"Unexpected error: {e}")

    # 計算結果の表示
    if 'infusion_mix' in st.session_state:
        infusion_mix = st.session_state['infusion_mix']
        
        st.markdown("---")
        st.header("計算結果")
        
        # 計算結果を2つのカラムに分割して表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("基本情報")
            if infusion_mix.gir is not None:
                st.write(f"**GIR:** {infusion_mix.gir:.2f} mg/kg/min")
            if infusion_mix.amino_acid is not None:
                st.write(f"**アミノ酸量:** {infusion_mix.amino_acid:.2f} g/kg/day")
            if infusion_mix.na is not None:
                st.write(f"**Na量:** {infusion_mix.na:.2f} mEq/kg/day")
        
        with col2:
            st.subheader("その他の栄養素")
            if infusion_mix.k is not None:
                st.write(f"**K量:** {infusion_mix.k:.2f} mEq/kg/day")
            if infusion_mix.p is not None:
                st.write(f"**P量:** {infusion_mix.p:.2f} mmol/kg/day")
        
        st.subheader("混合溶液の詳細")
        # 混合溶液の詳細を表形式で表示
        df = {
            "製剤名": list(infusion_mix.detailed_mix.keys()),
            "必要量 (mL/day)": [f"{value:.2f}" for value in infusion_mix.detailed_mix.values()]
        }
        st.table(df)
        
        st.subheader("計算ステップの詳細")
        with st.expander("計算ステップを表示"):
            # Markdown形式で計算ステップを整形
            steps_formatted = infusion_mix.calculation_steps.replace("\n", "\n")
            st.markdown(f"**計算ステップ:**\n\n{steps_formatted}")
            st.info("各計算ステップを確認してください。")
        
        # (オプション) 計算結果のダウンロード
        with st.expander("計算結果をダウンロード"):
            # データの収集
            rows = []
            if infusion_mix.gir is not None:
                rows.append({"項目": "GIR (mg/kg/min)", "値": infusion_mix.gir})
            if infusion_mix.amino_acid is not None:
                rows.append({"項目": "アミノ酸量 (g/kg/day)", "値": infusion_mix.amino_acid})
            if infusion_mix.na is not None:
                rows.append({"項目": "Na量 (mEq/kg/day)", "値": infusion_mix.na})
            if infusion_mix.k is not None:
                rows.append({"項目": "K量 (mEq/kg/day)", "値": infusion_mix.k})
            if infusion_mix.p is not None:
                rows.append({"項目": "P量 (mmol/kg/day)", "値": infusion_mix.p})
            
            # データフレームを作成
            if rows:
                results_df = pd.DataFrame(rows)
            else:
                results_df = pd.DataFrame(columns=["項目", "値"])
            
            # バッファに書き込み
            buffer = io.BytesIO()
            results_df.to_csv(buffer, index=False, encoding='utf-8-sig')
            buffer.seek(0)
            
            st.download_button(
                label="CSVとしてダウンロード",
                data=buffer,
                file_name="infusion_results.csv",
                mime="text/csv",
            )

# メイン関数の呼び出し
if __name__ == "__main__":
    main()
