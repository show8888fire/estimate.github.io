import cv2
import numpy as np
import pytesseract
import subprocess
import copy
import pyocr
from PIL import Image, ImageEnhance
import os
import cv2
import re
import json
import uuid 
import os
from estimation_app import EstimationApp
import tkinter as tk

circled_numbers = {
    '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
    '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⓪': '0'
}

hiragana_to_katakana = {
    'あ': 'ア', 'い': 'イ', 'う': 'ウ', 'え': 'エ', 'お': 'オ',
    'か': 'カ', 'き': 'キ', 'く': 'ク', 'け': 'ケ', 'こ': 'コ',
    'さ': 'サ', 'し': 'シ', 'す': 'ス', 'せ': 'セ', 'そ': 'ソ',
    'た': 'タ', 'ち': 'チ', 'つ': 'ツ', 'て': 'テ', 'と': 'ト',
    'な': 'ナ', 'に': 'ニ', 'ぬ': 'ヌ', 'ね': 'ネ', 'の': 'ノ',
    'は': 'ハ', 'ひ': 'ヒ', 'ふ': 'フ', 'へ': 'ヘ', 'ほ': 'ホ',
    'ま': 'マ', 'み': 'ミ', 'む': 'ム', 'め': 'メ', 'も': 'モ',
    'や': 'ヤ', 'ゆ': 'ユ', 'よ': 'ヨ',
    'ら': 'ラ', 'り': 'リ', 'る': 'ル', 'れ': 'レ', 'ろ': 'ロ',
    'わ': 'ワ', 'を': 'ヲ', 'ん': 'ン',
    'が': 'ガ', 'ぎ': 'ギ', 'ぐ': 'グ', 'げ': 'ゲ', 'ご': 'ゴ',
    'ざ': 'ザ', 'じ': 'ジ', 'ず': 'ズ', 'ぜ': 'ゼ', 'ぞ': 'ゾ',
    'だ': 'ダ', 'ぢ': 'ヂ', 'づ': 'ヅ', 'で': 'デ', 'ど': 'ド',
    'ば': 'バ', 'び': 'ビ', 'ぶ': 'ブ', 'べ': 'ベ', 'ぼ': 'ボ',
    'ぱ': 'パ', 'ぴ': 'ピ', 'ぷ': 'プ', 'ぺ': 'ペ', 'ぽ': 'ポ'
}

similar_chars_dict = {
    '0': ['O', 'o', 'Q', 'ロ', '〇'],
    '1': ['I', 'l', '|', 'い', 'し', '｜'],
    '2': ['Z', '乙', 'ニ'],
    '3': ['E', 'ミ'],
    '4': ['A', 'ハ', 'よ'],
    '5': ['S', 'さ'],
    '6': ['G', 'む'],
    '7': ['T', 'ナ'],
    '8': ['B', 'は', 'バ'],
    '9': ['g', 'q', 'ク'],
}

word_list = ['キリ','M','φ','リーマ','座ぐり','深さ', '通し']

class search_word():
    def __init__(self, img_url):
        # 丸囲み数字を通常の数字に変換するマッピング


        # Path設定
        TESSERACT_PATH = 'C:/Program Files/Tesseract-OCR/'  # インストールしたTesseract-OCRのpath
        TESSDATA_PATH = 'C:/Program Files/Tesseract-OCR/tessdata'  # tessdataのpath

        os.environ["PATH"] += os.pathsep + TESSERACT_PATH
        os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH

        # OCRエンジン取得
        tools = pyocr.get_available_tools()
        tool = tools[0]

        # OCRの設定 ※tesseract_layout=6が精度には重要。デフォルトは3
        builder = pyocr.builders.TextBuilder(tesseract_layout=11)

        # 解析画像読み込み
        img = Image.open(img_url)  # 他の拡張子でもOK

        # 適当に画像処理（グレースケール変換、コントラスト調整、しきい値処理を追加）
        img_g = img.convert('L')  # グレースケール変換

        # OpenCVを使用した閾値処理
        img_np = np.array(img_g)  # PIL画像をNumPy配列に変換

        _, img_thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY)  # 閾値150でしきい値処理


        # Pillow形式に戻す
        img_thresh_pil = Image.fromarray(img_thresh)

        # コントラストを上げる
        enhancer = ImageEnhance.Contrast(img_thresh_pil)  # コントラストを上げる
        img_con = enhancer.enhance(2.0)  # コントラストを上げる

        # 画像からOCRで日本語を読んで、文字列として取り出す
        txt_speocr = tool.image_to_string(img_con, lang='eng+jpn', builder=builder)
        txt_faiocr = tool.image_to_string(img_con, lang='grc', builder=builder)
        txt_pyocr = txt_faiocr + '\n' + txt_speocr

        # OCRの出力テキストを変換
        for circled_num, normal_num in circled_numbers.items():
            txt_pyocr = txt_pyocr.replace(circled_num, normal_num)

        ##いらない文字を削除し文字の成形する##
        txt_pyocr = txt_pyocr.replace(' ', '')
        txt_pyocr = txt_pyocr.split()
        txt_ident = []
        new_pyocr = ""

        identify_list = ["φ", "x", "M"]

        for word in txt_pyocr:
            if any(key in word for key in identify_list):
                keyword_list = list(word)
                txt_ident.append(keyword_list)



        for num, word in similar_chars_dict.items():
            for t_l in txt_ident:
                for i, txt in enumerate(t_l):
                    if txt in word:
                        t_l.remove(txt)
                        t_l.insert(i, num)


        new_pyocr = [''.join(sub) for sub in txt_ident]



        delete_words = ["φ", "x"]
        for py in new_pyocr:

            for word in delete_words:
                disc_word = py.replace(f"{word}", "")
            #ここでprint(disc_word)を使うと結果が6x15キりと615キりになる
        #ここでprint(disc_word)を使うと結果が615キりのみになる

        self.no_jap_list = []

        self.next_py = []
        if not disc_word.isdigit():
            # OCRの出力テキストをカタカナに変換
            for py in new_pyocr:
                print('py', py)
                for hiragana, katakana in hiragana_to_katakana.items():
                    py = py.replace(hiragana, katakana)

                self.next_py.append(py)
                no_jap = re.sub(r'[ァ-ン]', '', py)

                print('no_jap', no_jap)

                self.no_jap_list.append(no_jap)

        #個々にリストに追加
        self.filtering_text()
        
    def filtering_text(self):
        filtered_text = []
        print('self.next_py', self.next_py)

        for word in self.next_py:
            if any(w in word for w in word_list):
                filtered_text.append(word)

        print(filtered_text)


        print(self.no_jap_list)

        word_dict = {}

        for idx, f_t in enumerate(filtered_text):
            word_dict[f_t] = self.no_jap_list[idx]

        print('serch_word_dict', word_dict)
        return word_dict


class contackt_circle():
    use_word = []
    def __init__(self, img_url, search):
        
        self.circles_list = []
        self.use_word = []
        self.under_list = []
        self.process_word = {}
        self.word_dict = search.filtering_text()
        print('word_dict', self.word_dict)


        # 画像を読み込む
        self.oli_img = cv2.imread(img_url, 0)
        img = cv2.imread(img_url, 0)
        img = cv2.medianBlur(img,1)
        gray = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
        self.up_count = 0
        self.thur = 0

        self.img_processing(img, gray)
        
    ###ここから画像処理###
        
    def img_processing(self, img, gray) :
        py_img = img

        circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, dp=1, minDist=50, param1=100, param2=30, minRadius=10, maxRadius=50)
        
        # エッジの検出（Cannyを使用）
        edges = cv2.Canny(img, 50, 150, apertureSize=3)
        
        # 直線の検出（HoughLinesPを使用）
        self.lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=60, minLineLength=50, maxLineGap=10)
        
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
                        # 円を描画
                cv2.circle(gray, (i[0], i[1]), i[2], (0, 255, 0), 2)  # 外側の円
                cv2.circle(gray, (i[0], i[1]), 2, (0, 0, 255), 3)        # 円の中心
        
        # 検出された直線を描画
        for line in self.lines:

                x1, y1, x2, y2 = line[0]
                cv2.line(gray, (x1, y1), (x2, y2), (255, 0, 0), 2)
        self.thur = 1
        self.main_process(circles, py_img, gray)
    
    def up_scale_img(self, scale_factor):
            print('scale', scale_factor)
            self.process_word = {}
            print('sk', scale_factor)
            print('count', self.up_count)
            width = int(self.oli_img.shape[1] * scale_factor)
            height = int(self.oli_img.shape[0] * scale_factor)
            dim = (width, height)
            img = cv2.resize(self.oli_img, dim, interpolation=cv2.INTER_LINEAR)
            
            
            # メディアンフィルタを適用
            img = cv2.medianBlur(img, 1)
            
            # 二値化処理
            _, gray = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY)
            
            # モルフォロジー変換（クロージング処理）
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # 適応的しきい値処理
            gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 11, 2)
            


            gray = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            self.img_processing(img, gray) 

        
    ###ここからメインプログラム###
    def main_process(self, circles, py_img, gray):
        #word_dict.keys() process_word.keys()の文字数が同じなら終了、count=2になったら文字数が同じじゃなくともprocess_wordを
        # 各単語とその座標を出力
        while self.up_count < 3:
            print('count', self.up_count)
            print('pass', self.thur)
            print('dict', self.process_word)
            if self.thur == 1:
                pass
            elif len(self.word_dict.keys()) != len(self.process_word.keys()) and self.up_count != 0:
                scale_factor = self.up_count * 0.5 + 1
                self.up_scale_img(scale_factor)
            elif len(self.word_dict.keys()) == len(self.process_word.keys()):
                  break
            else:
                self.cv2_result
            for i, c in enumerate(circles[0, :]):

                circle_center = (c[0], c[1])
                full_circle = list(j for j in c)
                full_circle = self.convert_to_standard_types(full_circle)
                circle_center = self.convert_to_standard_types(circle_center)
                self.circles_list.append(full_circle)
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)# OCR処理を実行し、文字と位置情報を取得

                deep_copy = copy.deepcopy(self.word_dict)
                none_dict = {}


                for i in range(len(data['text'])):
                        print('word_dict', self.word_dict)
                        process_len = len(list(self.process_word.keys()))
                        check_len = len(list(self.word_dict.keys()))
                        if data['text'][i] and not data['text'][i] == " "  and process_len != check_len:  # テキストが空でない場合
                            text_data = data['text'][i]
                            print(text_data)
                            x, y = data['left'][i], data['top'][i]
                            w, h = data['width'][i], data['height'][i]

                            # 中心座標を計算
                            center_x = x + w / 2
                            center_y = y

                            result, word, txt_x = self.feltering_text(text_data, deep_copy, center_x, none_dict, data['text'])

                            print('fainal check dict', self.process_word)

                            
                            if result == True:
                                    self.use_word.append(text_data)
                                    
                                    print(f"文字: {word} 座標: ({txt_x}, {center_y})")

                                    full_text = word

                                    if full_text not in self.process_word:

                                        self.text_underline(txt_x, center_y, full_text, full_circle, gray)
            self.thur = 0
            self.up_count += 1
            

    def feltering_text(self, text, deep_copy, x, none_dict, data):
        posi_dict = {}
        idx = 1
        for word, enum in deep_copy.items():
            print('word', word, 'dict', deep_copy)
            print('text len', len(text), 'enum len', len(enum))

            #文字数の一致と使用している文字の部分一致
            if len(text) == len(enum):

                if any(t in enum for t in text):
                    print('text', text)
                    del deep_copy[word]
                    print('word', word, 'dict', deep_copy)
                    return True, word, x
                
            
            elif any(w in word and w in text for w in word_list):
                        
                    if word in none_dict:
                        posi_dict[text] = x
                        none_dict[word].append(posi_dict)
                        print('none_dict2', none_dict)

                    else:

                        print('none_word is', text)
                        posi_dict[text] = x
                        
                        print('posi_dict', posi_dict)
                        none_dict[word] = [posi_dict]
                        print('none_dict', none_dict)
            
            elif none_dict:
                    print('none_dict[word] items', none_dict[word])
                    if data.index(text) == data.index(next(iter(none_dict['M8x20'][0].keys()))) + 1:
                        posi_dict[text] = x
                        none_dict[word].append(posi_dict)
                        print('none_dict3', none_dict)



      
        if none_dict:
            word = next(iter(none_dict))
            print('none_check', none_dict[word], len(none_dict[word]))
            if len(none_dict[word]) > 1:
                print('thor')

                for idx in range(idx):
                
                            if self.none_word_check(none_dict[word], idx, enum):
                                    keys = [list(d.keys())[0] for d in none_dict[word]]
                                    values = [list(d.values())[0] for d in none_dict[word]]

                                    join_word = ''.join(keys)
                                    txt_x = sum(values) / len(values)
                                    print('create_word', join_word, txt_x)

                                    del none_dict[word]

                                    return True, join_word, txt_x
            
            
            else:

                    return False, None, x
            
        elif len(deep_copy) == 1:
            word = next(iter(deep_copy.keys())) 
            return True, word, x
            
        else:
                return False, None, x


    def none_word_check(self, none_word, idx, enum):

        count = 0
        n_lword = []
        for i in range(idx):
            n_lword.append(none_word[i])
            
        new_word = ''.join(n_lword)
        if len(new_word) == len(enum):
            self.split_word(enum, idx)
            for j in range(idx):
                if any(w in enum[j] for w in new_word[j]):
                    count += 1
        
        if count == idx:
            return True


    def split_word(self, word, index):
              # word の長さを取得
        length = len(word)
        
        # 何個に分割できるか計算
        num_parts = length // index
        remainder = length % index
        
        # 各部分に何文字ずつ割り当てるか調整
        result = []
        start = 0
        
        for i in range(num_parts):
                # 割り切れない分は前の部分から増やしていく
                extra_char = 1 if remainder > 0 else 0
                result.append(word[start:start + index + extra_char])
                start += index + extra_char
                remainder -= extra_char
        
        # 最後の部分が残っている場合
        if start < length:
                result.append(word[start:])
        
        return result

                    
                      


    def text_underline(self, x, y, full_text, circle, gray):
        
        txt_x = x
        txt_y = y
        
        idx = 0
        onece = 0
        
        for line in self.lines:
                    print('line is', line)

                    if onece == 0:
                        if txt_y + 50 > line[0][1] > txt_y and line[0][1] * 0.8 <  line[0][3] < line[0][1] * 1.2:
                            print('y_under', line)
                            line_y = (line[0][1] + line[0][3]) / 2
                            txt_posi = (txt_x, txt_y, txt_x, line_y)
                            if line[0][0] < txt_x < line[0][2]:

                                print("line01", line[0])
                                true_line = list(int(l) for l in line[0])
                                
                                self.under_list.append(line)
                                self.conect_circle(true_line, full_text, circle, idx, gray)

                                onece += 1
                                
                    elif onece != 0:
                           break

        

    
    def conect_circle(self, txt_line, full_text, circle, idx, gray):

        converted_circle_cross_lines = self.isconect_circle(circle, self.lines, gray)
        
        if txt_line != [0, 0, 0, 0]:

                for c_posi, l_posi_o in converted_circle_cross_lines.items():
                        print(len(l_posi_o))

                        while idx < len(l_posi_o):

                
                            l_posi = tuple(int(i) for i in l_posi_o[idx])
                            print(l_posi, '+', idx)
                            
                            tuple_data = tuple(int(x) for x in txt_line)


                            if self.comparison_line(tuple_data, l_posi, 0):
                                            self.process_word[full_text] = circle
                                            print("tuple", tuple_data)
                                            print("posi", l_posi)
                                            print("process_word",    self.process_word)
                                            idx += len(l_posi_o)


                            elif self.comparison_line(tuple_data, l_posi, 1):
                                            self.process_word[full_text] = circle
                                            print("tuple", tuple_data)
                                            print("posi", l_posi)
                                            print("process_word",    self.process_word)
                                            idx += len(l_posi_o)

                            
                            elif self.comparison_line(tuple_data, l_posi, 2):
                                            self.process_word[full_text] = circle
                                            print("tuple", tuple_data)
                                            print("posi", l_posi)
                                            print("process_word",    self.process_word)
                                            idx += len(l_posi_o)


                            else:
                                            print("one more")
                                            idx += 1
                                            self.extra_conect(tuple_data, full_text, l_posi, circle, idx, gray)

        

    def comparison_line(self, tuple_data, l_posi, pattern):

        l = 0
        r_l = [2, 3, 0, 1]
        c_count = 0
        while l < 4:
            if pattern == 0:
                if tuple_data[l] - 3 < l_posi[l] < tuple_data[l] + 3: #l_posiの始点もしくは終点がtuple_dataの始点または終点の近くにあるかをチェック
                    c_count += 1

                    if c_count == 2:
                        return True
            elif pattern == 1:
                if tuple_data[l] - 3 < l_posi[r_l[l]] < tuple_data[l] + 3: #l_posiの始点と終点を反転させる

                    c_count += 1
                    print("count", c_count)

                    if c_count == 2:
                        return True

            l += 1

        if pattern == 2: #tuple_dataとl_posiが交差しているかをチェック
               A = (tuple_data[0], tuple_data[1])
               B = (tuple_data[2], tuple_data[3])
               C = (l_posi[0], l_posi[1])
               D = (l_posi[2], l_posi[3])
               #直線に対する点の位置を取得
               if self.cross_product(A, B, C) * self.cross_product(A, B, D) < 0:
                   return True
        
               
    def cross_product(self, x, y, z):
        return (y[0] - x[0]) * (z[1] - x[1]) - (y[1] - x[1]) * (z[0] - x[0])
               
                         
        
    def extra_conect(self, tuple_data, full_text, l_posi, circle, idx, gray):
        
        if l_posi[0: 2] in tuple_data or l_posi[-2:] in tuple_data:
            
            print("idx is", idx)
            self.conect_circle(l_posi, full_text, circle, idx, gray)
        else:
            txt_line = [0, 0, 0, 0]
            
            print("idx0002", idx)
            self.conect_circle(txt_line, full_text, circle, idx, gray)
            
            print("Nothing")
            
        




    # 円と直線の接触を確認する関数
    def is_line_touching_circle(self, circle, line):
        x1, y1, x2, y2 = line
        circle_center = np.array([circle[0], circle[1]])
        radius = circle[2]
            
        # 直線の点と円の中心までの距離を計算
        point1 = np.array([x1, y1])
        point2 = np.array([x2, y2])
        
        line_vec = point2 - point1
        line_len = np.linalg.norm(line_vec)#ユークリッド距離の計算三角関数のCのところ
        line_unitvec = line_vec / line_len
            
            
        circle_vec = circle_center - point1
            
            
        proj_length = np.dot(circle_vec, line_unitvec)
        
        proj_point = point1 + proj_length * line_unitvec #point1とpoint2の線分内にあり円の中心から最も近い座標
        
            
        # 円の中心と直線の最短距離を計算
        dist_to_circle = np.linalg.norm(proj_point - circle_center)#ユークリッド距離の計算三角関数のCのところ
            
        # 距離が半径以下なら円に接触していると判断
        return dist_to_circle <= self.radius
            
    
    def isconect_circle(self, circle, lines, gray):
    # 円と直線の接触を確認し、接触している場合は特別な表示
        if circle is not None and lines is not None:
                conect_line=[]
                circle_cross_lines = {}
                


                circle_center = (circle[0], circle[1])  # 円の中心座標 (x, y)
                        
                self.radius = circle[2]  # 円の半径

                for line in lines:  # 各直線について処理
                                
                                if self.is_line_touching_circle(circle, line[0]):  # 接触判定
                                        

                                        x1, y1, x2, y2 = line[0]

                                        # 接触している線を赤く表示
                                        cv2.line(gray, (x1, y1), (x2, y2), (0, 0, 255), 3)

                                        if line[0][0] != line[0][2] and line[0][1] != line[0][3]:#中央線を消すため
                                            conect_line.append(line[0])
                

                                        # 辞書に円と接触している線を追加
        if circle_center not in circle_cross_lines:
                                                
                        circle_cross_lines[circle_center] = conect_line


                        

                        converted_circle_cross_lines = self.convert_to_standard_types(circle_cross_lines)
                        print('total lines', converted_circle_cross_lines)
                        return converted_circle_cross_lines
            
    #print(lines)

    def convert_to_standard_types(self, data):
    
        if isinstance(data, dict):  # 辞書の場合、キーと値を再帰的に処理
                return {self.convert_to_standard_types(k): self.convert_to_standard_types(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):  # リストやタプルの場合、各要素を再帰的に処理

                return type(data)(self.convert_to_standard_types(x) for x in data)
        elif isinstance(data, (np.ndarray)):  # リストやタプルの場合、各要素を再帰的に処理

                return [self.convert_to_standard_types(x) for x in data.tolist()]

        elif isinstance(data, (np.integer)):  # NumPyの数値型はintに変換
                
                return int(data)

        else:
                return data  # その他の型はそのまま返す


            
    # 結果を表示
    def cv2_result(self):        
        cv2.imshow('Detected Circles and Lines', self.gray)
        cv2.waitKey(0)
        cv2.destroyAllWindows()



class generate_json_data():
    def __init__(self, contackt):


        # Create an instance and access process_word
        app = contackt

        process_word = app.process_word
        circles_list = app.circles_list

        olrigin_depth = 0

        quantity_list = ['x', '-', ' ']

        para_dict = {
            'hole':['キリ','M','φ','リーマ','座ぐり','P'], #Pは実際の図面にはなくポケット加工に対応するための特別な記号
            'depth':['深さ', '通し']
        }



        save_list = []
        saveable_data = {}

        print(circles_list)

        def circle_num(word):
            pro_list = []
            json_w_dict = {}
            new_word = []
            del_list = []
            
            word = re.findall(r'[A-Za-zぁ-んァ-ン一-龯]+|\d+|\+|\-|\.|\φ', word)  # +や-も見つける
            print('word is ' ,word)
            for i, w in enumerate(word):
                if w.isdigit():
                    new_word.append(int(w))
                elif not w.isdigit():
                    if w == '.':
                        n_w = word[i - 1] + word[i] + word[i + 1]
                        del_list.append(int(i))

                        new_word.append(float(n_w))
                    else:
                        new_word.append(w)
            
            for idx in del_list:
                del new_word[idx+1]
                del new_word[idx-1]


            print(new_word)
            for i, item in enumerate(new_word):
                # 最初に見つかった数字を辞書に入れる
                if isinstance(item, int) and 'first_num' not in json_w_dict:
                    json_w_dict['first_num'] = int(item)

                # 最初に見つかった文字列を辞書に入れる
                elif isinstance(item, str)  and 'first_str' not in json_w_dict:
                    json_w_dict['first_str'] = item

                elif item in pro_list:
                    if isinstance(new_word[i], int) and isinstance(new_word[i + 1], str) and isinstance(new_word[i + 2], int):
                        json_w_dict['second_num'] = int(float(item))

                if i == 0 and isinstance(item, int):
                    print('item', item)
                    if any(q in new_word[i + 1] for q in quantity_list):
                        json_w_dict['quantity_var'] = item


                elif i > 0 and i < len(new_word) - 1 and isinstance(item, int):
                    if any(q in new_word[i - 1] for q in quantity_list) and any(q in new_word[i + 1] for q in quantity_list):
                        print('quantity_list', quantity_list)
                        print('index', i)
                        print('item', item)
                        json_w_dict['quantity_var'] = item

                

                
            reword = list(reversed(new_word))


            for i, reitem in enumerate(reword):
                # + や - の場合、その次の次にある数字を precision_var に入れる
                
                if reitem == '+' or reitem == '-':
                    
                    if isinstance(reword[i - 1], float):
                        print(f'{i} + word + {reitem}')
                        json_w_dict['precision_var'] = reword[i - 1]

            return json_w_dict, new_word





        def process_setting(word, func):

            process_id = uuid.uuid4()
            individual_words, full_words = circle_num(word)
            input_values_dick = {}
            register_data = {}
            
            if func ==  'tap_process':
                process_var = "タップ"

            
            elif func ==  'hole_process':
                process_var = "穴あけ"

            
            elif func == 'hole_process':
                first_num = individual_words['first_num'].get() 
                if first_num > 20:
                    word += 'P'
                    process_setting(word, func)

            
            for n, ind in enumerate(full_words):

                if ind in para_dict['hole']:

                    if ind == 'M':
                        first_para = full_words[n + 1]
                        input_values_dick['first_para'] = first_para
                        if n + 2 < len(full_words) and full_words[n + 2] == 'x':
                            for i in range(len(full_words) - (n + 2)):

                                if isinstance(full_words[n + 2 + i], int):
                                    second_para = full_words[n + 2 + i]
                                    input_values_dick['second_para']  = second_para
                                    print('s_p', second_para)


                        #third_para = full_words[n + 1]
                        #if third_para:
                        #   input_values_dick['third_para'] = third_para
                    elif not ind == 'M':
                        print(ind)
                        first_para = full_words[n - 1]
                        input_values_dick['first_para'] = first_para

                    elif ind in para_dict['depth'] and not second_para:
                        second_para= ind[n - 1]
                        input_values_dick['second_para']  = second_para
        


                if len(list(input_values_dick.keys())) == 1:

                        second_para = olrigin_depth
                        input_values_dick['second_para'] = second_para
                    
            if len(input_values_dick.keys()) == 3 :
                sorted_dict = dict(sorted(input_values_dick.items()))
                input_values = list(sorted_dict.values())
            else:
                input_values = list(input_values_dick.values())

            print(individual_words)
            precision_var = str(individual_words.get('precision_var', 0))


            quantity_var = individual_words.get('quantity_var')
            button_id =  0
            register_item = {
                'process_var': process_var,
                'precision_var': precision_var,
                'difficult_var': '0',
                'quantity_var': quantity_var,
                'button_id': button_id,
                'input_values': input_values,
                'result_var': 0

            }

            register_data[process_id] = register_item
            print(register_data)

            save_list.append(register_data)




        process_dict = {
            'tap_process' : ["M","タップ"],
            'hole_process' : ["キリ", "φ"],
            'poket_process' : ["P"],
        }



        for word in process_word.keys():

            for process_func, per_words in process_dict.items():
                if any(p_w in word for p_w in per_words):
                    process_setting(word, process_func)
                else:
                    process_func = 'hole_process'
                    per_words = ''
                    process_setting

        #save_listをjson形式保存関数に送る
        def creat_json_data(list):
            combined_data = {}
            for s_d in list:
                converted_data = {str(key): value for key, value in s_d.items()}
                combined_data.update(converted_data)

            name = 'orc_data.json'
            folder_path = r'C:\Estimate Generator\data'
            full_path = os.path.join(folder_path, name)

            # ファイルに保存
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=4)


        print('save_list', save_list)
        creat_json_data(save_list)



if __name__ == "__main__":
    share_image = 'useM8.png'
    # 使用例
    search = search_word(share_image)  # search_wordのインスタンスを作成
    contackt = contackt_circle(share_image, search)  # search_wordのインスタンスをcontackt_circleに渡す
    json_data_generator = generate_json_data(contackt)  # contackt_circleのインスタンスをgenerate_json_dataに渡す

    # メソッドを呼び出して処理
    