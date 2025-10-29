from enum import Enum, auto

class EnvironmentCategory(Enum):
    """
    環境情報推論におけるカテゴリ。

    - GATE_LEFT: 電子掲示板で左矢印表示
    - GATE_RIGHT: 電子掲示板で右矢印表示
    - GATE_CENTER: 電子掲示板で前矢印表示
    - PARKING: 駐車状態
    - ETC: 分類できないもの
    - START_1: スタートライン1
    - START_2: スタートライン2
    - START_3: スタートライン3
    - CORNER_FIRST: 540度ターンの突入領域
    - CORNER_END: : 540度ターンの脱出 or 再突入領域

    開発者ノート:
    CATEGORIES (文字列 -> Enum.name) と POST_* (整数、0ベースインデックス -> Enum.value) 両方を纏めて定義
    """
    GATE_LEFT = 0
    GATE_RIGHT = 1
    GATE_CENTER = 2
    PARKING = 3
    ETC = 4
    START_1 = auto()
    START_2 = auto()
    START_3 = auto()
    CORNER_FIRST = auto()
    CORNER_END = auto()

    def __str__(self):
        return self.name
