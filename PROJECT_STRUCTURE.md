# PROJECT_STRUCTURE.md

```
employees/
├── CHANGELOG.md
├── FAQ.md
├── PROJECT_STRUCTURE.md
├── README.md
├── ROADMAP.md
├── aic/
│   ├── __init__.py
│   ├── aic_config.json
│   ├── core/
│   │   ├── __init__.py
│   │   ├── browser_manager.py
│   │   ├── file_search.py
│   │   ├── message_handler.py
│   │   └── timer.py
│   ├── handlers/
│   │   ├── stage_handler.py
│   │   └── token_parser.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── output/
│   │   ├── approved_code_20260424_164249.txt
│   │   ├── approved_code_20260424_183445.txt
│   │   ├── documentation_20260424_164527.md
│   │   ├── documentation_20260424_184030.md
│   │   ├── report_20260424_165036.md
│   │   └── report_20260424_184116.md
│   ├── prompts/
│   │   ├── Analyst.txt
│   │   ├── Boss.txt
│   │   ├── Chief_developer.txt
│   │   └── Ordinary_developer.txt
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── panels.py
│   │   └── timer_display.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── text_utils.py
├── aic_config.json
├── first part/
│   ├── CHANGELOG.md
│   ├── FAQ.md
│   ├── PROJECT_STRUCTURE.md
│   ├── README.md
│   ├── ROADMAP.md
│   ├── aic/
│   │   ├── __init__.py
│   │   ├── aic_config.json
│   │   ├── copy/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── browser_manager.py
│   │   │   ├── file_search.py
│   │   │   ├── message_handler.py
│   │   │   └── timer.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── stage_handler.py
│   │   │   ├── tester_handler.py
│   │   │   └── token_parser.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── output/
│   │   │   └── output_history/
│   │   │       ├── approved_code_20260424_164249.txt
│   │   │       ├── approved_code_20260424_212457.txt
│   │   │       ├── approved_code_20260424_225740.txt
│   │   │       ├── documentation_20260424_164527.md
│   │   │       ├── documentation_20260424_212735.md
│   │   │       ├── documentation_20260424_230018.md
│   │   │       ├── documentation_20260424_230530.md
│   │   │       ├── report_20260424_165036.md
│   │   │       ├── report_20260424_213246.md
│   │   │       └── report_20260424_231042.md
│   │   ├── prompts/
│   │   │   ├── Analyst.txt
│   │   │   ├── Boss.txt
│   │   │   ├── Chief_developer.txt
│   │   │   ├── Ordinary_developer.txt
│   │   │   └── Tester.txt
│   │   ├── testers/
│   │   │   ├── __init__.py
│   │   │   └── unit_tests/
│   │   │       ├── .pytest_cache/
│   │   │       │   ├── CACHEDIR.TAG
│   │   │       │   ├── README.md
│   │   │       │   └── v/
│   │   │       │       └── cache/
│   │   │       │           ├── lastfailed
│   │   │       │           └── nodeids
│   │   │       ├── __init__.py
│   │   │       └── test_browser_manager.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py
│   │   │   ├── panels.py
│   │   │   └── timer_display.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py
│   │       └── text_utils.py
│   ├── script.py
│   ├── лог
│   └── рабочая версия AIC.zip
├── script.py
├── second part/
│   ├── CHANGELOG.md
│   ├── FAQ.md
│   ├── PROJECT_STRUCTURE.md
│   ├── README.md
│   ├── ROADMAP.md
│   ├── config.json
│   ├── core/
│   │   ├── __init__.py
│   │   ├── lm_studio_client.py
│   │   └── orchestrator.py
│   ├── logs/
│   │   ├── 2026-05-02/
│   │   │   ├── 18-08-42.txt
│   │   │   ├── 18-14-13.txt
│   │   │   ├── 18-30-33.txt
│   │   │   ├── 18-31-36.txt
│   │   │   ├── 18-37-56.txt
│   │   │   ├── 18-38-07.txt
│   │   │   ├── 18-38-31.txt
│   │   │   ├── 18-38-44.txt
│   │   │   ├── 18-48-29.txt
│   │   │   ├── 19-21-38.txt
│   │   │   ├── 19-49-07.txt
│   │   │   ├── 20-44-33.txt
│   │   │   └── 21-08-24.txt
│   │   ├── 2026-05-03/
│   │   │   └── 21-28-22.txt
│   │   ├── 2026-05-04/
│   │   │   ├── 20-08-19.txt
│   │   │   ├── 20-14-56.txt
│   │   │   ├── 20-15-08.txt
│   │   │   ├── 20-25-51.txt
│   │   │   ├── 20-47-46.txt
│   │   │   └── 22-15-51.txt
│   │   ├── 2026-05-05/
│   │   │   ├── 14-39-00.txt
│   │   │   ├── 15-39-13.txt
│   │   │   ├── 16-28-14.txt
│   │   │   ├── 21-47-37.txt
│   │   │   └── 22-13-59.txt
│   │   └── 2026-05-06/
│   │       ├── 18-33-41.txt
│   │       ├── 20-49-50.txt
│   │       └── 21-46-36.txt
│   ├── main.py
│   ├── prompts/
│   │   ├── Analyst.yaml
│   │   ├── Boss.yaml
│   │   ├── Chief_developer.yaml
│   │   ├── Chief_tester.yaml
│   │   ├── Distributor.yaml
│   │   ├── Ordinary_developer.yaml
│   │   └── Ordinary_tester.yaml
│   ├── script.py
│   └── ui/
│       ├── __init__.py
│       └── panels.py
└── third part/
    ├── 76.25%.7z
    ├── CHANGELOG.md
    ├── FAQ.md
    ├── PATTERN/
    │   ├── feature_cache/
    │   │   └── train_orig.pkl
    │   ├── features/
    │   │   ├── edit_distance_classifier.py
    │   │   ├── hybrid_features.py
    │   │   ├── nonogram_features.py
    │   │   ├── pattern_stick_features.py
    │   │   ├── voice_stick_features.py
    │   │   └── word_sequence_features.py
    │   ├── main.py
    │   ├── mnist.pkl.gz
    │   ├── models/
    │   │   ├── coarse_to_fine.py
    │   │   ├── hybrid_recursive.py
    │   │   ├── pair_pattern_net.py
    │   │   └── super_hybrid.py
    │   ├── tests/
    │   │   ├── test_logical.py
    │   │   ├── test_sequence_visual.py
    │   │   ├── test_super_hybrid.py
    │   │   └── visualize_errors.py
    │   ├── text
    │   ├── utils.py
    │   └── Отчёт
    ├── PROJECT_STRUCTURE.md
    ├── README.md
    ├── ROADMAP.md
    ├── main.py
    ├── mnist.pkl.gz
    └── script.py
```
