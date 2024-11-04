import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import sys
import uuid  # ユニークID生成のため
import traceback
import json
from uuid import UUID
import os
import argparse
import math


# 各加工名に応じたフィールドとその計算ロジックの設定
PROCESS_FIELDS = {
    '穴あけ': ['ドリル直径', '深さ'],
    'ザグリ': ['直径', '深さ', '座ぐり', '座ぐり径'],
    'タップ': ['タップ径', '深さ', 'ピッチ'],
    'ポケット加工': ['幅', '高さ', '深さ'],
    'オープンポケット': ['幅', '高さ', '深さ'],
    '2.5軸等高線': ['等高線ピッチ', '高さ']
}

PROCESS_FUNCTION = {
    '穴あけ': 'calculate_drilling',
    'ザグリ': 'calculate_counterbore',
    'タップ': 'calculate_tap',
    'ポケット加工': 'calculate_pocket',
    'オープンポケット': 'calculate_open_pocket',
    '2.5軸等高線': 'calculate_contour_2_5_axis'
}

# 精度のリスト（ラジオボタン用）
PRECISION_OPTIONS = ['0', '0.1', '0.01', '0.0001']

DIFFICULT_OPTION = ['普通', '難しい', '危険']


PAST_FIELDS = {
    '焼き入れ': ['縦', '横', '高さ'],
    'メッキ': ['縦', '横', '高さ'],
}

tap_pitch_table = {
    "M1": 0.25,    "M1.2": 0.25,    "M1.4": 0.3,    "M1.6": 0.35,    "M1.8": 0.35,
    "M2": 0.4,    "M2.2": 0.45,    "M2.5": 0.45,    "M3": 0.5,    "M3.5": 0.6,
    "M4": 0.7,    "M5": 0.8,    "M6": 1.0,    "M8": 1.25,    "M10": 1.5,
    "M12": 1.75,    "M14": 2.0,    "M16": 2.0,    "M18": 2.5,    "M20": 2.5,
    "M22": 2.5,    "M24": 3.0,    "M27": 3.0,    "M30": 3.5,    "M33": 3.5,
    "M36": 4.0,    "M39": 4.0,    "M42": 4.5,    "M45": 4.5,    "M48": 5.0,
    "M52": 5.0,    "M56": 5.5,    "M60": 5.5
}


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process some arguments.")
    parser.add_argument('--chan', type=int, default=0, help='Chan value (0 or 1)')
    return parser.parse_args()

class OutputRedirector:
    def __init__(self, label):
        self.label = label

    def write(self, text):
        # テキストが空でない場合のみラベルを更新
        if text.strip():  # 改行や空白だけの入力を無視
            self.label.config(text=text)

    def flush(self):
        pass  # 必要に応じて実装（今回は空）

class ProcessApp(TkinterDnD.Tk):
    def __init__(self, chan=0):
        super().__init__()
        
        
        self.title("加工コスト計算機")
        self.geometry("500x700")
        
        ###canvas###
      
        # Canvasを作成
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # スクロールバーを作成
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Frameをキャンバス上に配置
        frame = tk.Frame(self.canvas)
        frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # CanvasにFrameを描画
        
        self.canvas.create_window((0, 0), window=frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # ウィンドウ全体でスクロールをバインド
        self.bind("<MouseWheel>", self._on_mousewheel)

        # ウィンドウのリサイズを有効化
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ###first_processing###

        # ラベルとコンボボックスを追加するフレーム
        self.selection_frame = tk.Frame(frame)
        self.selection_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        self.inter_file = {}  # 各プロセスを保存する辞書
        
        # ラベルと最初のコンボボックスを追加
        self.label = tk.Label(self.selection_frame, text="加工名を選択してください:")
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        ###second_processing###

        # ラベルと最初のコンボボックスを追加
        self.past_frame = tk.Frame(frame)
        self.past_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.label2 = tk.Label(self.past_frame, text="後加工名を選択してください:")
        self.label2.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        ###accessories###
            ##load_file##

        self.load_frame = tk.Frame(frame)
        self.load_frame.grid(row=2, column=0, padx=10, pady=10, sticky='w')

        ttk.Label(self.load_frame, text="ファイルを入力").pack(side=tk.TOP, anchor='nw', padx=10, pady=10)
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(self.load_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, padx=5)

        self.file_entry.drop_target_register(DND_FILES)
        self.file_entry.dnd_bind('<<Drop>>', self.on_drop)

        self.load_button = tk.Button(self.load_frame, text="復元", command=self.load_data)
        self.load_button.pack(side=tk.LEFT, padx=5)
        print('chan', chan)

        if chan == 1:
            self.file_path_var.set('orc_data.json')  # ファイルパスをセット
            self.load_button.invoke()  # ボタンを自動的にクリック        

            ##save_file##

        self.save_frame = tk.Frame(frame)
        self.save_frame.grid(row=3, column=0, padx=10, pady=10, sticky='w')

        ttk.Label(self.save_frame, text="セーブするファイル名を入力").pack(side=tk.TOP, padx=5)
        self.filename = tk.StringVar()
        self.file_entry = tk.Entry(self.save_frame, textvariable=self.filename)
        self.file_entry.pack(side=tk.LEFT, padx=5)

            ##buttons##

        # ボタンを追加するフレーム
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        # ボタンの追加
        self.add_button = tk.Button(self.button_frame, text="加工名を追加", command=lambda i=0: self.on_button_click(i))
        self.add_button.pack(side=tk.LEFT, padx=5)


        self.past_button = tk.Button(self.button_frame, text="後加工を追加", command=lambda i=1: self.on_button_click(i))
        self.past_button.pack(side=tk.LEFT, padx=5)

        # 計算ボタン
        self.calculate_button = tk.Button(self.button_frame, text="計算", command=self.calculate)
        self.calculate_button.pack(side=tk.LEFT, padx=5)

        # **終了ボタンの追加**
        self.exit_button = tk.Button(self.button_frame, text="終了", command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=5)



        ##show_result##

        """
        self.result_label = tk.Label(self,text="")
        self.result_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')

        self.output_redirector = OutputRedirector(self.result_label)
        sys.stdout = self.output_redirector

        """


        # 見積もり結果の表示
        self.all_label = tk.Label(self, text="全ての合計:") #frameの部分をselfにすることによって外側に配置することができる
        self.all_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')

        self.all_value = tk.Label(self, text="")
        self.all_value.grid(row=2, column=1, padx=10, pady=10, sticky='w')



    def _on_mousewheel(self, event):
        """マウスホイールによるスクロール処理"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def exit_app(self):
        self.quit()  # イベントループを終了
        self.destroy()  # ウィンドウを破棄

    def on_drop(self, event):
        # ドロップされたファイルパスを取得
        file_path = event.data.strip("}")
        # ファイルパスをエントリにセット
        file_name = os.path.basename(file_path)
        self.file_path_var.set(file_name)

        self.load_data()

    def on_button_click(self, button_id):
        unit_id = None
        self.create_selection_widgets(button_id, unit_id)




    def create_selection_widgets(self, button_id, unit_id):
        # 新しいユニークIDを作成
        #もしUUIDがある場合はprocess_idに代入する
        if unit_id != None:
            process_id = unit_id
        else:     
            process_id = uuid.uuid4()  # ユニークなIDを生成
        
        
        row = len(self.inter_file) * 8


        if button_id == 0:


            process_var = tk.StringVar()
            combobox = ttk.Combobox(self.selection_frame, textvariable=process_var)
            combobox['values'] = list(PROCESS_FIELDS.keys())
            combobox.grid(row=row, column=1, padx=10, pady=10, sticky='ew')
            combobox.bind("<<ComboboxSelected>>", lambda event, idx=len(self.inter_file): self.update_fields(process_id, button_id))

            fields_frame = tk.Frame(self.selection_frame)
            fields_frame.grid(row=row+1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

                # 数量のラベルと入力フィールドの追加

            quantity_label = tk.Label(self.selection_frame, text="数量:")
            quantity_label.grid(row=row+3, column=0, padx=5, pady=5, sticky='w')

            quantity_var = tk.StringVar()  # 数量のためのStringVar
            quantity_entry = tk.Entry(self.selection_frame, textvariable=quantity_var)
            quantity_entry.grid(row=row+3, column=1, padx=5, pady=5, sticky='w')
            
            #ラジオボタン
            precision_var = tk.StringVar(value=PRECISION_OPTIONS[0])
            precision_frame = tk.Frame(self.selection_frame)
            precision_frame.grid(row=row+4, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
            for option in PRECISION_OPTIONS:
                radio_button = tk.Radiobutton(precision_frame, text=option, variable=precision_var, value=option)
                radio_button.pack(side=tk.LEFT, padx=5, pady=5)

            #難易度の設定
            difficult_var = tk.StringVar(value=DIFFICULT_OPTION[0])
            difficult_frame = tk.Frame(self.selection_frame)
            difficult_frame.grid(row=row+5, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
            for option in DIFFICULT_OPTION:
                radio_button = tk.Radiobutton(difficult_frame, text=option, variable=difficult_var, value=option)
                radio_button.pack(side=tk.LEFT, padx=5, pady=5)

            
            # 削除ボタンの作成
            delete_button = tk.Button(self.selection_frame, text="削除", command=lambda: self.delete_process(process_id))
            delete_button.grid(row=row+6, column=1, padx=5, pady=5)

            result_label = tk.Label(self.selection_frame, text="合計:")
            result_label.grid(row=row+7, column=0, padx=10, pady=10, sticky='w')

            result_value = tk.Label(self.selection_frame, text="")
            result_value.grid(row=row+7, column=1, padx=10, pady=10, sticky='w')

                    # プロセス項目を辞書に保存
            self.process_item = {
                'combobox': combobox,
                'process_var': process_var,
                'fields_frame': fields_frame,
                'quantity_label': quantity_label,
                'quantity_var ': quantity_var,
                'quantity_entry' : quantity_entry,
                'precision_frame': precision_frame,  # ラジオボタンを含むフレーム
                'difficult_frame': difficult_frame, 
                'result_label': result_label,  # "合計:" のラベル
                'precision_var': precision_var,
                'difficult_var': difficult_var,
                'result_value': result_value,
                'delete_button': delete_button,
                'button_id' : button_id
            }

            # ユニークなIDでプロセスを保存
            
            self.inter_file[process_id] = self.process_item
            self.inter_file[process_id]['quantity_var'] = quantity_var






        
        elif button_id == 1:

            
            process_var = tk.StringVar()
            combobox = ttk.Combobox(self.past_frame, textvariable=process_var)
            combobox['values'] = list(PAST_FIELDS.keys())
            combobox.grid(row=row, column=1, padx=10, pady=10, sticky='ew')
            combobox.bind("<<ComboboxSelected>>", lambda event, idx=len(self.inter_file): self.update_fields(process_id, button_id))

            fields_frame = tk.Frame(self.past_frame)
            fields_frame.grid(row=row+1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')


            

            # 削除ボタンの作成
            delete_button = tk.Button(self.past_frame, text="削除", command=lambda: self.delete_process(process_id))
            delete_button.grid(row=row+3, column=1, padx=5, pady=5)

            result_label = tk.Label(self.past_frame, text="合計:")
            result_label.grid(row=row+4, column=0, padx=10, pady=10, sticky='w')

            result_value = tk.Label(self.past_frame, text="")
            result_value.grid(row=row+4, column=1, padx=10, pady=10, sticky='w')

            # プロセス項目を辞書に保存
            process_item = {
                'combobox': combobox,
                'process_var': process_var,
                'fields_frame': fields_frame,


                'result_label': result_label,  # "合計:" のラベル

                'result_value': result_value,
                'delete_button': delete_button,
                'button_id' : button_id
            }

            # ユニークなIDでプロセスを保存
            self.inter_file[process_id] = process_item
            





            




    def delete_process(self, process_id):
        # 削除する前に、指定されたIDが辞書内に存在するか確認する
        


        if process_id in self.inter_file:
            process_item = self.inter_file.pop(process_id)
            button_id = process_item['button_id']



            # 各要素を削除
            process_item['combobox'].destroy()
            process_item['fields_frame'].destroy()

            process_item['result_label'].destroy()  # "合計:" のラベルを削除
            process_item['result_value'].destroy()
            process_item['delete_button'].destroy()

            if button_id == 0 : 
                process_item['precision_frame'].destroy()  # ラジオボタンを含むフレームを削除
                process_item['difficult_frame'].destroy()
                process_item['quantity_label'].destroy()
                process_item['quantity_entry'].destroy()

            print(f"Process with ID {process_id} deleted successfully.")
            
        else:
            print(f"Error: Process with ID {process_id} not found.")
        sys.stdout.flush()



    def update_fields(self, index, button_id):
        # 該当するフィールド用フレームの内容をクリア
        frame = self.inter_file[index]['fields_frame']
        for widget in frame.winfo_children():
            widget.destroy()



        if button_id == 0:

            # 選択された加工名に応じてフィールドを生成
            process_name = self.inter_file[index]['process_var'].get()
            fields = PROCESS_FIELDS.get(process_name, [])

        if button_id == 1:

            # 選択された加工名に応じてフィールドを生成
            process_name = self.inter_file[index]['process_var'].get()
            fields = PAST_FIELDS.get(process_name, [])



        # フィールドのラベルとエントリーを生成
        for i, field in enumerate(fields):
            label = tk.Label(frame, text=field)
            label.grid(row=i, column=0, padx=5, pady=5, sticky='w')

            entry = tk.Entry(frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            frame.columnconfigure(1, weight=1)
            


    def calculate(self):
        total_sum = 0
        for process_id, process_item in self.inter_file.items():
                process_name = process_item['process_var'].get()
                
                frame = process_item['fields_frame']
                field_values = [float(entry.get()) for entry in frame.winfo_children() if isinstance(entry, tk.Entry)]
                button_id = process_item['button_id']

                function_name = PROCESS_FUNCTION.get(process_name)
                
                if button_id == 0:
                    quantity = int(process_item['quantity_var'].get())
                    precision = float(process_item['precision_var'].get())
                    diffi_judg = process_item['difficult_var'].get()
                    print(diffi_judg)
                    difficult = 0
                    if diffi_judg == '普通' : 
                        difficult = 1
                    elif diffi_judg == '難しい':
                        difficult = 1.3
                    elif diffi_judg == '危険':
                         difficult = 1.5
                     

                    if function_name:
                        # 該当する関数を取得し、引数を渡して実行
                        func = getattr(self, function_name)

                        if precision == 0:
                            result = func(*field_values, 1, difficult, quantity)
                        else:
                            result = func(*field_values, precision, difficult, quantity)
                        
                    else:
                        raise ValueError(f"不明なプロセス名: {process_name}")

                    # 他の加工の計算も追加

                    process_item['result_value'].config(text=f"{result:.2f}")
                    total_sum += result

                # 全体の合計を表示
                    self.all_value.config(text=f"{total_sum:.2f}")

                    process_item['input_values'] = field_values
                    process_item['result_var'] = result

                elif button_id == 1:


      
                    if process_name == '焼き入れ':
                        resulty = self.calculate_burning(*field_values)
                    elif process_name == 'メッキ':
                        resulty = self.calculate_plating(*field_values)

                    process_item['result_value'].config(text=f"{resulty:.2f}")   

                    total_sum += resulty 
                                # 全体の合計を表示
                    self.all_value.config(text=f"{total_sum:.2f}")   

                    process_item['input_values'] = field_values
                    process_item['result_var'] = resulty    

                    
        file_list = list(self.inter_file.keys())
        



        
        sys.stdout.flush()
        self.save_data()

        return total_sum

    # 各加工の計算ロジックを定義
    def calculate_drilling(self, diameter, depth, precision, difficult, quantity):
        # 穴あけの計算ロジック（仮）
        return (abs(5 - diameter) + 1) * depth * 30 * difficult * math.log10(10 / precision) * quantity

    def calculate_counterbore(self, top_diameter, top_depth, bottom_diameter, bottom_depth, precision, difficult, quantity):
        # ザグリの計算ロジック（仮）
        top_pull = (abs(5 - top_diameter) + 1) * top_depth
        bottom_pull = (abs(5 - bottom_diameter) + 1) * bottom_depth
        return (top_pull +  bottom_pull) * 45 * difficult * math.log10(10 / precision)  * quantity

    def calculate_tap(self, diameter, depth, pitch, precision, difficult, quantity):
        # タップ加工の計算ロジック（仮）
        return (abs(5 - diameter) + 1) * depth * pitch * 40 * difficult * math.log10(10 / precision)  * quantity

    def calculate_pocket(self, width, height, depth, precision, difficult, quantity):
        # ポケット加工の計算ロジック（仮）
        return width * height * depth * 60 * difficult * math.log10(10 / precision)  * quantity

    def calculate_open_pocket(self, width, height, depth, precision, difficult, quantity):
        # オープンポケット加工の計算ロジック（仮）
        return width * height * depth * 50 * difficult * math.log10(10 / precision)  * quantity

    def calculate_contour_2_5_axis(self, pitch, height, precision, difficult, quantity):
        # 2.5軸等高線加工の計算ロジック（仮）
        return pitch * height * 80 * difficult * math.log10(10 / precision)  * quantity

    ###各後加工の計算ロジックを定義
    def calculate_burning(self, Length, width, height):
        return Length * width * height # * cost_value
    
    def calculate_plating(self, Length, width, height):
        return Length * width * height # * cost_value

    # 他の加工の計算ロジックも追加可能


    def save_data(self):
        saveable_data = {}

        #self.inter_fileをUUIDの前で区切る、リストに追加、リスト[i]を参照、保存


        if not self.filename:
            print("ファイル名を入力してください")
            self.canvas.yview_moveto(1)

        file_unit_list = list(self.inter_file.items())  # リスト化
       

        file_dict = dict(file_unit_list)  # 辞書に変換
    

        filename_str = self.filename.get()
        if not filename_str.endswith('.json'):
            filename_str += '.json'

        # 保存先のフォルダを指定
        # r をつけることで、その特殊な意味を無効にし、文字列をそのまま扱うことができます。
        folder_path = r'C:\Estimate Generator\data'

        # フォルダとファイル名を結合して完全なパスを作成
        full_path = os.path.join(folder_path, filename_str)


            

        for process_id, process_item in self.inter_file.items():
                difficult_word = process_item['difficult_var'].get()
                print(difficult_word)
                if difficult_word == '普通':
                    difficult_value = '0'
                elif difficult_word == '難しい':
                    difficult_value = '1'
                elif difficult_word == '危険':
                    difficult_value = '2'
                else:
                    difficult_value = None
                # 保存可能な情報だけを抽出
                saveable_data[str(process_id)] = {
                    'process_var': process_item['process_var'].get(),
                    'precision_var': process_item['precision_var'].get() if process_item.get('precision_var') else None,
                    'difficult_var': difficult_value,
                    'quantity_var': process_item['quantity_var'].get(),
                    'button_id': process_item['button_id'],
                    'input_values' : process_item['input_values'],
                    'result_var' : process_item['result_var']
                    }


        # JSONファイルに保存
        with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(saveable_data, f, ensure_ascii=False, indent=4)




    def load_data(self):
        file_path = self.file_path_var.get()  # StringVarから実際の文字列を取得

        default_path = os.path.join("data", file_path)

        if not file_path:
            print("ファイルパスが指定されていません。")
            return

        try:
            with open(default_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            self.restore_data_to_widgets(data)
        except FileNotFoundError:
            print(f"ファイル {default_path} が見つかりませんでした。")
        except json.JSONDecodeError:
            print(f"ファイル {default_path} のフォーマットが正しくありません。")
        except Exception as e:
            print(f"データの読み込み中にエラーが発生しました: {e}")
            traceback.print_exc()

    def restore_data_to_widgets(self, data):

        #create_selection_widgetsにUUIDを送る

        # データの復元
        for process_id, process_data in data.items():
            print('load_data', data)
            # ボタンIDに基づいて適切なウィジェットを作成
            button_id = process_data['button_id']
            unit_id = UUID(process_id)
            self.create_selection_widgets(button_id, unit_id)  # 適切なコンボボックスやフィールドを生成
            
            
            # 復元されたIDをUUIDに変換
            process_uuid = UUID(process_id)

            # ウィジェットを更新
            self.inter_file[process_uuid]['process_var'].set(process_data['process_var'])
            
            
            # 精度のラジオボタン（button_idが0の場合のみ）
            if button_id == 0 and 'precision_var' in process_data:
                self.inter_file[process_uuid]['precision_var'].set(process_data['precision_var'])
                
                quantity_value = self.inter_file[process_uuid]['quantity_var'].get()
                print('quantity_value', quantity_value)
                if not quantity_value:
                    self.inter_file[process_uuid]['quantity_var'].set('1')
                else:
                    self.inter_file[process_uuid]['quantity_var'].set(quantity_value)

                difficult_value = process_data['difficult_var']
                print(difficult_value)
                
                if difficult_value:
                    d_int = int(difficult_value)
                    difficult_word = DIFFICULT_OPTION[d_int]
                    self.inter_file[process_uuid]['difficult_var'].set(difficult_word)
                else:
                    print(f"Invalid difficult_value: {difficult_value}")
            
            if process_data['process_var'] == 'タップ':
                first_value = process_data['input_values'][0]
                first_value_str = f"M{int(first_value)}"  # 例：8なら"M8"とする
                pitch_value = tap_pitch_table.get(first_value_str, "N/A")
                process_data['input_values'].append(pitch_value)   # 3番目の値としてピッチをセット
                print(f"Updated pitch for {process_uuid}: {pitch_value}")

            # フィールドの値も復元
            self.update_fields(process_uuid, button_id)
            for i, value in enumerate(process_data['input_values']):
                position = i * 2 + 1
                entry_widget = self.inter_file[process_uuid]['fields_frame'].winfo_children()[position]                
                
                if isinstance(entry_widget, tk.Entry):
                    entry_widget.insert(0, str(value))


                    
                    

            # 計算結果も表示
        if self.inter_file[process_uuid]['result_value']:
            self.inter_file[process_uuid]['result_value'].config(text=f"{process_data['result_var']:.2f}")
        else:
            self.inter_file[process_uuid]['result_value'] = '0'

        print("データが復元されました。")



if __name__ == "__main__":
    args = parse_arguments()

    app = ProcessApp(chan=args.chan)
    app.mainloop()
