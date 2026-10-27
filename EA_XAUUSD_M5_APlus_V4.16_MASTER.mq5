name: Periksa EA XAUUSD APlus V4.16

on:
workflow_dispatch:
push:
paths:
- "EA_XAUUSD_M5_APlus_V4.16_MASTER.mq5"
- "uji_ea.py"
- ".github/workflows/windows.yml"

jobs:
periksa-file:
runs-on: ubuntu-latest
steps:
- name: Ambil repository
uses: actions/checkout@v4

  - name: Periksa file EA
    shell: bash
    run: |
      set -eu
      FILE="EA_XAUUSD_M5_APlus_V4.16_MASTER.mq5"

      test -s "$FILE"
      echo "File EA ditemukan dan tidak kosong."

      grep -Eq 'OnInit[[:space:]]*\(' "$FILE" || {
        echo "ERROR: Fungsi OnInit tidak ditemukan."
        exit 1
      }

      grep -Eq 'OnTick[[:space:]]*\(' "$FILE" || {
        echo "ERROR: Fungsi OnTick tidak ditemukan."
        exit 1
      }

      echo "Deklarasi OnInit dan OnTick ditemukan."

  - name: Siapkan Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"

  - name: Jalankan tes Python
    run: python uji_ea.py