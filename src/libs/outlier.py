# -*- coding: utf-8 -*-
"""
- ホテリング理論
- スミルノフ・グラブス検定
- 四分位範囲による除去

を用いた外れ値検出を行うクラスを実装。
"""

import numpy as np
from scipy.stats import chi2
import math
from scipy.stats import t


class hotelling:
    """
    ホテリング理論で外れ値を除去する
    """

    # 引数:
    # array:データ（一次元)、alpha:上側確率
    def __init__(self, array, alpha=0.01):
        # 平均と分散を計算する
        sample_var = np.var(array, ddof=1)
        sample_mean = np.mean(array)
        # 閾値を計算する
        border = chi2.ppf(q=1 - alpha, df=1)
        # データを標準化する
        converted_data = (array - sample_mean) ** 2 / sample_var
        # 外れ値を除外したデータを求める
        self.result = array[converted_data < border]
        # 外れ値の比率を求める
        self.rate_of_outlier = sum(converted_data >= border) / len(array)


class smi_test:
    """
    スミルノフ・グラブス検定を行う
    """

    def __init__(self, array, alpha=0.01):
        array = np.array(array)

        # 入力配列を属性として保存
        self.input_array = array
        self.alpha = alpha

        # データを除去していくため、入力配列のコピーを作る
        tmp_array = array.copy()
        # print(tmp_array)
        # 下で定義した関数を繰り返し呼び出し、再帰的に外れ値を除去する

        while tmp_array.any():
            # 外れ値を除去したデータが格納されているメソッド
            self.removed = tmp_array.copy()
            tmp_array = self.run_test(tmp_array)

    def run_test(self, array):
        # 標本平均と分散を計算する
        sample_var = np.var(array, ddof=1)
        sample_mean = np.mean(array)

        # 統計量を計算する（最大値の）
        statistics_smi = abs(max(array) - sample_mean) / math.sqrt(sample_var)
        statistics_smi

        # 閾値を計算する。
        n = len(array)
        t_value = t.ppf(q=1 - self.alpha / n, df=n - 2)
        # print(t_value)

        border_smi = (n - 1) * (t_value ** 2 / (n * (n - 2) + n * t_value ** 2)) ** (
            0.5
        )
        # print(statistics_smi, border_smi)

        if statistics_smi >= border_smi:
            new_array = np.delete(array, array == max(array))
            return new_array
        else:
            return np.array([])

    # 外れ値の割合を出力する関数
    def rate_of_outlier(self):
        return len(self.result) / len(self.input_array)


class quantile:
    """
    四分位範囲を利用した外れ値除去（参考：https://www.monotalk.xyz/blog/Calculate-the-interquartile-range-with-python/）
    今回はLSIML用に、下側の除去は行わない
    """

    def __init__(self, array):
        # 第一四分位数と第三四分位数、四分位範囲を計算する。
        quartile_1, quartile_3 = np.percentile(array, [25, 75])
        iqr = quartile_3 - quartile_1

        # 下限
        lower_bound = quartile_1 - (iqr * 1.5)
        # 上限
        upper_bound = quartile_3 + (iqr * 1.5)

        # 下限以上、上限未満の値のみ抽出
        # removed = np.array(array)[((array < upper_bound) & (array >= lower_bound))]

        # 上限未満の値のみ抽出
        removed = np.array(array)[(array < upper_bound)]
        self.removed = removed
