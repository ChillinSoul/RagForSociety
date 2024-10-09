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
    template="Écris un résumé pour ce texte dans le contexte de fournir le plus d'informations possible sur un certain sujet à un utilisateur. Le résumé doit contenir toutes les informations du document mais d'une façon structurée et plus courte **Écris seulement le résumé, pas de texte en plus (par exemple: N'écris pas de \"Voici un résumé structuré du texte:\")**: {content}"
)

# Initialize a RunnableSequence (replacing the LLMChain)
summarize_chain = prompt_template | llm | StrOutputParser()

# Define the first message and the AI response
def create_conversation_history():
    return [
        HumanMessage(content="""Écris un résumé pour ce texte dans le contexte de fournir le plus d'informations possible sur un certain sujet à un utilisateur. Le résumé doit contenir toutes les informations du document mais d'une façon structurée et plus courte **Écris seulement le résumé, pas de texte en plus (par exemple: N'écris pas de "Voici un résumé structuré du texte:")**: [Accueil](https://aide-sociale.be "Accueil")\n»\n[Famille](https://aide-sociale.be/famille/ "Famille")\n»\n[Familles à faibles revenus](https://aide-sociale.be/famille/familles-faibles-revenus/ "Familles à faibles revenus")\n \n# L’aide alimentaire en Belgique : Un soutien essentiel pour les personnes en difficulté\n \nPar Salma L. Mise à jour le 1 octobre 2024Temps de lecture estimé : 7 minutes\nEn Belgique, **l’aide alimentaire représente une bouée de sauvetage** pour de nombreuses **personnes qui se trouvent en situation de précarité**. Ce soutien se manifeste sous diverses formes, allant des **colis alimentaires** aux **épiceries sociales** et aux **restaurants sociaux**. \nDans ce qui suit, nous vous présenterons **les différentes formes d’aide alimentaire** disponibles en Belgique, **comment elles fonctionnent**, **qui y a droit**, et **comment y accéder**."""),
        AIMessage(content="""# Aide alimentaire en Belgique - Résumé structuré

## Définition et objectif
L'aide alimentaire est un soutien destiné aux personnes en situation de précarité ayant des difficultés à se nourrir pour des raisons économiques.

## Critères d'éligibilité
- Seuil de pauvreté : 
  - Personne isolée : < 1.287€/mois
  - Ménage de 4 personnes : < 2.703€/mois
- Profils typiques : familles monoparentales, travailleurs à faible revenu, sans-papiers, seniors sans revenus, étudiants en difficulté

## Types d'aide alimentaire
1. Colis alimentaires
   - Contenu : produits non périssables, produits frais
   - 460+ services de distribution en Wallonie

2. Épiceries sociales
   - Prix réduits (environ -10% du prix du marché)
   - ~100 épiceries en Wallonie
   - ~15 épiceries à Bruxelles

3. Restaurants sociaux
   - Repas chauds à bas prix
   - ~60 restaurants en région bruxelloise

4. Frigos solidaires
   - Partage de denrées proche péremption
   - ~15 frigos à Bruxelles

## Procédure d'accès
### Documents requis
- Fiches de paie
- Attestations de revenus
- Factures (énergie, télécommunications)
- Contrat de bail/preuves de logement
- Preuves de dettes

### Points de contact
- Wallonie : numéro vert 1718
- Bruxelles : 0800 35 243

## Organisations responsables
1. Banques alimentaires (9 en Belgique)
2. CPAS (Centres Publics d'Action Sociale)
3. Associations caritatives (Croix-Rouge, Restos du Cœur)
4. Initiatives citoyennes (Too Good To Go)

## Durée et conditions
- Durée variable selon situation
- Possibilité de combiner différentes formes d'aide
- Participation financière parfois demandée
- Accompagnement social disponible""")
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
