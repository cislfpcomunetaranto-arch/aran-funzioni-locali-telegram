\
name: Controllo orientamenti ARAN

on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Prova senza pubblicare su Telegram"
        required: true
        default: true
        type: boolean
      bootstrap_only:
        description: "Registra gli orientamenti esistenti senza pubblicarli"
        required: true
        default: true
        type: boolean
  schedule:
    # GitHub usa UTC. Esecuzione ogni 30 minuti.
    - cron: "7,37 * * * *"

permissions:
  contents: write

concurrency:
  group: aran-monitor
  cancel-in-progress: false

jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Scarica il repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configura Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Installa le dipendenze
        run: pip install -r requirements.txt

      - name: Imposta la modalità di esecuzione
        id: mode
        shell: bash
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "dry_run=${{ inputs.dry_run }}" >> "$GITHUB_OUTPUT"
            echo "bootstrap_only=${{ inputs.bootstrap_only }}" >> "$GITHUB_OUTPUT"
          else
            echo "dry_run=false" >> "$GITHUB_OUTPUT"
            echo "bootstrap_only=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Esegui il monitor
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
          DRY_RUN: ${{ steps.mode.outputs.dry_run }}
          BOOTSTRAP_ONLY: ${{ steps.mode.outputs.bootstrap_only }}
          MAX_LISTING_PAGES: "3"
        run: python -m src.main

      - name: Salva lo stato aggiornato
        shell: bash
        run: |
          if git diff --quiet -- data/state.json; then
            echo "Nessuna modifica allo stato."
            exit 0
          fi

          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/state.json
          git commit -m "Aggiorna stato orientamenti ARAN"
          git push
