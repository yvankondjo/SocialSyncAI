import sys
import os

# Ajouter le répertoire parent au path pour pouvoir importer app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db

def delete_file_in_bucket(file_name: str):
    db = get_db()
    result = db.storage.from_("message").remove(file_name)
    print(f"Fichier supprimé: {file_name}")
    print(f"Résultat: {result}")
    return result

if __name__ == "__main__":
    delete_file_in_bucket("277909d7-fb0a-42a7-a516-a98eacdfca35/wamid.HBgLMzM3NjU1NDAwMDMVAgASGBQzRjE5QTc2QkM3QjNFNEFGQkRBOQA=.jpg")
