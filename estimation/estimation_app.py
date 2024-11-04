import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time  # 待機用のtimeモジュールを追加
import re
import subprocess
import os





class EstimationApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__() 
        self.title("製造見積もりソフトウェア")
        self.create_widgets()


    def create_widgets(self):
        frame = ttk.Frame(padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.material_types = {
            '鉄': (7.85, 'https://www.e-metals.net/product/200546/'),
            'アルミ': (2.70, 'https://www.e-metals.net/product/202386/'),
            'ステンレス': (8.00, 'https://www.e-metals.net/product/202656/')
        }

        widgets = [
            ("材料タイプ", tk.StringVar()),
            ("幅（mm）", tk.DoubleVar()),
            ("高さ（mm）", tk.DoubleVar()),
            ("奥行き（mm）", tk.DoubleVar()),
            ("材料費（円/mm³）", tk.DoubleVar()),
            ("加工コスト", tk.DoubleVar()),
            ("間接費", tk.DoubleVar()),
            ("セットアップ時間（時間）", tk.DoubleVar()),
            ("加工時間（時間）", tk.DoubleVar()),
            ("検査時間（時間）", tk.DoubleVar()),
            ("個数", tk.DoubleVar())
        ]

        row = 0
        col = 0

        for idx, (label_text, *variables) in enumerate(widgets):

            ttk.Label(frame, text=label_text).grid(row=row, column=col, sticky=tk.W)
            col += 1
            for var in variables:
                if isinstance(var, tk.StringVar):
                    ttk.Entry(frame, textvariable=var).grid(row=row, column=col)
                else:
                    ttk.Entry(frame, textvariable=var).grid(row=row, column=col)
                col += 1
            col = 0
            row += 1

        self.material_type_var = widgets[0][1]
        self.width_var = widgets[1][1]
        self.height_var = widgets[2][1]
        self.depth_var = widgets[3][1]
        self.material_cost_var = widgets[4][1]
        self.labor_cost_var = widgets[5][1]
        self.overhead_cost_var = widgets[6][1]
        self.setup_time_var = widgets[7][1]
        self.machining_time_var = widgets[8][1]
        self.inspection_time_var = widgets[9][1]
        self.product_amount_var = widgets[10][1]

        ttk.Combobox(frame, textvariable=self.material_type_var, values=list(self.material_types.keys())).grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E))
        # 材料費取得ボタン
        ttk.Button(frame, text="材料費取得", command=self.scrape_material_cost).grid(row=row, column=0, columnspan=1)
        ttk.Button(frame, text="画像読み込み", command=self.ocr_json_data).grid(row=row+1, column=0, columnspan=1)

        self.img_path_var = tk.StringVar()
        self.img_entry = tk.Entry(frame, textvariable=self.img_path_var)
        self.img_entry.grid(row=row+1, column=1, columnspan=1)
    

       

        ttk.Button(frame, text="加工コストの計算", command=self.scrape_labor_cost_chan).grid(row=row+2, column=0, columnspan=1)
        ttk.Button(frame, text="見積もり計算", command=self.calculate_estimate).grid(row=row+3, column=0, columnspan=1)

        
        self.result_label = ttk.Label(frame, text="")
        self.result_label.grid(row=row+5, column=0, columnspan=2)



    def on_drop(self, event):
        # ドロップされたファイルパスを取得
        img_path = event.data.strip("}")
        # ファイルパスをエントリにセット
        img_name = os.path.basename(img_path)
        self.img_path_var.set(img_name)


    def ocr_json_data(self):
        process = subprocess.Popen(['python', 'compleat_OCR.py', '--img_url', f'{self.img_path_var}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            try:
            # 標準出力から計算結果を読み取る
                self.scrape_labor_cost(1)
            # labor_cost_var に設定する
            except ValueError:
                self.result_label.config(text="計算結果の取得に失敗しました。")
        else:
            self.result_label.config(text=f"エラーが発生しました: {stderr.decode().strip()}")        
        print()

    def scrape_labor_cost_chan(self):
        self.scrape_labor_cost(0)

    def scrape_labor_cost(self, chan):
        print('chan', chan)
        if chan == 0:
            process = subprocess.Popen(['python', 'task_app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif chan == 1:
            print('chan', chan)
            process = subprocess.Popen(['python', 'task_app.py', '--chan', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            try:
            # 標準出力から計算結果を読み取る
                 total_sum = float(stdout.decode().strip())
            # labor_cost_var に設定する
                 self.labor_cost_var.set(total_sum)
            except ValueError:
                 self.result_label.config(text="計算結果の取得に失敗しました。")
        else:
            self.result_label.config(text=f"エラーが発生しました: {stderr.decode().strip()}")



    def scrape_material_cost(self):
        material_type = self.material_type_var.get()

        if material_type not in self.material_types:
            self.result_label.config(text="材料タイプを選択してください。")
            return

        # 選択された材料タイプに対応するURLを取得
        url = self.material_types[material_type][1]
        
        chrome_options = Options()
        #chrome_options.add_argument("--headless")  # ヘッドレスモードで実行

        # ChromeDriverのパスを指定
        service = Service(executable_path='C:/Estimate Generator/chromedriver-win64/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        try:
            # 入力フィールドに値を入力
            width = self.width_var.get()
            height = self.height_var.get()
            depth = self.depth_var.get()

            # 指定されたIDに入力
            driver.find_element(By.ID, "dim_input_200546_W").send_keys(str(width))
            driver.find_element(By.ID, "dim_input_200546_H").send_keys(str(height))
            driver.find_element(By.ID, "dim_input_200546_L").send_keys(str(depth))
            driver.find_element(By.ID, "amount_input_200546").clear()  # 数量のフィールドをクリア
            driver.find_element(By.ID, "amount_input_200546").send_keys("1")  # 数量を1に設定

            # 5秒待機して計算結果を待つ
            time.sleep(5)

        # 材料費を取得
            price_element = driver.find_element(By.CLASS_NAME, "price-num")
            price_text = price_element.text

        # 正規表現で数値部分だけを抽出する
            price_match = re.search(r'\d+\.?\d*', price_text)
            if price_match:
                price = float(price_match.group())
                self.material_cost_var.set(price)
            else:
                self.result_label.config(text="価格情報が見つかりませんでした。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
        
        finally:
            driver.quit()

    def calculate_estimate(self):
        material_type = self.material_type_var.get()
        width = self.width_var.get()
        height = self.height_var.get()
        depth = self.depth_var.get()
        material_cost = self.material_cost_var.get()
        labor_cost = self.scrape_labor_cost.get()
        overhead_cost = self.overhead_cost_var.get()
        setup_time = self.setup_time_var.get()
        machining_time = self.machining_time_var.get()
        inspection_time = self.inspection_time_var.get()
        amount = self.product_amount_var.get()

        if material_type not in self.material_types:
            self.result_label.config(text="材料タイプを選択してください。")
            return

        density = self.material_types[material_type][0]
        volume = width * height * depth
        weight = volume * density

        total_material_cost = material_cost * volume
        total_labor_cost = labor_cost + overhead_cost
        total_time = setup_time + machining_time + inspection_time

        total_cost = (total_material_cost + total_labor_cost) * amount

        result_text = (f"総見積もり費用：{total_cost:.2f}円\n"
                       f"作成に要する時間：{total_time:.2f}\n"
                       f"材料体積：{volume:.2f} mm³\n"
                       f"材料重量：{weight:.2f} g")

        self.result_label.config(text=result_text)

if __name__ == "__main__":

    app = EstimationApp()
    app.mainloop()
