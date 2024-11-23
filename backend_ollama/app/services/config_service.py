# app/services/config_service.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, PromptTemplate, ModelConfig, ExperimentResult
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def get_prompt_template(self, component_type: str) -> Optional[str]:
        session = self.Session()
        try:
            template = session.query(PromptTemplate)\
                .filter_by(component_type=component_type, is_active=True)\
                .order_by(PromptTemplate.version.desc())\
                .first()
            return template.template_content if template else None
        finally:
            session.close()
            
    def get_model_config(self, component_type: str, experiment_group: Optional[str] = None) -> Optional[Dict]:
        session = self.Session()
        try:
            query = session.query(ModelConfig)\
                .filter_by(component_type=component_type, is_active=True)
            
            if experiment_group:
                query = query.filter_by(experiment_group=experiment_group)
                
            config = query.first()
            if config:
                return {
                    "provider": config.model_provider,
                    "name": config.model_name,
                    "parameters": config.parameters or {},
                    "system_prompt": config.system_prompt
                }
            return None
        finally:
            session.close()

    def get_experiment_groups(self) -> List[str]:
        session = self.Session()
        try:
            groups = session.query(ModelConfig.experiment_group)\
                .distinct()\
                .filter(ModelConfig.experiment_group.isnot(None))\
                .all()
            return [g[0] for g in groups if g[0]]
        finally:
            session.close()

    def save_experiment_result(self, question: str, answer: str, model_config_id: int, score: float, feedback: Optional[str] = None):
        session = self.Session()
        try:
            result = ExperimentResult(
                question=question,
                answer=answer,
                model_config_id=model_config_id,
                score=score,
                feedback=feedback
            )
            session.add(result)
            session.commit()
        finally:
            session.close()
            
    def initialize_default_configs(self):
        session = self.Session()
        try:
            # Default prompt templates
            default_prompts = [
                {
                    "name": "Multi Query Template",
                    "component_type": "multi_query",
                    "template_content": """Vous êtes un assistant modèle de langage IA.
Votre tâche est de générer cinq versions différentes de la question posée par l'utilisateur
afin de récupérer des documents pertinents à partir d'une base de données vectorielle dans le domaine des **aides sociales en Belgique**.
En générant plusieurs perspectives de la question de l'utilisateur avec plus de recul,
votre objectif est d'aider l'utilisateur à surmonter certaines des limites de la recherche de similarité basée sur la distance.
Fournissez ces questions alternatives, séparées par des sauts de ligne. Ne rends que les questions sans texte supplémentaire.
Question originale : {question}""",
                    "version": 1
                },
                {
                    "name": "Verifier Template",
                    "component_type": "verifier",
                    "template_content": """Étant donné la question et le document suivants, déterminez si le document est un peu ou beaucoup lié à la question.
Répondez "Oui" s'il est lié de près ou de loin, ou <non> s'il ne l'est pas. Ceci est dans le contexte des aides sociales en Belgique.
Réfléchis avant de prendre la décision.

Question : {question}

Document : {document}

Le document est-il lié de près ou de loin par rapport à la question ? Réfléchis en interne en plusieurs étapes concises, et ensuite répond par <oui> ou <non>. Si tu n'es pas sûr, répond <oui>.""",
                    "version": 1
                },
                {
                    "name": "Final Answer Template",
                    "component_type": "final_answer",
                    "template_content": """Tu es une IA qui a pour objectif d'aider des personnes à trouver s'ils peuvent toucher des aides sociales.
Réponds aux questions selon le contexte et donne des **explications concises**.
Si tu n'as pas de réponse, ou bien qu'il n'y a rien dans le contexte dis-le !
Si tu as besoin que l'auteur reformule la question, aide-le en proposant plusieurs choix, mais ne réponds pas qu'avec les liens, donne des explications dans ta réponse.
Si le contexte te procure un lien utile, écris-le dans ta réponse au **format Markdown**.
Répond avec des liens utiles au sein de ta réponse, au niveau de l'endroit qui est utile.
**Écris ta réponse dans le format Markdown**.
Réponds à la question uniquement en te basant sur le contexte suivant :
{context}

Question : {question}""",
                    "version": 1
                },
                {
                    "name": "Multiple Choice Template",
                    "component_type": "multiple_choice",
                    "template_content": """Tu es un assistant qui génère des questions à choix multiples sous forme de JSON pour obtenir des informations précises et personnelles sur l'utilisateur.
Les questions doivent porter sur les **caractéristiques personnelles, habitudes, préférences, besoins** ou **situations spécifiques** de l'utilisateur, et être basées sur le contexte fourni.
Chaque question doit être directement liée à l'utilisateur, concise, et proposer 3 à 4 options de réponse pertinentes. **La dernière option doit toujours être "N/A"**.

Documents : {context}

Question initiale : {question}""",
                    "version": 1
                }
            ]

            # Default model configurations with system prompts
            default_models = [
                {
                    "name": "Groq Multi Query",
                    "model_provider": "groq",
                    "model_name": "llama-3.2-90b-text-preview",
                    "component_type": "multi_query",
                    "system_prompt": """Tu es un assistant expert en aide sociale belge. Ta mission est de reformuler les questions des utilisateurs
pour mieux comprendre leurs besoins et trouver les informations pertinentes dans notre base de données.""",
                    "parameters": {"temperature": 0.9},
                    "experiment_group": "baseline"
                },
                {
                    "name": "Groq Verifier",
                    "model_provider": "groq",
                    "model_name": "llama-3.2-90b-text-preview",
                    "component_type": "verifier",
                    "system_prompt": """Tu es un expert en vérification de pertinence documentaire. Tu dois évaluer si les documents
sont pertinents pour répondre aux questions sur les aides sociales en Belgique.""",
                    "parameters": {"temperature": 0.1},
                    "experiment_group": "baseline"
                },
                {
                    "name": "Groq Final",
                    "model_provider": "groq",
                    "model_name": "llama-3.2-90b-text-preview",
                    "component_type": "final_answer",
                    "system_prompt": """Tu es un assistant spécialisé dans les aides sociales belges. Ta mission est d'aider les utilisateurs
à comprendre leurs droits et les démarches à suivre. Sois précis, concis et bienveillant dans tes réponses.""",
                    "parameters": {"temperature": 0.1},
                    "experiment_group": "baseline"
                },
                {
                    "name": "Groq Multiple Choice",
                    "model_provider": "groq",
                    "model_name": "llama-3.1-70b-versatile",
                    "component_type": "multiple_choice",
                    "system_prompt": """Tu es un expert en création de questionnaires. Ta mission est de générer des questions pertinentes
pour mieux comprendre la situation des utilisateurs et leurs besoins en matière d'aide sociale en Belgique.""",
                    "parameters": {"temperature": 0.7},
                    "experiment_group": "baseline"
                }
            ]
            
            # Add default prompts if they don't exist
            for prompt_data in default_prompts:
                existing_prompt = session.query(PromptTemplate)\
                    .filter_by(component_type=prompt_data["component_type"])\
                    .first()
                if not existing_prompt:
                    prompt = PromptTemplate(**prompt_data)
                    session.add(prompt)
            
            # Add default models if they don't exist
            for model_data in default_models:
                existing_model = session.query(ModelConfig)\
                    .filter_by(
                        component_type=model_data["component_type"],
                        experiment_group=model_data["experiment_group"]
                    )\
                    .first()
                if not existing_model:
                    model = ModelConfig(**model_data)
                    session.add(model)
            
            session.commit()
            logger.info("Default configurations initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing default configs: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()