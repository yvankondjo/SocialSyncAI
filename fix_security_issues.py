#!/usr/bin/env python3
"""
Script pour corriger les problèmes de sécurité PostgreSQL identifiés par le linter Supabase.
Corrige les fonctions avec search_path mutable et affiche les résultats.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def load_linter_results(file_path: str) -> List[Dict[str, Any]]:
    """Charge les résultats du linter depuis un fichier JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier {file_path} non trouvé")
        return []
    except json.JSONDecodeError as e:
        print(f"Erreur de parsing JSON: {e}")
        return []

def filter_search_path_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtre les problèmes liés au search_path mutable."""
    return [
        issue for issue in issues 
        if issue.get('name') == 'function_search_path_mutable'
    ]

def get_unique_functions(issues: List[Dict[str, Any]]) -> List[str]:
    """Extrait la liste unique des fonctions à corriger."""
    functions = set()
    for issue in issues:
        metadata = issue.get('metadata', {})
        function_name = metadata.get('name')
        if function_name:
            functions.add(function_name)
    return sorted(list(functions))

def execute_migration(migration_file: str) -> bool:
    """Exécute la migration SQL."""
    try:
        # Vérifier si le fichier existe
        if not os.path.exists(migration_file):
            print(f"Fichier de migration {migration_file} non trouvé")
            return False
        
        # Exécuter la migration (suppose que psql est disponible)
        cmd = ['psql', '-f', migration_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration exécutée avec succès")
            print("Sortie:", result.stdout)
            return True
        else:
            print("❌ Erreur lors de l'exécution de la migration")
            print("Erreur:", result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ psql non trouvé. Assurez-vous que PostgreSQL est installé et dans le PATH")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def generate_manual_fix_script(functions: List[str]) -> str:
    """Génère un script SQL manuel pour corriger les fonctions."""
    script = "-- Script manuel pour corriger le search_path des fonctions\n\n"
    
    for func in functions:
        script += f"-- Corriger {func}\n"
        script += f"ALTER FUNCTION public.{func} SET search_path = public;\n\n"
    
    return script

def main():
    """Fonction principale."""
    print("🔧 Script de correction des problèmes de sécurité PostgreSQL")
    print("=" * 60)
    
    # Charger les résultats du linter
    linter_file = "linter_results.json"
    if len(sys.argv) > 1:
        linter_file = sys.argv[1]
    
    print(f"📁 Chargement des résultats du linter depuis: {linter_file}")
    issues = load_linter_results(linter_file)
    
    if not issues:
        print("❌ Aucun résultat de linter trouvé")
        return
    
    # Filtrer les problèmes de search_path
    search_path_issues = filter_search_path_issues(issues)
    print(f"🔍 Trouvé {len(search_path_issues)} problèmes de search_path mutable")
    
    if not search_path_issues:
        print("✅ Aucun problème de search_path à corriger")
        return
    
    # Extraire les fonctions uniques
    functions = get_unique_functions(search_path_issues)
    print(f"📋 Fonctions à corriger: {', '.join(functions)}")
    
    # Chemin vers la migration
    migration_file = "backend/migrations/migration_022_fix_search_path_security.sql"
    
    print(f"\n🚀 Exécution de la migration: {migration_file}")
    success = execute_migration(migration_file)
    
    if not success:
        print("\n📝 Script manuel de correction:")
        print("-" * 40)
        manual_script = generate_manual_fix_script(functions)
        print(manual_script)
        
        # Sauvegarder le script manuel
        with open("manual_fix_search_path.sql", "w", encoding="utf-8") as f:
            f.write(manual_script)
        print("💾 Script manuel sauvegardé dans: manual_fix_search_path.sql")
    
    print("\n✅ Correction terminée!")

if __name__ == "__main__":
    main()
