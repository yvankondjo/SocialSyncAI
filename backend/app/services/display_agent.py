import sys
import os
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

# Importer les modules nécessaires
from app.services.rag_agent import create_rag_agent
from app.deps.system_prompt import SYSTEM_PROMPT

# Créer l'agent
print('Création de l\'agent RAG...')
agent = create_rag_agent(
    user_id="test_user_id",
    conversation_id="test_conversation_id",
    system_prompt=SYSTEM_PROMPT,
    test_mode=True
)

# Accéder au graphique
print('Accès au graphique...')
graph = agent.graph.get_graph()

# Obtenir le code Mermaid
print('Génération du code Mermaid...')
try:
    mermaid_code = graph.draw_mermaid()
    print('Code Mermaid généré avec succès!')
    print('Longueur du code:', len(mermaid_code), 'caractères')
    
    # Sauvegarder le code Mermaid dans un fichier
    with open('/workspace/rag_agent_graph.mmd', 'w', encoding='utf-8') as f:
        f.write(mermaid_code)
    print('Code Mermaid sauvegardé dans /workspace/rag_agent_graph.mmd')
    
    # Afficher les premières lignes du code
    print('\nPremières lignes du code Mermaid:')
    print('=' * 50)
    lines = mermaid_code.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f'{i+1:2d}: {line}')
    if len(lines) > 20:
        print(f'... et {len(lines) - 20} lignes supplémentaires')
    
except Exception as e:
    print(f'Erreur lors de la génération du code Mermaid: {e}')
    import traceback
    traceback.print_exc()