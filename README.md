# LSIML
秒間隔株式データから、各日のLSIMLを計算するモジュール

出力はcsv形式であり、
- date: 日付
- RV_sec1: Realized Volatilityの値
- LSIML_b=x: LSIMLの値（ジャンプ除去済み）
- Num_jump_b=x: 検出されたジャンプ回数
- Size_jump_b=x: 検出されたジャンプサイズ

列が含まれる。

尚、xの部分には自分で設定したbの値が保存される。

ジャンプ除去を行わないLSIMLの値は`LSIML_b=x`列に`Size_jump_b=x`列を加算すれば良い。

出力サンプルは
`output/output_sample.csv`を参照されたい。

## How to use
### データを用意する
まず、`data/grid_data`フォルダ内に株価のデータを用意する。
データ形式は等間隔で観測されたもの（例えば、１秒間隔）を仮定している。
また、
- `date`
- `price`
列が必須である。

具体的な形式は`"data/grid_data/sample.csv"`を参照されたい。

### パラメータを設定する
`setting\parameters.txt`でパラメータを設定する。具体的には
- `alpha`: SIML, LSIMLを計算する際に用いるα
- `b`: LSIMLを計算する際に用いるb
- `overlap_rate`: overlap LSIMLを計算する際に用いる重複比率（デフォルトでは0）

### 計算を実行する
データが用意出来たら、`src/calc_LSIML_series.py`を実行する。

ターミナル上で
`python src/calc_LSIML_series.py`
と打てばよい。

計算結果は`output`フォルダ内に出力される。