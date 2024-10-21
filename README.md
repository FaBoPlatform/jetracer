# FaBo JetRacer Kit(Race24ブランチ)

このレポジトリは、[NVIDIA-AI-IOT/jetracer](http://github.com/NVIDIA-AI-IOT/jetracer)のForkプロジェクトです。

## 各種ブランチ

- [AI86](https://github.com/FaBoPlatform/jetracer/tree/AI86) ハンズオン用のNotebook(基本的なNotebook)
- [Desktop](https://github.com/FaBoPlatform/jetracer/tree/Desktop) Desktop用 Notebook(Windows, OSXにも対応)
- [Race24](https://github.com/FaBoPlatform/jetracer/tree/Race24) ミニカーバトル2024用 Notebook
- [Next24](https://github.com/FaBoPlatform/jetracer/tree/Next24) Google Next 2024@ラスベガス 展示デモ
- [Race23](https://github.com/FaBoPlatform/jetracer/tree/Race23) ミニカーバトル2023用 Notebook
  
## レース

- [自動運転ミニカーバトル 2024](https://autonomous-minicar-battle.github.io/race-2024/)(2024年10/26(日)開催)

## 車体

![Race24](https://github.com/user-attachments/assets/314b2018-5fbb-48d8-926f-1e0ab66c2c09)

## Hardware

- FaBo JetRacer Kit for Race Edition
- Jetson Orin Nano
- Camera(IMX219) x 2
  
## レース要件

コース途中に矢印が表示されるので、矢印側に走行を寄せる。

## 推論の動作

- 走行モデル(矢印右走行)
- 走行モデル(矢印左走行)
- 駐車モデル
- 環境情報モデル(周回カウント)

の4モデルで走行を実現。

