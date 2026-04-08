import gradio as gr
from scraper import Website, scrape_multiple
from llm_service import extract_relevant_links, generate_brochure_stream

def create_brochure(company_name: str, url: str):
    """
    Pipeline complet :
    1. Scrape la page principale
    2. Extrait les liens pertinents via LLM
    3. Scrape les sous-pages
    4. Génère la brochure en streaming
    """
    if not company_name.strip() or not url.strip():
        yield "⚠️ Veuillez renseigner le nom de l'entreprise et l'URL."
        return

    if not url.startswith("http"):
        url = "https://" + url

    # Étape 1 : Scrape la page principale
    yield "🔍 Analyse de la page principale..."
    try:
        main_site = Website(url)
    except ValueError as e:
        yield f"❌ Erreur de scraping : {e}"
        return

    # Étape 2 : LLM extrait les liens pertinents
    yield "🤖 Identification des sections pertinentes..."
    links_response = extract_relevant_links(url, main_site.links)

    relevant_urls = [item.url for item in links_response.links[:4]]  # Max 4 sous-pages
    all_urls = [url] + relevant_urls

    yield f"📄 {len(relevant_urls)} sous-pages trouvées. Scraping en cours..."

    # Étape 3 : Scrape toutes les pages
    aggregated_content = scrape_multiple(all_urls)

    # Étape 4 : Génère la brochure en streaming
    yield "✍️ Génération de la brochure...\n\n"
    for partial_result in generate_brochure_stream(company_name, aggregated_content):
        yield partial_result


# Interface Gradio
with gr.Blocks(title="AI Brochure Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏢 AI Brochure Generator
        Génère automatiquement une brochure professionnelle à partir du site web d'une entreprise.
        *Propulsé par Llama 3.3-70b via Groq*
        """
    )

    with gr.Row():
        company_input = gr.Textbox(
            label="Nom de l'entreprise",
            placeholder="Ex: Anthropic",
        )
        url_input = gr.Textbox(
            label="URL du site web",
            placeholder="Ex: https://anthropic.com",
        )

    generate_btn = gr.Button("🚀 Générer la brochure", variant="primary")

    output = gr.Markdown(label="Brochure générée")

    gr.Examples(
        examples=[
            ["Anthropic", "https://anthropic.com"],
            ["Hugging Face", "https://huggingface.co"],
        ],
        inputs=[company_input, url_input],
    )

    generate_btn.click(
        fn=create_brochure,
        inputs=[company_input, url_input],
        outputs=output,
    )

if __name__ == "__main__":
    demo.launch()