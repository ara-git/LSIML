# LSIML
LSIMLを計算するモジュール

## How to use
### データを用意する
まず、grid_dataフォルダ内に株価のデータを用意する。
データ形式は等間隔で観測されたもの（例えば、１秒間隔）を仮定している。
また、
- date
- price
列が必須である。

具体的な形式は`"grid_data/sample.csv"`を参照されたい。

### パラメータを設定する
`setting\parameters.txt`でパラメータを設定する。具体的には
- alpha: SIML, LSIMLを計算する際に用いるα
- b: LSIMLを計算する際に用いるb
- overlap_rate: overlap LSIMLを計算する際に用いる重複比率（デフォルトでは0）

### 計算を実行する
データが用意出来たら、`src/calc_LSIML_series.py`を実行する。

ターミナル上で
`python src/calc_LSIML_series.py`
と打てばよい。

計算結果は`output`フォルダ内に出力される。