# W06-015／E11-018 重引例位置

共享引文：「詩人之賦麗以則，辭人之賦麗以淫」。

| split | sent_id | 篇名 | 作者 | 分期 | 位置 |
|---|---|---|---|---|---|
| v2_main | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | test |
| v2_main | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | test |
| v2_grouped | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train |
| v2_grouped | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | test |
| v3_labelonly | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | test |
| v3_labelonly | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | test |
| v3_main | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train |
| v3_main | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |
| v3_grouped | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train |
| v3_grouped | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |
| v3_genre_experiment | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train（子書 held-out 以此 split 為準） |
| v3_genre_experiment | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | not in 子書 test（史書） |
| v3_P1_liuan_wangchong | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train |
| v3_P1_liuan_wangchong | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |
| v3_P2_liuan_huantan | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | train |
| v3_P2_liuan_huantan | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |
| v3_P3_yangxiong_wangchong | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | test |
| v3_P3_yangxiong_wangchong | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |
| v3_P4_yangxiong_huantan | W06-015 | 法言·吾子（節選） | 揚雄 | 西漢 | test |
| v3_P4_yangxiong_huantan | E11-018 | 漢書·藝文志（詩、詩賦略節選） | 班固 | 東漢 | train |

注意：v2_main 與 v3_labelonly 兩者都在測試；v3_main 與 v3_grouped 兩者都在訓練。
v2_grouped 是 W06 在訓練、E11 在測試，才是重引跨切分的實例。
作者配對中，W06 在 P3/P4 為測試、P1/P2 為訓練；E11 在四組皆為訓練。
