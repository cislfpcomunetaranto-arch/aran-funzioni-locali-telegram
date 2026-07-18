\
from src.aran_scraper import extract_item_links, parse_item


def test_extract_item_links():
    html = """
    <html><body>
      <a href="/orient-applicativi/esempio-uno/">Uno</a>
      <a href="https://www.aranagenzia.it/orient-applicativi/esempio-due/">Due</a>
      <a href="/orientamenti-applicativi/">Elenco</a>
    </body></html>
    """
    links = extract_item_links(
        html,
        "https://www.aranagenzia.it/orientamenti-applicativi/",
    )
    assert len(links) == 2


def test_parse_item():
    html = """
    <html>
      <head><title>Quesito di prova</title></head>
      <body>
        <main>
          <article>
            <h1>Quesito di prova</h1>
            <div class="entry-content">
              <p>Id: 37473</p>
              <p>Precedente ID: CFL999</p>
              <p>Testo dell'orientamento.</p>
              <div><strong>Area/Comparto</strong></div>
              <div>Comparto funzioni locali</div>
              <div><strong>Argomento</strong></div>
              <div>Riposo compensativo</div>
              <div><strong>Data pubblicazione</strong></div>
              <div>04 Giugno 2026</div>
            </div>
          </article>
        </main>
      </body>
    </html>
    """
    item = parse_item(html, "https://www.aranagenzia.it/orient-applicativi/prova/")
    assert item.item_id == "37473"
    assert item.previous_id == "CFL999"
    assert item.title == "Quesito di prova"
