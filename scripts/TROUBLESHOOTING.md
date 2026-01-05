# Guide de dépannage - Commandes gcloud

## Problème: Erreur avec `gcloud compute scp`

### Erreur typique
```
/usr/bin/scp: unknown option -- -
ERROR: (gcloud.compute.scp) [/usr/bin/scp] exited with return code [1].
```

### Cause
Cette erreur se produit généralement quand :
1. Vous utilisez des backslashes (`\`) au lieu de backticks (`` ` ``) dans PowerShell
2. La commande est mal formatée avec des espaces ou caractères spéciaux
3. Les chemins de fichiers contiennent des espaces non échappés

### Solution

**Dans PowerShell, utilisez toujours des backticks (`` ` ``) pour continuer les lignes :**

```powershell
# ✅ CORRECT
gcloud compute scp --tunnel-through-iap `
    --zone=europe-west1-b `
    "chemin/vers/fichier" `
    worker-instance:/tmp/destination

# ❌ INCORRECT (backslashes)
gcloud compute scp --tunnel-through-iap \
    --zone=europe-west1-b \
    "chemin/vers/fichier" \
    worker-instance:/tmp/destination
```

**Ou utilisez une commande sur une seule ligne :**

```powershell
# ✅ CORRECT
gcloud compute scp --tunnel-through-iap --zone=europe-west1-b "fichier.txt" worker-instance:/tmp/

# ✅ CORRECT (avec variables)
$cmd = "gcloud compute scp --tunnel-through-iap --zone=$Zone `"$EnvFile`" `"$Instance:/tmp/.env`""
Invoke-Expression $cmd
```

### Commandes alternatives

Si vous continuez à avoir des problèmes, utilisez les scripts fournis :

```powershell
# Pour déployer le fichier .env
.\scripts\fix-workers-env.ps1 -Deploy

# Pour vérifier le statut
.\scripts\check-workers-status.ps1
```

### Vérification

Pour tester si gcloud fonctionne correctement :

```powershell
# Test simple
gcloud compute instances list --zone=europe-west1-b

# Test avec IAP
gcloud compute ssh worker-instance --zone=europe-west1-b --tunnel-through-iap --command="echo test"
```


