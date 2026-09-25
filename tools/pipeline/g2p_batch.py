"""韓文唸法（g2pk2）：讀 stdin 的 JSON 字串陣列，輸出同順序的唸法陣列。
要用工作區的 .venv-g2p 跑（g2pk2＋python-mecab-ko；它和 wordfreq 需要的 mecab-python3 裝在同一個 venv 會互相蓋掉）。
g2pk 抓不到詞彙性的緊音化（여권 [여꿘]、결제 [결쩨]），字典查得到的詞一律以 KRDict 的發音欄為準。"""
import contextlib, json, sys, warnings
warnings.filterwarnings("ignore")
with contextlib.redirect_stdout(sys.stderr):   # g2pk2 載入時會在 stdout 印「mecab installed」，會弄壞輸出的 JSON
    from g2pk2 import G2p
    g = G2p()
texts = json.load(sys.stdin)
json.dump([g(t) if t else "" for t in texts], sys.stdout, ensure_ascii=False)
