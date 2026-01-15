# agent_service/views.py

from django.shortcuts import render, redirect
 
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 

# Importation des sérialiseurs 
from .serializers import ProfileInputSerializer, RecommendationOutputSerializer

# Importation de la fonction de l'Agent (qui utilise Groq)
from .groq_agent import recommend_product  

class AgentAnalyzeAPIView(APIView): 
    """ 
    Endpoint API pour soumettre un profil client et recevoir une  recommandation. 
    Intègre la logique Human-in-the-Loop (HITL) basée sur la confiance.  """ 
    
    def post(self, request, *args, **kwargs): 
        # 1. Validation des données d'entrée 
        input_serializer = ProfileInputSerializer(data=request.data)  
        if not input_serializer.is_valid(): 
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
        data = input_serializer.validated_data 
  
        # 2. Appel de l'Agent IA (maintenant l'Agent Groq)  
        try: 
            pydantic_recommendation = recommend_product(  age=data['age'], 
                sector=data['sector'], 
                need=data['need_description'] 
            ) 
            # --- LOGIQUE DE L'HUMAIN DANS LA BOUCLE (HITL) ---  
            CONFIDENCE_THRESHOLD = 0.75 
            
            # Seuil : Si < 0.75, le processus  nécessite une validation humaine. 
            if pydantic_recommendation.score_confiance <  CONFIDENCE_THRESHOLD: 
            # L'IA manque de confiance : nécessite l'intervention  humaine 
                hitl_status = "À_VALIDER_MANUEL" 
                http_status = status.HTTP_202_ACCEPTED # 202: Processus  accepté, en attente 
            else: 
                # L'IA est suffisamment confiante : le processus est  automatisé 
                hitl_status = "VALIDÉ_AUTO" 
                http_status = status.HTTP_200_OK # 200: Succès immédiat 

            # 3. Préparation de la réponse structurée 
            response_data = pydantic_recommendation.model_dump()  
            # Ajout du statut HITL à la réponse JSON (clé pour le moteur  BPM) 
            response_data['hitl_status'] = hitl_status  
    
            # Sérialisation finale 
            output_serializer =  RecommendationOutputSerializer(data=response_data) 
            output_serializer.is_valid(raise_exception=True)   
            return Response(output_serializer.data, status=http_status)   
        except Exception as e: 
            # Gestion des erreurs de la couche Django/API  
            return Response({"error": "Erreur interne critique du service d'Agent.",  "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# ----------------------------------------------------------------- 
# # NOUVELLE VUE : Interface utilisateur pour l'Agent 
# ----------------------------------------------------------------- 

def recommendation_form(request): 
    """ 
        Gère l'affichage du formulaire et le traitement des données POST.  
    """ 
  
    # 1. Traitement des données POST (Soumission du formulaire)  
    if request.method == 'POST': 
        # NOTE : Les données POST sont des chaînes (str), pas des JSON ou  des objets Python. 
    
        # Récupération des données du formulaire POST 
        try: 
            profile_data = { 
                "name": request.POST.get('name', 'Client Anonyme'),  "age": int(request.POST.get('age', 0)), 
                # Conversion en int  
                "sector": request.POST.get('sector', ''),  "need_description": request.POST.get('need_description',  '') 
            } 
        except ValueError: 
            # Gérer le cas où l'âge n'est pas un nombre 
            context = {'error': "L'âge doit être un nombre valide."}  
            return render(request, 'agent_service/form.html', context) 
    
        # 2. Appel de l'Agent Groq (la fonction Python) 
        recommendation = recommend_product( 
            age=profile_data['age'], 
            sector=profile_data['sector'], 
            need=profile_data['need_description'] 
        )
    
        # 3. Logique HITL et préparation du résultat (réplique la logique  de l'API) 
        CONFIDENCE_THRESHOLD = 0.75 
    
        # Le résultat est un dictionnaire pour le template  
        result = recommendation.model_dump() 
    
        if result['score_confiance'] < CONFIDENCE_THRESHOLD:  
            result['hitl_status'] = "À VALIDER MANUELLEMENT"  
        else: 
            result['hitl_status'] = "VALIDÉ AUTOMATIQUEMENT" 
        
        # Ajout du nom du client pour l'affichage 
        result['client_name'] = profile_data['name'] 
    
        # 4. Affichage du résultat 
        return render(request, 'agent_service/result.html', {'result':  result}) 
        
    # 5. Affichage du formulaire (méthode GET) 
    return render(request, 'agent_service/form.html') 
