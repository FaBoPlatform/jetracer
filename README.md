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
- [Desktop](https://github.com/FaBoPlatform/jetracer/tree/Desktop) Desktop用 Notebook(Winodwsにも対応)
- [Race24](https://github.com/FaBoPlatform/jetracer/tree/Race24) ミニカーバトル2024用 Notebook
- [Next24](https://github.com/FaBoPlatform/jetracer/tree/Next24) Google Next 2024@ラスベガス 展示デモ
- [Race23](https://github.com/FaBoPlatform/jetracer/tree/Race23) ミニカーバトル2023用 Notebook
  
## プロジェクト

```
git clone -b Desktop https://github.com/FaBoPlatform/jetracer.git Desktop
cd Desktop
```

## パッケージのインストール

```
conda create --name jetracer python=3.9
conda activate jetracer
```

```
conda install pytorch torchvision cudatoolkit=11.8 -c pytorch -c nvidia
conda install opencv -c nvidia
```

```
pip install -r requirements.txt
```

## Jupyterの起動

```
cd notebooks
jupoyter notebooks
```
