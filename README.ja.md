# cat-music-patterns

## 用途
- cmrt-client-playgroundから利用
  - chord進行
  - Tone.jsモード（cmrtをlocalで起動していないとき）のときの、Tone.js音色
- cmrtから利用
  - `surge-xt-patch-voicing.json` : keyboard画面でのchord/アルペジオ の判別用（自動判別結果）
  - `surge-xt-patch-voicing-overrides.json` : 上に同じ（手動補正結果）
- cat-plugin-playerから利用
  - `surge-xt-patch-catalog.json` : cmrt のない環境で音色を選べるようにする用
  - `surge-xt-fx-states.json` : Effects の preset を高速に鳴らせるようにする用
  - `surge-xt-start-delay.json` : waitなしで鳴らせる音色か？の判別用
  - `patch-pitch-tracking.json` : drum/percussion欄の音色について、pitched percussion欄に移動すべきか？の判別用

## いろいろ

### from-mutopia/
- 「The Mutopia Projectによる、CC0ライセンスで自由に扱えるデータ」を配置しています。
  - 例えば、クラシック、バッハのトッカータとフーガ ニ短調 BWV 565。
  - データの用途は、例えば、バッハのトッカータとフーガ ニ短調 BWV 565の一部または全体を、そのままあるいはアレンジして演奏する用です。
  - 元データをそのまま配置し、元URLを書いているのは、利用者の参考用です。
  - CC0のメリットは、許可なしで再配布も可能なこと等です。The Mutopia Projectスタッフの尽力に感謝します。

## 頻繁に破壊的変更をします
