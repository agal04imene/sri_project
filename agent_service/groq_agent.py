# agent_service/groq_agent.py

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# --- BLOC DE CHARGEMENT et VÉRIFICATION DE LA CLÉ ---
load_dotenv()
# Récupération de la clé GROQ
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("La clé GROQ_API_KEY n'est pas configurée dans l'environnement.")
# --- FIN BLOC DE CHARGEMENT et VÉRIFICATION DE LA CLÉ ---

# 1. DÉFINITION DU SCHÉMA DE SORTIE AVEC PYDANTIC
class RecommendationSchema(BaseModel):
 """Schéma de sortie attendu de l'Agent."""
 product_id: str = Field(description="L'identifiant unique du produit/service recommandé (ex: S-2024-PRO).")
 justification_courte: str = Field(description="Explication concise (max 30 mots) du pourquoi ce produit est idéal pour le client.")
 score_confiance: float = Field(description="Un score de confiance entre 0.0 et 1.0 sur la pertinence de la recommandation.")

# --- FONCTION DE SIMULATION (Utilisée par défaut) ---
def recommend_product_SIMULATED(age: int, sector: str, need: str) -> RecommendationSchema:
    """Retourne un résultat structuré sans appeler le LLM."""
    if "finance" in sector.lower() or "analyse" in need.lower():
        product_id = "S-2024-PRO"
    else:
        product_id = "B-2024-ESS"
    return RecommendationSchema(
        product_id=product_id,
        justification_courte="Recommandation simulée. Solution basiqueadaptée aux besoins simples.",
        score_confiance=0.99
    )
# --- FIN FONCTION DE SIMULATION ---

# 2. CONFIGURATION DE L'AGENT ET DU PARSER
parser = PydanticOutputParser(pydantic_object=RecommendationSchema)
# Initialisation du LLM Groq
# Nous utilisons Llama-3.3-70b qui est excellent et gratuit sur Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.1 # Température basse pour assurer un bon formatage JSON
)

def generate_recommendation_chain():
    """Crée et retourne la chaîne LangChain pour la recommandation."""

    # Instructions pour l'Agent
    template = """
    Tu es un Expert en Recommandation de Produits pour des clients B2B.
    Ton rôle est d'analyser le profil client fourni et de recommander un seul produit/service.
    
    RÈGLES DE CONFIANCE (CRITIQUE pour le score_confiance) :
    1. CONFIANCE ÉLEVÉE (Score > 0.80) : Si le secteur et le besoin correspondent parfaitement à l'un des produits (ex: "analyse de données" pour S-2024-PRO).
    2. CONFIANCE MOYENNE (Score entre 0.70 et 0.80) : Si le besoin est clair mais le secteur est générique (ex: "Autre").
    3. CONFIANCE BASSE (Score < 0.70) : **Ceci déclenchera la validation humaine (HITL).** Utilise un score bas dans les cas suivants :
        - Le besoin est **ambigu, flou ou incohérent** (ex: "juste quelque chose de sympa").
    - Le client a un **profil très jeune ou très vieux** (Âge < 5 ans ou > 60 ans), indiquant un cas atypique.
    - La recommandation semble être un compromis et **ne correspond pas idéalement** à l'un des produits.
    
    Tu dois absolument respecter le format de sortie JSON spécifié par les instructions de formatage.
    Ne rajoute aucun texte avant ou après le JSON.

    Profil Client :
        - Âge du client : {age}
        - Secteur d'activité : {sector}
        - Besoin exprimé : {need}
    
    Liste des Produits/Services disponibles (utilise ces IDs uniquement) :
        - S-2024-PRO (Solution Pro Data) : Idéale pour les besoins complexes en analyse de données.
        - B-2024-ESS (Basique Essentiel) : Pour les petites entreprises ayant des besoins simples en gestion.
        - C-2024-MIG (Migration Cloud) : Pour les clients cherchant à moderniser leur infrastructure.
        
        {format_instructions}
    """

    prompt = ChatPromptTemplate.from_template(
        template=template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Chaîne : Prompt -> LLM -> Parser
    chain = prompt | llm | parser
    return chain

# 3. FONCTION PRINCIPALE POUR L'APPEL
def recommend_product(age: int, sector: str, need: str) -> RecommendationSchema:
    """
    Appelle la chaîne de recommandation et retourne l'objet Pydantic.
    """

 # --- LOGIQUE RÉELLE ---
    try:
        chain = generate_recommendation_chain()
        result = chain.invoke({
            "age": age,
            "sector": sector,
            "need": need
        })
        return result
    except Exception as e:
        print(f"Erreur lors de l'appel LLM: {e}")
        # En cas d'échec de l'API
        return RecommendationSchema(
            product_id="API_FAIL",
            justification_courte=f"Erreur API Groq: {str(e)}",
        score_confiance=0.0
    )
        
if __name__ == '__main__':
    # Exemple de test
    test_age = 45
    test_sector = "Finance"
    test_need = "J'ai besoin d'une solution pour analyser rapidement les gros volumes de données de marché."

    print(f"Analyse du profil : {test_sector}, {test_age}, Besoin:'{test_need[:50]}...'")

    # Appel de l'Agent
    recommendation = recommend_product(test_age, test_sector, test_need)

    print("\n--- RÉSULTAT DE L'AGENT (GROQ) ---")
    print(f"Produit Recommandé : {recommendation.product_id}")
    print(f"Justification : {recommendation.justification_courte}")
    print(f"Confiance : {recommendation.score_confiance:.2f}")

    # Vérification du type (doit être Pydantic)
    print(f"Type de l'objet retourné : {type(recommendation)}")

    print("\n--- TEST TERMINÉ ---")