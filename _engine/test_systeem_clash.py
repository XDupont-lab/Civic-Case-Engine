#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit- en regressietest voor de Systeem-Clash Sentiment Analyzer."""
import sys
from pathlib import Path

engine_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(engine_dir))

from systeem_clash_sentiment import SysteemClashAnalyzer

def run_tests():
    analyzer = SysteemClashAnalyzer()

    # Test 1: Harde ambtelijke afwijzing met hoge cloaking (sussende opening + harde afwijzing)
    sample_cloaked = (
        "Geachte heer, Met vriendelijke groet sluiten wij af en wensen u een fijn weekend. "
        "Wij begrijpen dat dit vervelend voor u is. Echter, uw verzoek is buiten behandeling gesteld "
        "en afgewezen wegens het verstrijken van de fatale termijn. Er is geen sprake van een fout in de systemen."
    )
    res1 = analyzer.analyze_text(sample_cloaked, "test_cloaked")
    assert res1.monodromy_cloaking >= 0.50, f"Expected high cloaking, got {res1.monodromy_cloaking}"
    assert res1.agency_w < 0.20, f"Expected low agency w, got {res1.agency_w}"
    assert res1.gu_ratio >= 0.50, f"Expected high gu_ratio, got {res1.gu_ratio}"
    print("PASS: Test 1 (Monodromy-Cloaking & Lage Agency)")

    # Test 2: Gezonde dialoog / maatwerk (Regime E / F kandidaat)
    sample_dialogue = (
        "Beste burger, In overleg met u kijken we naar maatwerk voor uw situatie. "
        "U heeft de keuze om uw voorkeur aan te geven. Wij nodigen u uit voor een persoonlijk gesprek "
        "waarin we gezamenlijk de medische feiten en uw dossier doornemen."
    )
    res2 = analyzer.analyze_text(sample_dialogue, "test_dialogue")
    assert res2.agency_w >= 0.35, f"Expected higher agency w, got {res2.agency_w}"
    assert res2.psi_res > 0.0, f"Expected positive resonance, got {res2.psi_res}"
    assert res2.monodromy_cloaking < 0.30, f"Expected low cloaking, got {res2.monodromy_cloaking}"
    print("PASS: Test 2 (Gezonde Dialoog & Positieve Resonantie)")

    # Test 3: Eufemisering & Afschuiving (Wet 9: nu vermindering)
    sample_euphemism = (
        "Het betreft een menselijke fout en administratieve omissie tijdens de afhandeling. "
        "Er is geen sprake van systeemoverschrijdende contaminatie in het Datafundament."
    )
    res3 = analyzer.analyze_text(sample_euphemism, "test_euphemism")
    assert res3.name_readiness_nu <= 0.40, f"Expected low nu due to euphemisms, got {res3.name_readiness_nu}"
    assert res3.theta_em_deg > 10.0, f"Expected framing-drift theta_em > 10, got {res3.theta_em_deg}"
    print("PASS: Test 3 (Wet 9 Observer-Inhibitie & Eufemisering)")

    print()
    print("ALLE SYSTEEM-CLASH TESTS GESLAAGD (100% OK)")
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
