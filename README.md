# TPN Calculator Streamlit App

TPN（Total Parenteral Nutrition）配合計算アプリケーションです。このアプリは、患者の体重や必要な栄養素の量を入力し、選択した輸液製剤の組成データに基づいて必要な配合量を計算します。特に新生児をターゲットにしています。

## 特徴

- 患者情報の簡単な入力
- 輸液製剤の選択
- 必要なGIR、アミノ酸量、Na量、K量、P量の計算
- 混合溶液の詳細表示
- 詳細なログ出力によるデバッグ支援
- ユニットテストによる計算ロジックの検証

## セットアップ

### 必要条件

- Python 3.8以上
- Poetryパッケージマネージャー

### インストール手順

1. **Poetryのインストール**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   インストール後、シェルを再起動するか、以下を実行してパスを更新:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **プロジェクトのクローン**
   ```bash
   git clone https://github.com/yourusername/TPNCalculatorStreamlit.git
   cd TPNCalculatorStreamlit
   ```

3. **依存関係のインストール**
   ```bash
   poetry install
   ```
   これにより、poetry.lock に記録された正確なバージョンのパッケージがインストールされます。

4. **requirements.txt の生成**
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```
   Streamlit Cloudへのデプロイ用にrequirements.txtを生成します。

5. **アプリケーションの実行**
   ```bash
   poetry run streamlit run app.py
   ```
   ブラウザが自動的に開き、TPN配合計算アプリケーションが表示されます。

6. **ユニットテストの実行**
   ```bash
   poetry run pytest tests/test_calculation.py
   ```
   計算ロジックの正確性を検証します。