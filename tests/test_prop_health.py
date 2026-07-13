import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from prop_health import Sample, health, ANSWER

def test_green():
    r = health(Sample(1.0, 0.01, 2))
    assert r["status"]=="GREEN" and r["answer"]==ANSWER

def test_red():
    assert health(Sample(0.5, 0.0, 1))["status"]=="RED"

if __name__=="__main__":
    test_green(); test_red(); print("ok")
