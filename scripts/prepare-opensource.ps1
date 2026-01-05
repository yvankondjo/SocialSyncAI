# Script PowerShell pour préparer le dossier Open Source
$sourceDir = Get-Location
$destDir = "$($sourceDir.Path)\..\SocialsyncAI"

Write-Host "Préparation du dossier Open Source vers $destDir..." -ForegroundColor Cyan

# Créer le dossier de destination s'il n'existe pas
if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir | Out-Null
    Write-Host "Dossier créé." -ForegroundColor Green
}

# Liste des dossiers à copier avec Robocopy (plus robuste pour les exclusions)
$foldersToCopy = @("backend", "frontend", "migrations", "scripts", "supabase", "tasks")

foreach ($folder in $foldersToCopy) {
    $src = Join-Path $sourceDir $folder
    $dst = Join-Path $destDir $folder
    
    if (Test-Path $src) {
        Write-Host "Copie de $folder (sans node_modules/venv)..."
        # Robocopy arguments:
        # /E : Recurse including empty dirs
        # /XD : Exclude Directories
        # /XF : Exclude Files
        # /NFL /NDL : No File/Dir List (less noise)
        # /NJH /NJS : No Job Header/Summary (less noise)
        robocopy $src $dst /E /XD node_modules __pycache__ .git .next .venv .vercel build dist /XF *.pyc *.pyo .DS_Store /NFL /NDL /NJH /NJS
        if ($LASTEXITCODE -ge 8) {
            Write-Host "⚠️ Erreur Robocopy pour $folder (Code: $LASTEXITCODE)" -ForegroundColor Red
        }
    }
}

# Copie des fichiers à la racine
$filesToCopy = @(
    "architecture-diagrams.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".gitignore",
    ".env.example",
    "docker-compose.yml"
)

foreach ($file in $filesToCopy) {
    $src = Join-Path $sourceDir $file
    $dst = Join-Path $destDir $file
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
    }
}

# Renommer README_OPENSOURCE.md en README.md
$readmeSource = Join-Path $sourceDir "README_OPENSOURCE.md"
$readmeDest = Join-Path $destDir "README.md"
if (Test-Path $readmeSource) {
    Copy-Item -Path $readmeSource -Destination $readmeDest -Force
    Write-Host "README_OPENSOURCE.md copié en tant que README.md" -ForegroundColor Green
}

# Nettoyage spécifique dans le dossier de destination
$sensitiveFiles = @(
    "backend/cloud-run-env.yaml",
    "backend/cloud-run-env.txt",
    "backend/scripts/setup-github-secrets.ps1",
    "socialsynv-*.json",
    "*.tf",
    "*.tfvars",
    "*.env"
)

foreach ($pattern in $sensitiveFiles) {
    $files = Get-ChildItem -Path $destDir -Include $pattern -Recurse -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        Remove-Item $file.FullName -Force
        Write-Host "Supprimé (sensible): $($file.FullName)" -ForegroundColor Red
    }
}

# Supprimer le dossier terraform s'il a été copié
$terraformDir = Join-Path $destDir "infrastructure\compute-engine\terraform"
if (Test-Path $terraformDir) {
    Remove-Item -Path $terraformDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Dossier Terraform supprimé du repo open source." -ForegroundColor Red
}

Write-Host "✅ Préparation terminée ! Vous pouvez aller dans $destDir" -ForegroundColor Green
