# FaBo JetRacer Kit

このレポジトリは、[NVIDIA-AI-IOT/jetracer](http://github.com/NVIDIA-AI-IOT/jetracer)のForkプロジェクトです。

教育現場への導入を目的に、株式会社FaBoがキット化し、改良したバージョンとなります。　

主な修正点としては

- Jetson Nanoをマウントする箇所のカーボン化
- TAMIYA社 TT-02向けに細かい値の設定を可能にしたノートブック
- 学習方法等の工夫をおこなったノートブック

などが挙げられます。

## 各種ブランチ

- [AI86](https://github.com/FaBoPlatform/jetracer/tree/AI86) 最新のNotebook
- [Desktop](https://github.com/FaBoPlatform/jetracer/tree/Desktop) Desktop用 Notebook(Windows, OSXにも対応)
- [Race24](https://github.com/FaBoPlatform/jetracer/tree/Race24) ミニカーバトル2024用 Notebook
- [Next24](https://github.com/FaBoPlatform/jetracer/tree/Next24) Google Next 2024@ラスベガス 展示デモ
- [Race23](https://github.com/FaBoPlatform/jetracer/tree/Race23) ミニカーバトル2023用 Notebook
  
## 車体

|  [FaBo JetRacer Kit](https://fabo.store/collections/jetracer) |
|--------------|
| <img src="https://faboplatform.github.io/JetracerDocs/img/jetracer1.jpg" width=256>  | 
| 1/10th スケール |
| ベース車両は、TAMIYA社　TT-02|

## チュートリアル

ドキュメント
- [FaBo JetRacer Docs](https://faboplatform.github.io/JetracerDocs/)

動画チュートリアル(YouTube)
- [1.PWMの設定](https://www.youtube.com/watch?v=n5FJrSu17x0)
- [2.アノテーションと学習](https://www.youtube.com/watch?v=gz_bV-wJAO0&t=7s)
- [3.TensorRTへの変換](https://www.youtube.com/watch?v=zbNoygm1JSQ)
- [4.自動走行](https://www.youtube.com/watch?v=YQ8U5KHhLLA)

## 展示会デモ

<b>Google Next24@ラスベガス ブースデモ(Googleブース, Gemini連携デモ)</b><br>
[![youtube](https://img.youtube.com/vi/RqErJ61W3Jw/default.jpg)](https://www.youtube.com/watch?v=RqErJ61W3Jw)
[![youtube](https://img.youtube.com/vi/pLzW4NR5-y8/default.jpg)](https://www.youtube.com/watch?v=pLzW4NR5-y8)

<b>各種イベントデモ走行</b><br>
[![youtube](https://img.youtube.com/vi/Rbr38xTfuqY/default.jpg)](https://www.youtube.com/watch?v=Rbr38xTfuqY)

## レース

<b>自動運転ミニカーバトル 2023</b><br>

[Race23ブランチ](https://github.com/FaBoPlatform/jetracer/tree/Race23)に、レース時使用Notebookを公開しています。<br>

レースの様子<br>
[![youtube](https://img.youtube.com/vi/DJxsbYfvvCg/default.jpg)](https://www.youtube.com/watch?v=DJxsbYfvvCg) <br>

- [11_record_camera.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/11_record_camera.ipynb)
- [12_file_manager.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/12_file_manager.ipynb)
- [13_annotation.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/13_annotation.ipynb)
- [15_train.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/15_train.ipynb)
- [16_convert.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/16_convert.ipynb)
- [20_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/20_detect.ipynb)
- [21_convert_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/21_convert_detect.ipynb)
- [25_run_dual_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/25_run_dual_detect.ipynb)
  
のNotebookを使用してモデルを作成しました。

Colabでの学習用Notebook<br>
[FaBo JetRacerCloud](https://colab.research.google.com/drive/1GbDrNiosTKSJNOJiCiVgv6V8X-0GDBfW?usp=sharing)

自動運転ミニカーバトル 2023で使用したデータセットと学習済みモデル<br>
[Google Driveからダウンロード](https://drive.google.com/file/d/1_HXaD-Ev0keZ9yzCyCSvznkpXGhL3yhE/view?usp=sharing)

## Jetson Orin Nano用環境構築Script

- [Orin Nano JetPack 5.1.4 SD](https://github.com/FaBoPlatform/Jetson_script/blob/main/aicar/orin_nano/install.sh)

## Jetson Nano用SDカードイメージ

- [FaBo JetRacer Kit 1.0 for Jetpack4.6.1](https://drive.google.com/file/d/1tZ5bNfE9gJ67E_HGm_hXMXGRFWvKaoTe/view?usp=sharing)
- [FaBo JetRacer Kit 1.0 for Jetpack4.5.1](https://drive.google.com/file/d/1-MvsHPYKcunSOiaXaXR15DQP6QMJJhEm/view?usp=sharing)
