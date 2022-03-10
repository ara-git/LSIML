"""
リッジ回帰で予測を行う
"""

import pandas as pd
import glob

import libs.node_ridge as node_ridge

# LSIMLのデータ
LSIML_data_list = glob.glob("output/*.csv")
LSIML_data_list

# 日次収益率のデータ
daily_data_list = glob.glob("data/daily_data/*.csv")
daily_data_list

sec = 50

for i in range(len(LSIML_data_list)):
    # データを読み込む
    LSIML_data = pd.read_csv(LSIML_data_list[i])
    daily_data = pd.read_csv(daily_data_list[i]).shift()

    # データを前処理する
    data = node_ridge.preprocess_for_ridge(LSIML_data, daily_data, sec)
    print(LSIML_data_list[i])
    print(daily_data_list[i])

    # print(data)
    # リッジ回帰で予測する
    """
    # 元系列に対して、非対称性が存在するか確かめる
    x_names = ["tod", "week", "month", "asym", "jump"]
    ridge = Ridge().fit(data[x_names], data["tom"])

    # 係数を出力する
    res_coef = pd.DataFrame(ridge.coef_).T 
    res_coef.columns = x_names
    res_coef
    """

    """
    非対数モデル
    """

    x_names = ["tod", "week", "month"]
    X = data[x_names]
    Y = data["tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["tod", "week", "month", "jump"]
    X = data[x_names]
    Y = data["tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["tod", "week", "month", "asym"]
    X = data[x_names]
    Y = data["tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["tod", "week", "month", "asym", "jump"]
    X = data[x_names]
    Y = data["tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    """
    対数モデル
    """
    x_names = ["log_tod", "log_week", "log_month"]
    X = data[x_names]
    Y = data["log_tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["log_tod", "log_week", "log_month", "log_jump"]
    X = data[x_names]
    Y = data["log_tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["log_tod", "log_week", "log_month", "asym"]
    X = data[x_names]
    Y = data["log_tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)

    ####
    x_names = ["log_tod", "log_week", "log_month", "log_jump", "asym"]
    X = data[x_names]
    Y = data["log_tom"]

    result = node_ridge.ridge_rolling(X, Y)
    print(x_names, result)
