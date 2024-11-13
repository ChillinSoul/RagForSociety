import getpass
import json
import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import AIMessage, HumanMessage

# Load environment variables from .env file
load_dotenv("C:/Users/basil/source/repos/RagForSociety/backend_ollama/.env")

# Ensure the API key is loaded properly
langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
if not langchain_api_key:
    raise ValueError("LANGCHAIN_API_KEY is not set. Please check your .env file.")

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = langchain_api_key

# Prompt for Groq API key if not already set in the environment
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

# Initialize the LLM model
llm = ChatGroq(model="llama-3.2-90b-text-preview")

# Create a prompt template for summarizing content
prompt_template = PromptTemplate(
    input_variables=["content"],
    template="""Écris un résumé pour ce texte dans le contexte de fournir le plus d'informations possible sur un certain sujet à un utilisateur.
      Le résumé doit contenir toutes les informations du document mais d'une façon structurée et plus courte **Écris seulement le résumé, pas de texte en plus (par exemple: N'écris pas de \"Voici un résumé structuré du texte:\")**
      Il faut impérativement s'intégrer **TOUS** les liens vers les sites gouvernementaux et autre liens permettant d'aider l'utilisateur sous **format markdown**.
      Ces lien doivent **IMPÉRATIVEMENT** être intégrés à l'intérieur du résumé, au niveau de la phrase qui leur correspond, et surtout **PAS TOUS Á LA FIN**.
      Voici le texte à résumer:
        {content}"""
)

# Initialize a RunnableSequence (replacing the LLMChain)
summarize_chain = prompt_template | llm | StrOutputParser()

# Define the first message and the AI response
def create_conversation_history():
    return [
        HumanMessage(content="""Écris un résumé pour ce texte dans le contexte de fournir le plus d'informations possible sur un certain sujet à un utilisateur.
                        Le résumé doit contenir toutes les informations du document mais d'une façon structurée et plus courte **Écris seulement le résumé, pas de texte en plus (par exemple: N'écris pas de "Voici un résumé structuré du texte:")**
                        Il faut impérativement s'intégrer **TOUS** les liens vers les sites gouvernementaux et autre liens permettant d'aider l'utilisateur sous **format markdown**.
                        Ces lien doivent **IMPÉRATIVEMENT** être intégrés à l'intérieur du résumé, au niveau de la phrase qui leur correspond, et surtout **PAS TOUS Á LA FIN**.
                        Voici le texte à résumer:
                         [Accueil](https://aide-sociale.be "Accueil")\n»\n[Famille](https://aide-sociale.be/famille/ "Famille")\n»\n[Familles à faibles revenus](https://aide-sociale.be/famille/familles-faibles-revenus/ "Familles à faibles revenus")\n \n# L’aide alimentaire en Belgique : Un soutien essentiel pour les personnes en difficulté\n \nPar Salma L. Mise à jour le 1 octobre 2024Temps de lecture estimé : 7 minutes\nEn Belgique, **l’aide alimentaire représente une bouée de sauvetage** pour de nombreuses **personnes qui se trouvent en situation de précarité**. Ce soutien se manifeste sous diverses formes, allant des **colis alimentaires** aux **épiceries sociales** et aux **restaurants sociaux**. \nDans ce qui suit, nous vous présenterons **les différentes formes d’aide alimentaire** disponibles en Belgique, **comment elles fonctionnent**, **qui y a droit**, et **comment y accéder**."""),
        AIMessage(content="""**L'aide alimentaire en Belgique : Un soutien essentiel pour les personnes en difficulté**

L'aide alimentaire en Belgique est un dispositif essentiel proposant plusieurs formes de soutien aux personnes en difficulté financière. Pour une assistance immédiate : appelez le 1718 en Wallonie ou le 0800 35 243 à Bruxelles. Plus d'informations sur [aide-sociale.be](https://aide-sociale.be/).

**Qui a droit à l'aide alimentaire ?**

L'accès est réservé aux personnes sous le seuil de pauvreté :
- Personne isolée : revenu inférieur à 1.287 euros/mois
- Ménage de quatre personnes : revenu inférieur à 2.703 euros/mois

Bénéficiaires principaux :
- [Familles monoparentales](https://aide-sociale.be/aides-familles-monoparentales/)
- [Travailleurs à faible revenu](https://aide-sociale.be/famille/familles-faibles-revenus/)
- [Personnes sans papiers](https://aide-sociale.be/aides-personnes-sans-papiers/) (avec accompagnement spécialisé)
- Seniors sans revenus
- Étudiants en difficulté

**Types d'aide alimentaire disponibles**

1. **Colis alimentaires** :
   - Plus de 460 services de distribution en Wallonie
   - Contiennent des produits non périssables et frais
   - [Répertoire complet des services](https://www.fdss.be/fr/concertation-aide-alimentaire/repertoire-de-l-aide-alimentaire/)

2. **Épiceries sociales** :
   - Réduction moyenne de 10% sur les prix du marché
   - Environ 100 épiceries en Wallonie : [Liste complète](https://www.fdss.be/wp-content/uploads/R%C3%A9pertoire_aide_alimentaire_wallonie.pdf)
   - 15 épiceries à Bruxelles : [Répertoire](https://social.brussels/category/454)
   - Accompagnement personnalisé pour la gestion du budget

3. **Restaurants sociaux** :
   - 60 établissements en région bruxelloise : [Liste des restaurants](https://social.brussels/category/43)
   - [Restos du Cœur](https://restosducoeur.be/fr/) : [Localisez le plus proche](https://restosducoeur.be/fr/nos-restos)
   - Repas chauds à prix réduits avec accompagnement social

4. **Frigos solidaires** :
   - 15 frigos à Bruxelles
   - Initiative anti-gaspillage via [Too Good To Go](https://www.toogoodtogo.com/fr-be)

**Documents requis et procédure d'inscription**

Documents nécessaires :
 - Preuves de revenus : fiches de paie, [allocations de chômage](https://aide-sociale.be/chomage/), [allocations handicap](https://aide-sociale.be/reconnaissance-handicap/)
 - Factures récentes : énergie, télécommunications
 - Logement : bail, quittances, [crédit hypothécaire social](https://aide-sociale.be/credit-hypothecaire-social/)
 - Situation spécifique : [allocation d'intégration](https://aide-sociale.be/allocation-integration/) (dispensée de preuves)

**Organisations et contacts**

1. **[Banques alimentaires](https://www.foodbanks.be/fr/index.html)** :
   - 9 banques en Belgique
   - Coordination de la collecte et distribution

2. **[CPAS](https://www.belgium.be/fr/famille/aide_sociale/cpas)** :
   - [CPAS Bruxelles](https://cpasbxl.brussels/)
   - Aide alimentaire et accompagnement social

3. **Associations caritatives** :
   - [Croix-Rouge](https://www.croix-rouge.be/)
   - [Restos du Cœur](https://restosducoeur.be/fr/)

**Informations complémentaires**

 - Durée de l'aide : adaptée à chaque situation
 - Coût : gratuit ou participation symbolique selon les services
 - Cumul possible des aides selon les besoins
 - [Rente alimentaire](https://aide-sociale.be/rente-alimentaire/) disponible en cas de séparation
 - Accompagnement social personnalisé disponible dans la plupart des services""")
    ]

def process_and_summarize(data, output_file):
    total_items = len(data)

    for i, (url, item) in enumerate(data.items()):
        # Check if the item has already been summarized
        if item.get("summarized", False):
            continue

        print(f"Processing item {i+1}/{total_items}")

        # Get the content to be summarized
        string = item.get("converted_markdown", "")
        if not string:
            continue  # Skip if no content available

        # Add conversation history
        conversation_history = create_conversation_history()
        
        # Add the current content as a new user message in the history
        conversation_history.append(HumanMessage(content=string))

        # Summarize the content (invoke the summarization chain)
        summary_result = summarize_chain.invoke({"content": string})

        # Extract the summarized content
        summary = summary_result
        print(f"Summarized: {summary}")

        # Add the summarized content back under the correct URL
        item["summary"] = summary
        item["summarized"] = True  # Mark the item as summarized

        # Save after processing each item
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    return data

def load_data(output_file, input_file):
    # If summarized data file exists, load it, otherwise load the original data
    if os.path.exists(output_file):
        print(f"Resuming from {output_file}...")
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print(f"Starting fresh from {input_file}...")
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def main():
    input_file = "new_output.json"  # Update this to your new input file
    output_file = "summarized_data_new.json"

    # Load data (resume if output file exists)
    data = load_data(output_file, input_file)

    # Process and summarize the JSON content
    summarized_data = process_and_summarize(data, output_file)

if __name__ == "__main__":
    main()
