# EGI-RAG 鍏稿瀷妗堜緥瀵规瘮

鑷姩鐢熸垚锛氬姣?Naive RAG 涓?EGI-RAG 鍦ㄥ櫔澹版枃妗ｅ満鏅笅鐨勭瓟妗堝樊寮傘€?

## 妗堜緥 1: rgb_0000

**闂**锛歐ho is the runner-up in the women's singles at the 2023 French Open?

**鍙傝€冪瓟妗?*锛氭棤

**姝ｇ‘鏂囨。鎽樿**锛?
- `doc_5`: Jun 12, 2023 ... Iga Swiatek won the French Open 2023 women's singles title with a 6-2, 5-7, 6-4 win over Karolina Muchova in the final on Saturday.
- `doc_1`: Members of my team are witnesses that ever since we first played, I knew we were going to play tough matches, play these finals ... I really hope we鈥檙e going to play many more f...

**鍣０/璇鏂囨。鎽樿**锛?
- `doc_26` (noise): Swiatek breaks back! Swiatek serving to stay ahead in the deciding set. Loopy forehand return from Muchova and Swiatek nets the forehand in response - 0-15. Double fault from Sw...
- `doc_19` (noise): Soon there was the increasingly familiar sight of Swiatek emerging in the stands for a celebratory huddle with her team and a few quiet words with her sports psychologist, Daria...

**Naive RAG 杈撳嚭** (閿欒)锛氭棤娉曟牴鎹粰瀹氫俊鎭‘瀹?

閫変腑 doc_ids: doc_26, doc_19, doc_6, doc_23, doc_11

**EGI-RAG 杈撳嚭** (閿欒)锛欳oco Gauff

鏍￠獙缁撴灉: supported | 杩唬杞暟: 1

閫変腑 doc_ids: doc_8, doc_19

**璇佹嵁鍙?*锛?
- `doc_8`: 6 Coco Gauff, runner-up to Swiatek last year, was the last American to be eliminated (by Swiatek in the quarterfinals).

**鏂囨。璇勫垎锛堣妭閫夛級**锛?
- `doc_8`: label=directly_supportive, score=0.95, reason=鏄庣‘鎻愬埌Coco Gauff鏄?023骞存硶缃戝コ鍗曚簹鍐涳紙runner-up to Swiatek last year锛夛紝鐩存帴鍥炵瓟闂銆?
- `doc_7`: label=irrelevant, score=0.0, reason=浠呮弿杩?023骞存硶缃戣禌浜嬫鍐靛拰绉垎濂栭噾锛屾湭鎻愬強濂冲崟浜氬啗淇℃伅銆?
- `doc_19`: label=partially_relevant, score=0.3, reason=鎻愬埌Swiatek澶哄啝鍜孧uchova鍐宠禌锛屼絾鏈槑纭鏄庝簹鍐涙槸璋侊紝闇€鎺ㄦ柇銆?
- `doc_11`: label=irrelevant, score=0.0, reason=鍐呭娑夊強2022骞磋禌浜嬶紝涓?023骞存硶缃戝コ鍗曚簹鍐涙棤鍏炽€?
- `doc_6`: label=irrelevant, score=0.0, reason=璁ㄨ绉垎鍜岀瀛愰€夋墜閫€璧涳紝鏈彁鍙婂コ鍗曚簹鍐涖€?

**淇缁撹**锛氫袱绉嶆柟娉曞潎鏈瓟瀵癸紝鍙兘闇€瑕佹洿寮虹殑鍐茬獊妫€娴嬫垨鎷掔瓟鏈哄埗銆?

## 妗堜緥 2: rgb_0003

**闂**锛歐hich animated series won the Emmy Award for Best Animated Program?

**鍙傝€冪瓟妗?*锛氭棤

**姝ｇ‘鏂囨。鎽樿**锛?
- `doc_4`: Netflix's League of Legends-based animated series Arcane has won an Emmy for Outstanding Animated Program, becoming the first streaming series to win in that category. It beat o...
- `doc_5`: Sep 3, 2022 ... 鈥淎rcane鈥?won the Emmy for Best Animated Program at Saturday evening's Creative Arts Emmys ceremony. It was the overwhelming favorite to win ...

**鍣０/璇鏂囨。鎽樿**锛?
- `doc_7` (noise): The Primetime Emmy Award for Outstanding Animated Program is a Creative Arts Emmy Award which is given annually to an animated series. In the following list, the first titles li...
- `doc_10` (noise): By subscribing, I agree to the Terms of Use and Privacy Policy. This site is protected by reCAPTCHA Enterprise and the Google Privacy Policy and Terms of Service apply. We will ...

**Naive RAG 杈撳嚭** (閿欒)锛氭棤娉曟牴鎹粰瀹氫俊鎭‘瀹?

閫変腑 doc_ids: doc_7, doc_10, doc_16, doc_24, doc_8

**EGI-RAG 杈撳嚭** (閿欒)锛欰rcane

鏍￠獙缁撴灉: supported | 杩唬杞暟: 1

閫変腑 doc_ids: doc_4, doc_24, doc_7

**璇佹嵁鍙?*锛?
- `doc_4`: Netflix's League of Legends-based animated series Arcane has won an Emmy for Outstanding Animated Program, becoming the first streaming series to win in that category.

**鏂囨。璇勫垎锛堣妭閫夛級**锛?
- `doc_7`: label=partially_relevant, score=0.4, reason=鏂囨。鎻忚堪浜嗗椤瑰巻鍙蹭笌瑙勫垯锛屼絾鏈洿鎺ョ粰鍑哄叿浣撹幏濂栧姩鐢荤郴鍒楀悕绉般€?
- `doc_24`: label=partially_relevant, score=0.5, reason=鏂囨。鍒楀嚭鑾峰娆℃暟鏈€澶氱殑绯诲垪锛屼絾鏈槑纭洖绛斿摢涓郴鍒楄幏濂栥€?
- `doc_4`: label=directly_supportive, score=0.95, reason=鏄庣‘璇存槑Arcane璧㈠緱浜嗚壘缇庡鏈€浣冲姩鐢昏妭鐩銆?
- `doc_25`: label=insufficient, score=0.2, reason=浠呮彁鍙?021骞存彁鍚嶄笌鑾峰鑰咃紝鏃犲叿浣撶郴鍒楀悕绉般€?
- `doc_23`: label=insufficient, score=0.2, reason=浠呮彁鍙?022骞存彁鍚嶄笌鑾峰鑰咃紝鏃犲叿浣撶郴鍒楀悕绉般€?

**淇缁撹**锛氫袱绉嶆柟娉曞潎鏈瓟瀵癸紝鍙兘闇€瑕佹洿寮虹殑鍐茬獊妫€娴嬫垨鎷掔瓟鏈哄埗銆?

## 妗堜緥 3: rgb_0004

**闂**锛欻ow much money did Texas Tech pay Marlene Stollings in the settlement?

**鍙傝€冪瓟妗?*锛氭棤

**姝ｇ‘鏂囨。鎽樿**锛?
- `doc_3`: That same month, Texas Tech paid $740,000 to settle a breach-of-contract lawsuit filed by former women鈥檚 basketball coach Marlene Stollings, who was fired in 2020 following a jo...
- `doc_2`: Texas Tech paid former women's basketball coach Marlene Stollings approximately $740,000 in settling a lawsuit she filed after being fired by the school in 2020, according to a ...

**鍣０/璇鏂囨。鎽樿**锛?
- `doc_15` (noise): [i] As standard procedure, the defendants collectively moved to dismiss its former coach鈥檚 complaint and in August 2021, the District Court granted their motion as for the breac...
- `doc_32` (noise): Aug 12, 2022 ... The former Lady Raiders coach was fired amid allegations of abuse.

**Naive RAG 杈撳嚭** (閿欒)锛氭棤娉曟牴鎹粰瀹氫俊鎭‘瀹?

閫変腑 doc_ids: doc_15, doc_32, doc_31, doc_34, doc_14

**EGI-RAG 杈撳嚭** (閿欒)锛?740,000

鏍￠獙缁撴灉: supported | 杩唬杞暟: 1

閫変腑 doc_ids: doc_3

**璇佹嵁鍙?*锛?
- `doc_3`: That same month, Texas Tech paid $740,000 to settle a breach-of-contract lawsuit filed by former women鈥檚 basketball coach Marlene Stollings, who was fired in 2020 following a joint investigation by The Intercollegiate and USA Today.

**鏂囨。璇勫垎锛堣妭閫夛級**锛?
- `doc_31`: label=insufficient, score=0.3, reason=鏂囨。鎻愬埌Stollings琚В闆囧拰璇夎锛屼絾鏈彁鍙婂拰瑙ｉ噾棰濄€?
- `doc_3`: label=directly_supportive, score=0.95, reason=鏄庣‘璇存槑Texas Tech鏀粯浜?740,000鍜岃В閲戙€?
- `doc_14`: label=irrelevant, score=0.0, reason=璁ㄨ鎹愭銆佸叾浠栨浠跺拰璇勮锛屾湭娑夊強Stollings鍜岃В閲戦銆?
- `doc_34`: label=misleading, score=0.1, reason=鏍囬鏆楃ず澶嶈亴锛屼絾瀹為檯鍐呭鏈彁渚涘拰瑙ｉ噾棰濓紝鍙兘璇銆?
- `doc_15`: label=insufficient, score=0.2, reason=璁ㄨ娉曞緥绋嬪簭锛屼絾鏈彁鍙婂叿浣撳拰瑙ｉ噾棰濄€?

**淇缁撹**锛氫袱绉嶆柟娉曞潎鏈瓟瀵癸紝鍙兘闇€瑕佹洿寮虹殑鍐茬獊妫€娴嬫垨鎷掔瓟鏈哄埗銆?

## 妗堜緥 4: rgb_0005

**闂**锛歐hen will Splatoon 3 be released?

**鍙傝€冪瓟妗?*锛氭棤

**姝ｇ‘鏂囨。鎽樿**锛?
- `doc_5`: Splatoon 3鈥?Splatoon 3 is the third entry in the Splatoon series and the sequel to Splatoon 2. Announced during the February 2021 Nintendo Direct, it was released on the Nintend...
- `doc_6`: On 10 August 2022, Nintendo broadcast a Splatoon 3-focused Nintendo Direct, revealing the date for the game's Splatfest World Premiere, a limited time demo Splatfest.[54] Ninten...

**鍣０/璇鏂囨。鎽樿**锛?
- `doc_16` (noise): Enter the Splatlands! Ink your way to the top in online modes like Turf War and Salmon Run. Discover the mysteries of story mode. Only on the Nintendo ...
- `doc_29` (noise): All Trailers and Gameplay Videos Updated 9/1/2022 A number of trailers and gameplay videos have been released for Splatoon 3. Check them out to learn more about the inkoming gam...

**Naive RAG 杈撳嚭** (閿欒)锛歋platoon 3 was released on 9 September 2022.

閫変腑 doc_ids: doc_5, doc_6, doc_10, doc_9, doc_16

**EGI-RAG 杈撳嚭** (閿欒)锛歋eptember 9, 2022

鏍￠獙缁撴灉: supported | 杩唬杞暟: 1

閫変腑 doc_ids: doc_7, doc_6, doc_5, doc_10

**璇佹嵁鍙?*锛?
- `doc_7`: Splatoon 3 was released on September 9, 2022, and is now available on the Nintendo Switch.
- `doc_6`: The game was released worldwide on 9 September 2022.
- `doc_5`: it was released on the Nintendo Switch on 9 September 2022.
- `doc_10`: Splatoon 3 releases on September 9, 2022, so hopefully, it is not too much longer after that.

**鏂囨。璇勫垎锛堣妭閫夛級**锛?
- `doc_29`: label=insufficient, score=0.1, reason=鏂囨。鍒楀嚭浜嗘洿鏂版棩鏈燂紝浣嗘湭鐩存帴鎻愬強Splatoon 3鐨勫彂琛屾棩鏈熴€?
- `doc_10`: label=partially_relevant, score=0.5, reason=鏂囨。鎻愬埌Splatoon 3浜?022骞?鏈?鏃ュ彂琛岋紝浣嗕富瑕佽璁篈miibo鑰岄潪鐩存帴鍥炵瓟鍙戣鏃ユ湡銆?
- `doc_7`: label=directly_supportive, score=0.95, reason=鏂囨。鏄庣‘璇存槑Splatoon 3浜?022骞?鏈?鏃ュ彂琛岋紝骞舵彁渚涗簡璇︾粏鏃堕棿淇℃伅銆?
- `doc_5`: label=directly_supportive, score=0.93, reason=鏂囨。鐩存帴鎸囧嚭Splatoon 3浜?022骞?鏈?鏃ュ湪Nintendo Switch涓婂彂琛屻€?
- `doc_6`: label=directly_supportive, score=0.94, reason=鏂囨。鏄庣‘璇存槑娓告垙浜?022骞?鏈?鏃ュ叏鐞冨彂琛屻€?

**淇缁撹**锛氫袱绉嶆柟娉曞潎鏈瓟瀵癸紝鍙兘闇€瑕佹洿寮虹殑鍐茬獊妫€娴嬫垨鎷掔瓟鏈哄埗銆?

## 妗堜緥 5: rgb_0007

**闂**锛歐hich team won the 2023 Big 12 Championships in women's golf?

**鍙傝€冪瓟妗?*锛氭棤

**姝ｇ‘鏂囨。鎽樿**锛?
- `doc_1`: Apr 23, 2023 ... DALLAS, Texas 鈥?No. 23 Oklahoma State women's golf swept both the team and individual titles at the Big 12 Championships at the Dallas ...
- `doc_2`: Apr 23, 2023 ... DALLAS 鈥?Oklahoma State posted a 54-hole score of 868 to claim its 11th Big 12 title and its second in three years. 路 Final Team Leaderboard. 1.

**鍣０/璇鏂囨。鎽樿**锛?
- `doc_19` (noise): Apr 23, 2023 ... During the final round, the team jumped to fourth place after posting a five-over 293. The Cyclones concluded with an overall score of 877 to ...
- `doc_10` (noise): DALLAS, Tex. 鈥?The Iowa State women's golf team earns a fourth-place finish at the Big 12 Women's Golf Championship at Dallas Athletic Club. The Cyclones had two freshman finish...

**Naive RAG 杈撳嚭** (閿欒)锛氭棤娉曟牴鎹粰瀹氫俊鎭‘瀹?

閫変腑 doc_ids: doc_19, doc_10, doc_14, doc_6, doc_15

**EGI-RAG 杈撳嚭** (閿欒)锛歄klahoma State

鏍￠獙缁撴灉: supported | 杩唬杞暟: 1

閫変腑 doc_ids: doc_1, doc_10

**璇佹嵁鍙?*锛?
- `doc_1`: No. 23 Oklahoma State women's golf swept both the team and individual titles at the Big 12 Championships at the Dallas ...

**鏂囨。璇勫垎锛堣妭閫夛級**锛?
- `doc_1`: label=directly_supportive, score=0.95, reason=鏂囨。鏄庣‘鎻愬埌Oklahoma State women's golf璧㈠緱浜?023骞碆ig 12閿︽爣璧涚殑鍥綋鍐犲啗锛岀洿鎺ュ洖绛斾簡闂銆?
- `doc_6`: label=irrelevant, score=0.0, reason=鏂囨。璁ㄨ鐨勬槸Pac-12濂冲瓙楂樺皵澶敠鏍囪禌锛屼笌Big 12鏃犲叧銆?
- `doc_14`: label=irrelevant, score=0.0, reason=鏂囨。鍐呭涓築ig 12鐢峰瓙楂樺皵澶椤瑰拰濂冲瓙楂樺皵澶椤圭殑鍙戝竷锛屾湭鎻愬強2023骞村コ瀛愰珮灏斿か閿︽爣璧涘啝鍐涖€?
- `doc_13`: label=irrelevant, score=0.0, reason=涓巇oc_14鍐呭鐩稿悓锛屽潎涓哄椤瑰彂甯冧俊鎭紝鏈秹鍙婂啝鍐涗俊鎭€?
- `doc_10`: label=partially_relevant, score=0.3, reason=鏂囨。鎻愬埌Iowa State鍦˙ig 12濂冲瓙楂樺皵澶敠鏍囪禌涓幏寰楃鍥涘悕锛屼絾鏈鏄庡啝鍐涙槸璋侊紝浠呮彁渚涢儴鍒嗚儗鏅俊鎭€?

**淇缁撹**锛氫袱绉嶆柟娉曞潎鏈瓟瀵癸紝鍙兘闇€瑕佹洿寮虹殑鍐茬獊妫€娴嬫垨鎷掔瓟鏈哄埗銆?
