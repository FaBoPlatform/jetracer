from enum import Enum, auto

class EnvironmentCategory(Enum):
    """
    環境情報推論における基本カテゴリ。

    - GATE_LEFT: 電子掲示板で左矢印表示
    - GATE_RIGHT: 電子掲示板で右矢印表示
    - GATE_CENTER: 電子掲示板で前矢印表示
    - PARKING: 駐車状態
    - ETC: 分類できないもの
    - START_1〜3: スタートライン
    """
    GATE_LEFT = 0
    GATE_RIGHT = 1
    GATE_CENTER = 2
    ETC = 3

    def __str__(self):
        return self.name


class EnvironmentCategory540(Enum):
    """
    540度ターンに関するカテゴリ。

    - CORNER_FIRST: 540度ターンの突入領域
    - CORNER_END: 540度ターンの脱出または再突入領域
    """
    CORNER_FIRST = 0
    CORNER_END = 1
    CORNER_NOT = 2

    def __str__(self):
        return self.name
