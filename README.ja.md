# cat-music-patterns

## 用途
- cmrt-client-playgroundから利用
  - chord進行
  - Tone.jsモード（cmrtをlocalで起動していないとき）のときの、Tone.js音色
- cmrtから利用
  - `surge-xt-patch-voicing.json` : keyboard画面でのchord/アルペジオ の判別用（自動判別結果）
  - `surge-xt-patch-voicing-overrides.json` : 上に同じ（手動補正結果）
- cat-plugin-playerから利用
  - `surge-xt-patch-catalog.json` : cmrt の無い環境で Surge XT の音色を選ぶ catalog（Surge XT 1.3.4 から生成）
  - `surge-xt-fx-states.json` : Surge XT Effects の preset ごとの準備済み state。`.srgfx` の SHA-256 で引く（Surge XT 1.3.4 から生成）
  - `surge-xt-start-delay.json` : Surge XT の音色ごとに、インスタンス化直後の待ち時間を0msにして発音しても問題ないかの実測結果（cat-plugin-player の `measure-surge-start-delay` で生成）
  - `patch-pitch-tracking.json` : drum の percussion 欄に入る音色（plugin を問わない）ごとに、note を変えると音高がついてくるか（`tracks_keyboard`）の実測結果。true の音色は lead へ移す。`plugin_id`+`display` で引く。`observations` は note 48/49/55/60 で推定した周波数（推定できなかった note は `null`）
    - 生成: clap-mml-render-tui の repository で `cargo run --release -p clap-mml-render-tui -- build-pitch-tracking --output ../cat-music-patterns/patch-pitch-tracking.json`（cmrt の catalog を対象にし、1 音色ごとに clap-mml-play-server の `probe-pitch-tracking` を起動して測る）

## いろいろ

### from-mutopia/
- 「The Mutopia Projectによる、CC0ライセンスで自由に扱えるデータ」を配置しています。
  - 例えば、クラシック、バッハのトッカータとフーガ ニ短調 BWV 565。
  - データの用途は、例えば、バッハのトッカータとフーガ ニ短調 BWV 565の一部または全体を、そのままあるいはアレンジして演奏する用です。
  - 元データをそのまま配置し、元URLを書いているのは、利用者の参考用です。
  - CC0のメリットは、許可なしで再配布も可能なこと等です。The Mutopia Projectスタッフの尽力に感謝します。

## 頻繁に破壊的変更をします
