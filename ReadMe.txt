Structure du projet

sri_project/
├── manage.py           # Script de gestion Django
├── .env                # Variables d'environnement (API keys)
├── requirements.txt    # Dépendances Python
├── db.sqlite3          # Base de données SQLite
├── sri_project/        # Configuration Django principale
│ ├── __init__.py
│ ├── settings.py       # Configuration du projet
│ ├── urls.py           # Routage principal
│ ├── asgi.py
│ └── wsgi.py
├── agent_service/      # Application Django pour l'agent
│ ├── __init__.py
│ ├── admin.py
│ ├── apps.py
│ ├── models.py
│ ├── tests.py
│ ├── groq_agent.py     # Logique de l'agent LangChain
│ ├── views.py          # Vues Django (API endpoints)
│ └── urls.py           # Routage de l'application
└── venv/               # Environnement virtuel Python