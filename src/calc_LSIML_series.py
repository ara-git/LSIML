"""
data/grid_dataディレクトリにあるcsvファイルを全て読み込み、LSIMLの系列を計算するモジュール
"""
import glob
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
        col_name_list = []
        for i in range(len(self.b_list)):
            col_name_list.append("LSIML_" + "b=" + str(self.b_list[i]))

        self.LSIML_result_df = pd.DataFrame(
            np.array(self.LSIML_list),
            columns=col_name_list,
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

        # 検出したジャンプ数に関する列をdfに結合
        col_name_list = []
        for i in range(len(self.b_list)):
            col_name_list.append("Num_jump_" + "b=" + str(self.b_list[i]))

        self.num_of_detected_jump_df = pd.DataFrame(
            self.num_of_detected_jump_list,
            columns=col_name_list,
        )

        # ジャンプの二乗和に関するdfを作成
        col_name_list = []
        for i in range(len(self.b_list)):
            col_name_list.append("Size_jump_" + "b=" + str(self.b_list[i]))

        self.size_jump_df = pd.DataFrame(
            self.size_jump_list,
            columns=col_name_list,
        )

        # dfを作成
        self.merged_result_df = pd.merge(
            self.merged_result_df,
            self.num_of_detected_jump_df,
            right_index=True,
            left_index=True,
        )
        self.merged_result_df = pd.merge(
            self.merged_result_df, self.size_jump_df, right_index=True, left_index=True
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
        Y = Y.dropna()
        RV = sum(np.diff(Y) ** 2)

        return RV

    def _calc_daily_LSIML(self, Y):
        """
        各日のLSIML,ジャンプ件数,ジャンプサイズを(b毎に)計算する
        alphaやbの値は共通なので、selfで処理する。

        Aug
            Y:対数価格(dataframe形式)
        Return
            daily_LSIML_list:各bに対してLSIMLのリスト
            daily_num_of_detected_jump_list:各bに対するジャンプ検出数のリスト
            daily_size_jump_list:各bに対するジャンプサイズのリスト
        """
        # 対数価格を抽出し、NANを除去する
        n = Y.count() - 1
        Y = Y.dropna()
        # print(n)
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
    # dataディレクトリにあるcsvファイルを全て読み込む
    stock_name_list = glob.glob("data/grid_data/*.csv")

    # パラメータを設定する（値はtxtファイルから読み込む）
    param_df = pd.read_csv("setting/parameters.txt", sep=", ")

    alpha = float(param_df[param_df["parameter"] == "alpha"].value.iloc[0])
    overlap_rate = float(
        param_df[param_df["parameter"] == "overlap_rate"].value.iloc[0]
    )

    # bのみ複数の値を設定したいので、リストとする
    b_list = list(map(int, param_df[param_df["parameter"] == "b"]["value"]))

    # 各銘柄ごとにLSIMLの系列を計算し、csv形式で出力する
    for stock_name in stock_name_list:
        print(stock_name)
        df = pd.read_csv(stock_name)

        Ins = calc_LSIML_series(
            df, b_list=b_list, alpha=alpha, overlap_rate=overlap_rate
        )
        LSIML_RV_df = Ins.merged_result_df

        # 保存用に名称変更
        stock_name = stock_name.replace("data\\", "")
        LSIML_RV_df.to_csv("output/LSIML_RV_" + stock_name, index=False)
