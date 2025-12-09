To run Python vs Rust via PyO3 benchmarks run in the main folder:

`rm -rf .venv`

`python3 -m venv .venv`

`source .venv/bin/activate`

`maturin develop --release`

`python new_main_adjusted.py`