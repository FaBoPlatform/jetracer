# FaBo JetRacer Kit

このレポジトリは、[NVIDIA-AI-IOT/jetracer](http://github.com/NVIDIA-AI-IOT/jetracer)のForkプロジェクトです。

## 各種ブランチ

- [AI86](https://github.com/FaBoPlatform/jetracer/tree/AI86) ハンズオン用のNotebook(基本的なNotebook)
- [Desktop](https://github.com/FaBoPlatform/jetracer/tree/Desktop) Desktop用 Notebook(Windows, OSXにも対応)
- [Race24](https://github.com/FaBoPlatform/jetracer/tree/Race24) ミニカーバトル2024用 Notebook
- [Next24](https://github.com/FaBoPlatform/jetracer/tree/Next24) Google Next 2024@ラスベガス 展示デモ
- [Race23](https://github.com/FaBoPlatform/jetracer/tree/Race23) ミニカーバトル2023用 Notebook
  
## レース

- [自動運転ミニカーバトル 2023](https://autonomous-minicar-battle.studio.site/)(2023年11/26(日)開催)

## レース要件

周回が偶数回の場合はショートカットをつかえ、周回が奇数回の場合はそのまま走行。

## 推論の動作

- 走行モデル(通常走行)
- 走行モデル(ショートカット走行)
- 環境情報モデル(周回カウント)

の3モデルで走行を実現。

## 決勝レースの様子

[![youtube](https://img.youtube.com/vi/_7cuafEg-AM/default.jpg)](https://www.youtube.com/watch?v=_7cuafEg-AM) <br>

## レースで使用したNotebook

- [11_record_camera.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/11_record_camera.ipynb)
- [12_file_manager.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/12_file_manager.ipynb)
- [13_annotation.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/13_annotation.ipynb)
- [15_train.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/15_train.ipynb)
- [16_convert.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/16_convert.ipynb)
- [20_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/20_detect.ipynb)
- [21_convert_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/21_convert_detect.ipynb)
- [25_run_dual_detect.ipynb](https://github.com/FaBoPlatform/jetracer/blob/Race23/notebooks/25_run_dual_detect.ipynb)

## Dataset

自動運転ミニカーバトル 2023で使用したデータセットと学習済みモデル<br>
- [Google Driveからダウンロード](https://drive.google.com/file/d/1_HXaD-Ev0keZ9yzCyCSvznkpXGhL3yhE/view?usp=sharing)
