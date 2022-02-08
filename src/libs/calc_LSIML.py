import numpy as np
import math
import outlier


def calc_C_n(n):
    """
    C_n(本当はインバース)を計算する。
    """
    C_n = np.zeros([n, n])
    for i in range(n):
        C_n[i][i] = 1
        if i != n - 1:
            C_n[i + 1][i] = -1
    C_n = np.array(C_n)
    return C_n


def calc_P_n(n):
    """
    P_nを計算する
    """
    P_n = np.zeros([n, n])
    for j in range(n):
        for k in range(
            n
        ):  # k = 0, 1, ..., n - 1, j = 0, 1, ,..., n - 1（論文だと1, 2,..., n）なので、少し式を工夫している
            P_n[j][k] = math.sqrt(2 / (n + 0.5)) * math.cos(
                2 * math.pi / (2 * n + 1) * ((k + 1) - 0.5) * ((j + 1) - 0.5)
            )
    P_n = np.array(P_n)

    return P_n


# bに対応したcを計算する関数
def calc_c(n, b, overlap_rate):
    c = int(n / (((b - 1) * (1 - overlap_rate) + 1)))
    return c


def calc_Z_n(Y, C_n, P_n, n):
    """
    対数価格系列YをZ_nに変換する関数(Yの長さ = Z_nの長さ + 1、初期値を含めるため)
    Augs
        Y:対数価格系列
        C_n:Yの長さに対応した行列
        P_n:同上
        n:Yの長さ - 1
    Returns
        Z_n:計算されたZ_n
    """
    # Y_diff = Y_n - Y_0を計算する
    ## 最初の価格で引き算
    Y_diff = Y - Y[0]
    Y_diff = Y_diff[1:]
    Y_diff = Y_diff.reshape([n, 1])

    # Z_nを求める。（√n,P_n, C_nをかける）
    Z_n = math.sqrt(n) * P_n.dot(C_n).dot(Y_diff)

    return Z_n


def calc_SIML(Z_n, m):
    """
    SIMLを計算する関数

    Augs
        Z_n:Zは観測された対数株価を変換したもの
        m:計算に用いるデータの個数
    Returns
        SIML:計算されたSIML
    """
    # Sigma_xを計算する。
    ##最初のm個のデータの二乗平均を計算する
    Sigma_x = 0

    for k in range(int(np.round(m))):
        Sigma_x += Z_n[k] ** 2

    Sigma_x /= np.round(m)
    # print("Σ_x:", Sigma_x)

    SIML = Sigma_x[0]
    return SIML


def calc_LSIML(
    Y,
    b,
    c,
    alpha,
    C_c,
    P_c,
    n,
    jump_detect=False,
    how_to_detect="quantile",
    overlap_rate=0,
):
    """
    (Overlap) LSIMLを計算する関数
    Augs
        Y:観測系列
        b:ブロックの数
        c:ブロック一つ辺りの観測数
        alpha:SIMLの計算に使うα
        C_c、P_c:LSIMLの計算に用いる行列
        overlap_rate:Overlapping LSIMLを計算したいときに使う、重複度合い
    Return:
        LSIML:計算されたLSIML
        LSIML_list:M_n(i)のリスト
        sum_of_jump:検出されたジャンプの(二乗の)総和
        num_of_detected_jump:検出されたジャンプの回数
        の辞書
    """
    # 各ブロックにおける計算に使うデータの個数を表すmを計算する。
    m = c ** alpha

    # LSIML = 0
    LSIML_list = []

    for i in range(b):
        # print(i)
        # Yを分割し、i個目のグループについて考える。長さはc + 1（なぜなら、初期値を含めるから。初期値は一個前のグループの最後の値）

        ##始点を計算する際に必要なc_を設定する。
        c_ = int((1 - overlap_rate) * c)
        Y_c = Y[i * c_ : i * c_ + c + 1]

        ##関数を使って変換を行う。
        ##Z_cの長さはc
        Z_c = calc_Z_n(Y_c, C_c, P_c, c)

        # 関数を使ってSIMLを計算し、足し合わせていく
        LSIML_list.append(calc_SIML(Z_c, m))

    if jump_detect:
        # 外れ値の除去を行う（デフォルト）
        ##スルミノフ・グラノフ検定を使う（デフォルト）
        if how_to_detect == "smi":
            # 対数を取ったものにsmitestを行い、それをnp.expで戻す
            removed_LSIML_list = np.exp(outlier.smi_test(np.log(LSIML_list)).removed)

        ##quantileに基づいた手法を用いる
        elif how_to_detect == "quantile":
            removed_LSIML_list = outlier.quantile(LSIML_list).removed

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
    return {
        "LSIML": LSIML,
        "LSIML_list": LSIML_list,
        "sum_of_jump": sum_of_jump,
        "num_of_detected_jump": num_of_detected_jump,
    }
