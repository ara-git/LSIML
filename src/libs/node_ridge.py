import pandas as pd
import numpy as np
import glob
from sklearn.linear_model import RidgeCV
from sklearn.linear_model import Ridge
from sklearn import preprocessing


def preprocess_for_ridge(LSIML_data, daily_data, sec):
    """
    LSIMLのデータと日次収益率データからリッジ回帰用のデータセットを作成する。
    """
    LSIML = LSIML_data["LSIML_b=" + str(sec)] + LSIML_data["Size_jump_b=" + str(sec)]

    # 移動平均、一日ずれデータを計算する
    week = LSIML.rolling(5).mean().shift()
    month = LSIML.rolling(22).mean().shift()
    shifted_LSIML = LSIML.shift()

    data = pd.concat([LSIML, shifted_LSIML, week, month], axis=1)
    data.columns = ["tom", "tod", "week", "month"]

    # ジャンプサイズについて
    data["jump"] = LSIML_data["Size_jump_b=" + str(sec)].shift()

    # 対数をとる
    data["log_tom"] = np.log(data["tom"])
    data["log_tod"] = np.log(data["tod"])
    data["log_week"] = np.log(data["week"])
    data["log_month"] = np.log(data["month"])
    # ジャンプサイズについては標準化する
    data["log_jump"] = np.log(1 + preprocessing.scale(data["jump"]))

    # 日次収益率について
    asym_list = []
    for i in range(len(daily_data)):
        asym_list.append(min([0, daily_data["daily_return"].iloc[i]]))

    data["asym"] = asym_list

    # 欠損値を削除
    data = data.dropna()

    return data


def ridge_rolling(X, Y):
    """
    リッジ回帰でローリングウィンドウの一期先予測を行う
    ハイパーパラメータαは[0.001, 0.011, 0.021,..., 0.091]からクロスバリデーションで選択する
    """
    # 学習データを作成
    train_length = len(X) // 2

    MSE_list = []
    MAE_list = []
    HMSE_list = []
    Res_list = []
    for i in range(len(X) - train_length):
        # 学習データを作成
        train_x = X.iloc[i : train_length + i]
        train_y = Y.iloc[i : train_length + i]
        # テストデータを作成
        test_x = X.iloc[train_length + i]

        # 変形
        test_x = np.array(test_x).reshape([1, len(test_x)])

        # モデルを作成
        """
        mod1 = RidgeCV(alphas=np.array(list(range(1, 101, 20))) / 1000, cv=5)
        mod1.fit(train_x, train_y)
        """

        mod1 = RidgeCV(alphas=np.array(list(range(1, 101, 20))) * 0.000001, cv=5)
        mod1.fit(train_x, train_y)
        # print(mod1.alpha_)

        pred_y = mod1.predict(test_x)

        test_y = Y.iloc[train_length + i]

        dif_ = (test_y - pred_y) ** 2
        abs_ = abs(test_y - pred_y)
        hmse_ = (1 - pred_y / test_y) ** 2

        MSE_list.append(float(dif_))
        MAE_list.append(float(abs_))
        HMSE_list.append(float(hmse_))
        # Res_list.append(test_y - pred_y)

    MSE = np.mean(MSE_list)
    MAE = np.mean(MAE_list)
    HMSE = np.mean(HMSE_list)
    # mean_res = np.mean(Res_list)

    return {
        "MSE": MSE,
        "MAE": MAE,
        "HMSE": HMSE,
    }
