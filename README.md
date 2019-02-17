# 割方体
正方形に切れ込みを入れた文字のフォント

# Build 

Build requires:
- Un\*x system
- Inkscape
- Python3 + pip
- Xvfb (optional)

On ubuntu you can install these prerequisites with:
```
sudo apt-get install inkscape python3-pip xvfb
```

Run the following commands to build `build/kappotaiw.otf` and `build/kappotaib.otf`
```
pip install -r requirements.txt
Xvfb :99
DISPLAY=:99 make
```

# License / ライセンス

これらのフォント及びビルドスクリプトはフリー（自由な）ソフトウエアです。あらゆる改変の有無に関わらず、また商業的な利用であっても、自由にご利用、複製、再配布することができますが、全て無保証とさせていただきます。

These fonts and build scripts are free software. Unlimited permission is granted to use, copy, and distribute them, with or without modification, either commercially or noncommercially. THIS SOFTWARE IS PROVIDED “AS IS” WITHOUT WARRANTY.
