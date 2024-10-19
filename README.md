# FaBo JetRacer Kit(Nextブランチ)

このレポジトリは、[NVIDIA-AI-IOT/jetracer](http://github.com/NVIDIA-AI-IOT/jetracer)のForkプロジェクトです。

## 各種ブランチ

- [AI86](https://github.com/FaBoPlatform/jetracer/tree/AI86) ハンズオン用のNotebook(基本的なNotebook)
- [Desktop](https://github.com/FaBoPlatform/jetracer/tree/Desktop) Desktop用 Notebook(Windows, OSXにも対応)
- [Race24](https://github.com/FaBoPlatform/jetracer/tree/Race24) ミニカーバトル2024用 Notebook
- [Next24](https://github.com/FaBoPlatform/jetracer/tree/Next24) Google Next 2024@ラスベガス 展示デモ
- [Race23](https://github.com/FaBoPlatform/jetracer/tree/Race23) ミニカーバトル2023用 Notebook
  
## 展示会

-[Google Cloud Next 24](https://cloud.withgoogle.com/next)

## ブース

Googleブース

![IMG_6152](https://github.com/user-attachments/assets/ef42495b-f47a-4ebd-aea7-7edd7cba4a39)

## デモ要件

Geminiからの指示を受けて目的地までJetRacerを自動走行させる

## 推論の動作

- 走行モデル(真中直進走行)
- 走行モデル(内側直進走行)
- 走行モデル(外側直進走行)
- 走行モデル(真中右折走行)
- 走行モデル(内側右折走行)
- 環境情報モデル(場所判定)

の6モデルで走行を実現。

推論の動画
[![youtube](https://img.youtube.com/vi/pLzW4NR5-y8/default.jpg)](https://www.youtube.com/watch?v=pLzW4NR5-y8)

## Hardware

- FaBo JetRacer Kit for Reace Edition
- Jetson Orin Nano
- Camera(IMX219) x 2
- LoRaモジュール(Geminiからの指示を転送)

## デモの様子

[![youtube](https://img.youtube.com/vi/cO0iVCv9cfI/default.jpg)](https://www.youtube.com/watch?v=cO0iVCv9cfI)   [![youtube](https://img.youtube.com/vi/RqErJ61W3Jw/default.jpg)](https://www.youtube.com/watch?v=RqErJ61W3Jw) |

