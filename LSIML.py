import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import outlier

# 対数価格系列YをZ_nに変換する関数(Yの長さ = Z_nの長さ + 1、初期値を含めるため)
def calc_Z_n(Y, C_n, P_n, n):
    # Y_diff = Y_n - Y_0を計算する
    ##最初の価格で引き算
    Y_diff = Y - Y[0]
    Y_diff = Y_diff[1:]
    Y_diff = Y_diff.reshape([n, 1])
    Y_diff

    # Z_nを求める。（√n,P_n, C_nをかける）
    Z_n = math.sqrt(n) * P_n.dot(C_n).dot(Y_diff)

    return Z_n


# Sigma_xを計算する関数
def func_of_SIML(Z_n, m):  # Zは観測された対数株価を変換したもの
    # Sigma_xを計算する。
    ##最初のm個のデータの二乗平均を計算する
    Sigma_x = 0

    for k in range(int(np.round(m))):
        Sigma_x += Z_n[k] ** 2

    Sigma_x /= np.round(m)
    # print("Σ_x:", Sigma_x)

    return Sigma_x[0]


# データ系列から外れ値を除去する関数
##四分位範囲を利用している。（参考：https://www.monotalk.xyz/blog/Calculate-the-interquartile-range-with-python/）
def identify_outliers(ys):
    # 第一四分位数と第三四分位数、四分位範囲を計算する。
    quartile_1, quartile_3 = np.percentile(ys, [25, 75])
    iqr = quartile_3 - quartile_1
    # 下限
    lower_bound = quartile_1 - (iqr * 1.5)
    # 上限
    upper_bound = quartile_3 + (iqr * 1.5)

    # 下限以上、上限未満の値のみ抽出
    # removed = np.array(ys)[((ys < upper_bound) & (ys >= lower_bound))]

    # 上限未満の値のみ抽出
    removed = np.array(ys)[(ys < upper_bound)]

    # print("detected number of jumps:", len(ys) - len(removed))

    # print(lower_bound, upper_bound)
    return removed


# Overlap LSIMLを計算する関数
# 引数：Y：観測系列、b：ブロックの数、c：ブロック一つ辺りの観測数、Overlap_rate：重複度合い、alpha：SIMLの計算に使うα、C_c、P_c
def func_of_LSIML_overlap(
    Y, b, c, alpha, overlap_rate, C_c, P_c, n, jump_detect=True, how_to_detect="smi"
):
    # 各ブロックにおける計算に使うデータの個数を表すmを計算する。
    m = c ** alpha

    # LSIML = 0
    LSIML_list = []

    for i in range(b):
        # print(i)
        # Yを分割し、i個目のグループについて考える。長さはc + 1（なぜなら、初期値を含めるから。初期値は一個前のグループの最後の値）

        ##始点を計算する際に必要なc_を設定する。
        c_ = int((1 - overlap_rate) * c)
        # print("c_:", c_)
        Y_c = Y[i * c_ : i * c_ + c + 1]
        # print([i * c_, i * c_ + c + 1])
        # print("len(Y_c):", len(Y_c))

        ##関数を使って変換を行う。
        ##Z_cの長さはc
        Z_c = calc_Z_n(Y_c, C_c, P_c, c)
        # print("len(Z_c):", len(Z_c))

        # 関数を使ってSIMLを計算し、足し合わせていく
        # LSIML += func_of_SIML(Z_c, m)
        LSIML_list.append(func_of_SIML(Z_c, m))

    if jump_detect:
        # 外れ値の除去を行う（デフォルト）
        ##スルミノフ・グラノフ検定を使う（デフォルト）
        if how_to_detect == "smi":
            # 対数を取ったものにsmitestを行い、それをnp.expで戻す
            removed_LSIML_list = np.exp(outlier.smi_test(np.log(LSIML_list)).result)

        ##quantileに基づいた手法を用いる
        elif how_to_detect == "quantile":
            removed_LSIML_list = identify_outliers(LSIML_list)
        ##how_to_detect変数が"smi"でも"quantile"でもなければエラーを吐く
        else:
            assert False

        # LSIMLを求める
        LSIML = sum(removed_LSIML_list)
        sum_of_jump = sum(LSIML_list) - LSIML

        # ジャンプの検出数を求める
        num_of_detected_jump = len(LSIML_list) - len(removed_LSIML_list)
        # print("detected number of jumps:", num_of_detected_jump)
    else:
        # 外れ値の除去を行わない
        LSIML = sum(LSIML_list)
        sum_of_jump = None
        num_of_detected_jump = None

    # overlap分の補正を行う
    LSIML = LSIML * (n / (n + overlap_rate * c * (b - 1)))
    return LSIML, LSIML_list, sum_of_jump, num_of_detected_jump
