# EGI-RAG 典型案例对比

自动生成：对比 Naive RAG 与 EGI-RAG 在噪声文档场景下的答案差异。

## 案例 1: rgb_0000

**问题**：Who is the runner-up in the women's singles at the 2023 French Open?

**参考答案**：无

**正确文档摘要**：
- `doc_5`: Jun 12, 2023 ... Iga Swiatek won the French Open 2023 women's singles title with a 6-2, 5-7, 6-4 win over Karolina Muchova in the final on Saturday.
- `doc_1`: Members of my team are witnesses that ever since we first played, I knew we were going to play tough matches, play these finals ... I really hope we’re going to play many more f...

**噪声/误导文档摘要**：
- `doc_26` (noise): Swiatek breaks back! Swiatek serving to stay ahead in the deciding set. Loopy forehand return from Muchova and Swiatek nets the forehand in response - 0-15. Double fault from Sw...
- `doc_19` (noise): Soon there was the increasingly familiar sight of Swiatek emerging in the stands for a celebratory huddle with her team and a few quiet words with her sports psychologist, Daria...

**Naive RAG 输出** (错误)：无法根据给定信息确定

选中 doc_ids: doc_26, doc_19, doc_6, doc_23, doc_11

**EGI-RAG 输出** (错误)：Coco Gauff

校验结果: supported | 迭代轮数: 1

选中 doc_ids: doc_8, doc_19

**证据句**：
- `doc_8`: 6 Coco Gauff, runner-up to Swiatek last year, was the last American to be eliminated (by Swiatek in the quarterfinals).

**文档评分（节选）**：
- `doc_8`: label=directly_supportive, score=0.95, reason=明确提到Coco Gauff是2023年法网女单亚军（runner-up to Swiatek last year），直接回答问题。
- `doc_7`: label=irrelevant, score=0.0, reason=仅描述2023年法网赛事概况和积分奖金，未提及女单亚军信息。
- `doc_19`: label=partially_relevant, score=0.3, reason=提到Swiatek夺冠和Muchova决赛，但未明确说明亚军是谁，需推断。
- `doc_11`: label=irrelevant, score=0.0, reason=内容涉及2022年赛事，与2023年法网女单亚军无关。
- `doc_6`: label=irrelevant, score=0.0, reason=讨论积分和种子选手退赛，未提及女单亚军。

**修正结论**：两种方法均未答对，可能需要更强的冲突检测或拒答机制。

## 案例 2: rgb_0003

**问题**：Which animated series won the Emmy Award for Best Animated Program?

**参考答案**：无

**正确文档摘要**：
- `doc_4`: Netflix's League of Legends-based animated series Arcane has won an Emmy for Outstanding Animated Program, becoming the first streaming series to win in that category. It beat o...
- `doc_5`: Sep 3, 2022 ... “Arcane” won the Emmy for Best Animated Program at Saturday evening's Creative Arts Emmys ceremony. It was the overwhelming favorite to win ...

**噪声/误导文档摘要**：
- `doc_7` (noise): The Primetime Emmy Award for Outstanding Animated Program is a Creative Arts Emmy Award which is given annually to an animated series. In the following list, the first titles li...
- `doc_10` (noise): By subscribing, I agree to the Terms of Use and Privacy Policy. This site is protected by reCAPTCHA Enterprise and the Google Privacy Policy and Terms of Service apply. We will ...

**Naive RAG 输出** (错误)：无法根据给定信息确定

选中 doc_ids: doc_7, doc_10, doc_16, doc_24, doc_8

**EGI-RAG 输出** (错误)：Arcane

校验结果: supported | 迭代轮数: 1

选中 doc_ids: doc_4, doc_24, doc_7

**证据句**：
- `doc_4`: Netflix's League of Legends-based animated series Arcane has won an Emmy for Outstanding Animated Program, becoming the first streaming series to win in that category.

**文档评分（节选）**：
- `doc_7`: label=partially_relevant, score=0.4, reason=文档描述了奖项历史与规则，但未直接给出具体获奖动画系列名称。
- `doc_24`: label=partially_relevant, score=0.5, reason=文档列出获奖次数最多的系列，但未明确回答哪个系列获奖。
- `doc_4`: label=directly_supportive, score=0.95, reason=明确说明Arcane赢得了艾美奖最佳动画节目奖。
- `doc_25`: label=insufficient, score=0.2, reason=仅提及2021年提名与获奖者，无具体系列名称。
- `doc_23`: label=insufficient, score=0.2, reason=仅提及2022年提名与获奖者，无具体系列名称。

**修正结论**：两种方法均未答对，可能需要更强的冲突检测或拒答机制。

## 案例 3: rgb_0004

**问题**：How much money did Texas Tech pay Marlene Stollings in the settlement?

**参考答案**：无

**正确文档摘要**：
- `doc_3`: That same month, Texas Tech paid $740,000 to settle a breach-of-contract lawsuit filed by former women’s basketball coach Marlene Stollings, who was fired in 2020 following a jo...
- `doc_2`: Texas Tech paid former women's basketball coach Marlene Stollings approximately $740,000 in settling a lawsuit she filed after being fired by the school in 2020, according to a ...

**噪声/误导文档摘要**：
- `doc_15` (noise): [i] As standard procedure, the defendants collectively moved to dismiss its former coach’s complaint and in August 2021, the District Court granted their motion as for the breac...
- `doc_32` (noise): Aug 12, 2022 ... The former Lady Raiders coach was fired amid allegations of abuse.

**Naive RAG 输出** (错误)：无法根据给定信息确定

选中 doc_ids: doc_15, doc_32, doc_31, doc_34, doc_14

**EGI-RAG 输出** (错误)：$740,000

校验结果: supported | 迭代轮数: 1

选中 doc_ids: doc_3

**证据句**：
- `doc_3`: That same month, Texas Tech paid $740,000 to settle a breach-of-contract lawsuit filed by former women’s basketball coach Marlene Stollings, who was fired in 2020 following a joint investigation by The Intercollegiate and USA Today.

**文档评分（节选）**：
- `doc_31`: label=insufficient, score=0.3, reason=文档提到Stollings被解雇和诉讼，但未提及和解金额。
- `doc_3`: label=directly_supportive, score=0.95, reason=明确说明Texas Tech支付了$740,000和解金。
- `doc_14`: label=irrelevant, score=0.0, reason=讨论捐款、其他案件和评论，未涉及Stollings和解金额。
- `doc_34`: label=misleading, score=0.1, reason=标题暗示复职，但实际内容未提供和解金额，可能误导。
- `doc_15`: label=insufficient, score=0.2, reason=讨论法律程序，但未提及具体和解金额。

**修正结论**：两种方法均未答对，可能需要更强的冲突检测或拒答机制。

## 案例 4: rgb_0005

**问题**：When will Splatoon 3 be released?

**参考答案**：无

**正确文档摘要**：
- `doc_5`: Splatoon 3​ Splatoon 3 is the third entry in the Splatoon series and the sequel to Splatoon 2. Announced during the February 2021 Nintendo Direct, it was released on the Nintend...
- `doc_6`: On 10 August 2022, Nintendo broadcast a Splatoon 3-focused Nintendo Direct, revealing the date for the game's Splatfest World Premiere, a limited time demo Splatfest.[54] Ninten...

**噪声/误导文档摘要**：
- `doc_16` (noise): Enter the Splatlands! Ink your way to the top in online modes like Turf War and Salmon Run. Discover the mysteries of story mode. Only on the Nintendo ...
- `doc_29` (noise): All Trailers and Gameplay Videos Updated 9/1/2022 A number of trailers and gameplay videos have been released for Splatoon 3. Check them out to learn more about the inkoming gam...

**Naive RAG 输出** (错误)：Splatoon 3 was released on 9 September 2022.

选中 doc_ids: doc_5, doc_6, doc_10, doc_9, doc_16

**EGI-RAG 输出** (错误)：September 9, 2022

校验结果: supported | 迭代轮数: 1

选中 doc_ids: doc_7, doc_6, doc_5, doc_10

**证据句**：
- `doc_7`: Splatoon 3 was released on September 9, 2022, and is now available on the Nintendo Switch.
- `doc_6`: The game was released worldwide on 9 September 2022.
- `doc_5`: it was released on the Nintendo Switch on 9 September 2022.
- `doc_10`: Splatoon 3 releases on September 9, 2022, so hopefully, it is not too much longer after that.

**文档评分（节选）**：
- `doc_29`: label=insufficient, score=0.1, reason=文档列出了更新日期，但未直接提及Splatoon 3的发行日期。
- `doc_10`: label=partially_relevant, score=0.5, reason=文档提到Splatoon 3于2022年9月9日发行，但主要讨论Amiibo而非直接回答发行日期。
- `doc_7`: label=directly_supportive, score=0.95, reason=文档明确说明Splatoon 3于2022年9月9日发行，并提供了详细时间信息。
- `doc_5`: label=directly_supportive, score=0.93, reason=文档直接指出Splatoon 3于2022年9月9日在Nintendo Switch上发行。
- `doc_6`: label=directly_supportive, score=0.94, reason=文档明确说明游戏于2022年9月9日全球发行。

**修正结论**：两种方法均未答对，可能需要更强的冲突检测或拒答机制。

## 案例 5: rgb_0007

**问题**：Which team won the 2023 Big 12 Championships in women's golf?

**参考答案**：无

**正确文档摘要**：
- `doc_1`: Apr 23, 2023 ... DALLAS, Texas – No. 23 Oklahoma State women's golf swept both the team and individual titles at the Big 12 Championships at the Dallas ...
- `doc_2`: Apr 23, 2023 ... DALLAS – Oklahoma State posted a 54-hole score of 868 to claim its 11th Big 12 title and its second in three years. · Final Team Leaderboard. 1.

**噪声/误导文档摘要**：
- `doc_19` (noise): Apr 23, 2023 ... During the final round, the team jumped to fourth place after posting a five-over 293. The Cyclones concluded with an overall score of 877 to ...
- `doc_10` (noise): DALLAS, Tex. – The Iowa State women's golf team earns a fourth-place finish at the Big 12 Women's Golf Championship at Dallas Athletic Club. The Cyclones had two freshman finish...

**Naive RAG 输出** (错误)：无法根据给定信息确定

选中 doc_ids: doc_19, doc_10, doc_14, doc_6, doc_15

**EGI-RAG 输出** (错误)：Oklahoma State

校验结果: supported | 迭代轮数: 1

选中 doc_ids: doc_1, doc_10

**证据句**：
- `doc_1`: No. 23 Oklahoma State women's golf swept both the team and individual titles at the Big 12 Championships at the Dallas ...

**文档评分（节选）**：
- `doc_1`: label=directly_supportive, score=0.95, reason=文档明确提到Oklahoma State women's golf赢得了2023年Big 12锦标赛的团体冠军，直接回答了问题。
- `doc_6`: label=irrelevant, score=0.0, reason=文档讨论的是Pac-12女子高尔夫锦标赛，与Big 12无关。
- `doc_14`: label=irrelevant, score=0.0, reason=文档内容为Big 12男子高尔夫奖项和女子高尔夫奖项的发布，未提及2023年女子高尔夫锦标赛冠军。
- `doc_13`: label=irrelevant, score=0.0, reason=与doc_14内容相同，均为奖项发布信息，未涉及冠军信息。
- `doc_10`: label=partially_relevant, score=0.3, reason=文档提到Iowa State在Big 12女子高尔夫锦标赛中获得第四名，但未说明冠军是谁，仅提供部分背景信息。

**修正结论**：两种方法均未答对，可能需要更强的冲突检测或拒答机制。

