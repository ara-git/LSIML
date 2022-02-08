"""
銘柄名(と何秒間隔のデータか)の情報を投げるとLSIMLの系列が返ってくるようなモジュール
"""
import pandas as pd
import numpy as np
import libs.calc_LSIML as calc_LSIML


class calc_LSIML_series:
    def __init__(self, df, b_list, alpha, overlap_rate):
        # 各種パラメータを設定する
        self.df = df
        self.b_list = b_list
        self.overlap_rate = overlap_rate
        self.alpha = alpha

        # 対数価格の列を追加
        self.df["log_price"] = np.log(self.df["price"])

        # nの一覧を取得する
        self.n_array = np.array(list(set(self.df.groupby("date")["log_price"].count())))
        self.n_array = self.n_array - np.array([1] * len(self.n_array))

        # c, C_c, P_cを計算する
        self.c_list_dict = self._calc_c_list_dict()
        self.C_c_list_dict, self.P_c_list_dict = self._calc_C_c_and_P_c_list_dict()

        # データが存在するような日付のリスト
        self.date_list = list(dict.fromkeys(self.df["date"]))

        # これらに格納していく
        self.RV_list = []
        self.LSIML_list = []
        self.num_of_detected_jump_list = []
        self.size_jump_list = []

        # 日付でグループ化する
        groups = self.df.groupby(self.df.date)

        count = 0
        for date in self.date_list:
            count += 1
            print(count)

            # LSIMLを計算する
            Y = groups.get_group(date)["log_price"]
            (
                daily_LSIML_list,
                daily_num_of_detected_jump_list,
                daily_size_jump_list,
            ) = self._calc_daily_LSIML(
                Y,
            )

            self.LSIML_list.append(daily_LSIML_list)
            self.num_of_detected_jump_list.append(daily_num_of_detected_jump_list)
            self.size_jump_list.append(daily_size_jump_list)

            # RVを計算する
            self.RV_list.append(self._calc_RV(Y))

        # 結果を出力するための準備
        self.LSIML_result_df = pd.DataFrame(
            np.array(self.LSIML_list),
            columns=[
                "LSIML_" + "b=" + str(self.b_list[0]) + "_sec1",
                "LSIML_" + "b=" + str(self.b_list[1]) + "_sec1",
                "LSIML_" + "b=" + str(self.b_list[2]) + "_sec1",
            ],
        )

        # プロット用に時間軸を保存
        time = np.array(pd.to_datetime(self.date_list))

        # RV列をdfに結合
        self.merged_result_df = pd.DataFrame([time, self.RV_list]).T
        self.merged_result_df.columns = ["date", "RV_sec1"]
        self.merged_result_df = pd.merge(
            self.merged_result_df,
            self.LSIML_result_df,
            right_index=True,
            left_index=True,
        )

    def _calc_c_list_dict(self):
        c_list_dict = {}
        for n in self.n_array:
            c_list = []
            for b in self.b_list:
                c_list.append(calc_LSIML.calc_c(n, b, self.overlap_rate))
            c_list_dict[n] = c_list

        return c_list_dict

    def _calc_C_c_and_P_c_list_dict(self):
        C_c_list_dict = {}
        P_c_list_dict = {}

        for n in self.n_array:
            c_list = self.c_list_dict[n]
            C_c_list = []
            P_c_list = []

            for c in c_list:
                C_c_list.append(calc_LSIML.calc_C_n(c))
                P_c_list.append(calc_LSIML.calc_P_n(c))

            C_c_list_dict[n] = C_c_list
            P_c_list_dict[n] = P_c_list

        return C_c_list_dict, P_c_list_dict

    def _calc_RV(self, Y):
        """
        RVを計算する関数

        """
        RV = sum(np.diff(Y) ** 2)

        return RV

    def _calc_daily_LSIML(self, Y):
        """
        各日のLSIML,ジャンプ件数,ジャンプサイズを(b毎に)計算する
        alphaやbの値は共通なので、selfで処理する。

        Aug
            Y:対数価格
        Return
            daily_LSIML_list:各bに対してLSIMLのリスト
            daily_num_of_detected_jump_list:各bに対するジャンプ検出数のリスト
            daily_size_jump_list:各bに対するジャンプサイズのリスト
        """
        # 対数価格を抽出し、NANを除去する
        n = len(Y) - 1
        Y = np.array(Y)

        daily_LSIML_list = []
        daily_num_of_detected_jump_list = []
        daily_size_jump_list = []

        # 各bに対して、LSIMLを計算する
        for j in range(len(self.b_list)):
            b = self.b_list[j]
            c = self.c_list_dict[n][j]
            C_c = self.C_c_list_dict[n][j]
            P_c = self.P_c_list_dict[n][j]
            # を計算する。
            ##quantileの手法でジャンプ検出を行う
            result_dict = calc_LSIML.calc_LSIML(
                Y,
                b,
                c,
                self.alpha,
                C_c,
                P_c,
                n,
                jump_detect=True,
                how_to_detect="quantile",
                overlap_rate=self.overlap_rate,
            )
            daily_LSIML_list.append(result_dict["LSIML"])
            daily_num_of_detected_jump_list.append(result_dict["num_of_detected_jump"])
            daily_size_jump_list.append(result_dict["sum_of_jump"])

        return daily_LSIML_list, daily_num_of_detected_jump_list, daily_size_jump_list


if __name__ == "__main__":
    stock_name_list = list(pd.read_csv("company_name.txt", header=None)[0])

    stock_name = stock_name_list[0]
    df = pd.read_csv("data/" + stock_name + "_1sec.csv")

    # コマンドライン引数を読み込む
    alpha = 0.4
    overlap_rate = 0
    b_list = [10, 50, 100]

    Ins = calc_LSIML_series(df, b_list=b_list, alpha=alpha, overlap_rate=overlap_rate)
    LSIML_RV_df = Ins.merged_result_df

    LSIML_RV_df.to_csv("LSIML_RV_" + stock_name + "csv", index=False, header=None)
