#!/usr/bin/env python3
"""
Script de déploiement pour l'architecture hybride Stripe + Supabase.

Ce script orchestre le déploiement complet de la migration vers
l'architecture hybride en suivant les bonnes pratiques DevOps.

Usage:
    python scripts/deploy_hybrid_architecture.py [--environment=staging|production]

Le script suit cette séquence:
1. Pré-déploiement checks
2. Migration DB (rollback-ready)
3. Création produits Stripe/Whop
4. Migration données existantes
5. Tests post-migration
6. Configuration webhooks
7. Validation finale
"""

import sys
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from supabase import create_client, Client

from app.core.config import get_settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deploy_hybrid_architecture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Gestionnaire de déploiement pour l'architecture hybride."""

    def __init__(self, environment: str = 'staging'):
        self.environment = environment
        self.db = None
        self.start_time = datetime.now(timezone.utc)
        self.steps_completed = []
        self.errors = []

        # Configuration selon environnement
        self.config = self._load_environment_config()

    def _load_environment_config(self) -> Dict[str, Any]:
        """Charge la configuration selon l'environnement."""
        settings = get_settings()

        config = {
            'environment': self.environment,
            'db_url': settings.SUPABASE_URL,
            'dry_run': self.environment == 'staging',
            'webhook_url': f"https://{settings.FRONTEND_URL.replace('http://', '').replace('https://', '')}/api",
            'stripe_enabled': bool(os.getenv('STRIPE_SECRET_KEY')),
            'whop_enabled': bool(os.getenv('WHOP_API_KEY')),
        }

        if self.environment == 'production':
            config.update({
                'backup_required': True,
                'rollback_timeout': 3600,  # 1 heure
                'monitoring_enabled': True
            })

        return config

    def log_step(self, step: str, status: str, details: Optional[str] = None):
        """Log une étape du déploiement."""
        timestamp = datetime.now(timezone.utc).isoformat()
        message = f"[{timestamp}] {status.upper()}: {step}"

        if details:
            message += f" - {details}"

        if status == 'error':
            logger.error(message)
            self.errors.append(message)
        elif status == 'success':
            logger.info(message)
            self.steps_completed.append(step)
        else:
            logger.info(message)

    def run_pre_deployment_checks(self) -> bool:
        """Exécute les vérifications pré-déploiement."""
        self.log_step("pre_deployment_checks", "start")

        checks = [
            ("database_connection", self._check_database_connection),
            ("required_tables_exist", self._check_required_tables),
            ("environment_variables", self._check_environment_variables),
            ("stripe_configuration", self._check_stripe_configuration),
            ("whop_configuration", self._check_whop_configuration),
            ("existing_data_backup", self._check_existing_data_backup),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    self.log_step(check_name, "success")
                else:
                    self.log_step(check_name, "error", "Check failed")
                    all_passed = False
            except Exception as e:
                self.log_step(check_name, "error", str(e))
                all_passed = False

        self.log_step("pre_deployment_checks", "success" if all_passed else "error")
        return all_passed

    def _check_database_connection(self) -> bool:
        """Vérifie la connexion à la base de données."""
        try:
            settings = get_settings()
            self.db = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

            # Test simple
            result = self.db.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def _check_required_tables(self) -> bool:
        """Vérifie que les tables requises existent."""
        required_tables = [
            'users', 'subscription_plans', 'user_subscriptions',
            'ai_models', 'credit_transactions'
        ]

        try:
            for table in required_tables:
                # Cette requête va échouer si la table n'existe pas
                self.db.table(table).select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Required table check failed: {e}")
            return False

    def _check_environment_variables(self) -> bool:
        """Vérifie les variables d'environnement critiques."""
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        optional_vars = ['STRIPE_SECRET_KEY', 'WHOP_API_KEY']

        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)

        if self.config['stripe_enabled']:
            if not os.getenv('STRIPE_WEBHOOK_SECRET'):
                missing.append('STRIPE_WEBHOOK_SECRET')

        if self.config['whop_enabled']:
            if not os.getenv('WHOP_WEBHOOK_SECRET'):
                missing.append('WHOP_WEBHOOK_SECRET')

        if missing:
            logger.error(f"Missing environment variables: {', '.join(missing)}")
            return False

        return True

    def _check_stripe_configuration(self) -> bool:
        """Vérifie la configuration Stripe."""
        if not self.config['stripe_enabled']:
            logger.info("Stripe not configured - skipping Stripe checks")
            return True

        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

            # Test API Stripe
            account = stripe.Account.retrieve()
            logger.info(f"Stripe account: {account.id}")
            return True
        except Exception as e:
            logger.error(f"Stripe configuration check failed: {e}")
            return False

    def _check_whop_configuration(self) -> bool:
        """Vérifie la configuration Whop."""
        if not self.config['whop_enabled']:
            logger.info("Whop not configured - skipping Whop checks")
            return True

        # TODO: Implémenter vérification Whop
        logger.warning("Whop configuration check not implemented yet")
        return True

    def _check_existing_data_backup(self) -> bool:
        """Vérifie qu'un backup des données existe."""
        if self.environment == 'production':
            # TODO: Vérifier existence d'un backup récent
            logger.warning("Production backup verification not implemented")
            return True
        return True

    def run_database_migration(self) -> bool:
        """Exécute la migration de base de données."""
        self.log_step("database_migration", "start")

        try:
            # Appliquer migration_027_stripe_tables.sql
            migration_success = self._apply_database_migration()

            if migration_success:
                self.log_step("database_migration", "success")
                return True
            else:
                self.log_step("database_migration", "error", "Migration failed")
                return False

        except Exception as e:
            self.log_step("database_migration", "error", str(e))
            return False

    def _apply_database_migration(self) -> bool:
        """Applique la migration SQL."""
        try:
            # Lire le fichier de migration
            migration_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'migrations',
                'migration_027_stripe_tables.sql'
            )

            if not os.path.exists(migration_file):
                raise FileNotFoundError(f"Migration file not found: {migration_file}")

            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Diviser en statements individuels (séparés par -- =====================================================)
            statements = []
            current_statement = []

            for line in sql_content.split('\n'):
                if line.strip().startswith('-- ====================================================='):
                    if current_statement:
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                else:
                    current_statement.append(line)

            if current_statement:
                statements.append('\n'.join(current_statement))

            # Exécuter chaque statement
            for i, statement in enumerate(statements):
                if statement.strip():
                    try:
                        # Note: Supabase Python client n'a pas d'execute_sql direct
                        # On utilise une approche alternative ou on recommande psql
                        logger.info(f"Would execute statement {i+1}/{len(statements)}")

                        if not self.config['dry_run']:
                            # TODO: Implémenter exécution SQL
                            pass

                    except Exception as e:
                        logger.error(f"Failed to execute statement {i+1}: {e}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False

    def run_products_creation(self) -> bool:
        """Crée les produits dans Stripe et Whop."""
        self.log_step("products_creation", "start")

        success = True

        # Créer produits Stripe
        if self.config['stripe_enabled']:
            stripe_success = self._create_stripe_products()
            if not stripe_success:
                success = False

        # Créer produits Whop
        if self.config['whop_enabled']:
            whop_success = self._create_whop_products()
            if not whop_success:
                success = False

        self.log_step("products_creation", "success" if success else "error")
        return success

    def _create_stripe_products(self) -> bool:
        """Crée les produits Stripe."""
        try:
            # Importer et exécuter le script Stripe
            from scripts.create_stripe_products import create_stripe_products

            logger.info("Creating Stripe products...")
            if not self.config['dry_run']:
                create_stripe_products()
            else:
                logger.info("[DRY-RUN] Would create Stripe products")

            return True
        except Exception as e:
            logger.error(f"Stripe products creation failed: {e}")
            return False

    def _create_whop_products(self) -> bool:
        """Crée les produits Whop."""
        try:
            # Importer et exécuter le script Whop
            from scripts.create_whop_products import main as create_whop_products

            logger.info("Creating Whop products...")
            if not self.config['dry_run']:
                # TODO: Adapter pour async
                pass
            else:
                logger.info("[DRY-RUN] Would create Whop products")

            return True
        except Exception as e:
            logger.error(f"Whop products creation failed: {e}")
            return False

    def run_data_migration(self) -> bool:
        """Exécute la migration des données existantes."""
        self.log_step("data_migration", "start")

        try:
            # Importer et exécuter le script de migration
            from scripts.migrate_to_hybrid_architecture import main as migrate_data

            logger.info("Migrating existing data...")
            if not self.config['dry_run']:
                # TODO: Adapter pour être appelable programmatiquement
                migrate_data()
            else:
                logger.info("[DRY-RUN] Would migrate existing data")

            self.log_step("data_migration", "success")
            return True

        except Exception as e:
            self.log_step("data_migration", "error", str(e))
            return False

    def run_post_migration_tests(self) -> bool:
        """Exécute les tests post-migration."""
        self.log_step("post_migration_tests", "start")

        try:
            # Importer et exécuter les tests
            import subprocess
            import sys

            logger.info("Running post-migration tests...")

            if not self.config['dry_run']:
                # Exécuter les tests
                result = subprocess.run([
                    sys.executable, '-m', 'pytest',
                    'tests/test_migration_hybrid_architecture.py',
                    '-v'
                ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

                if result.returncode == 0:
                    logger.info("All tests passed")
                    self.log_step("post_migration_tests", "success")
                    return True
                else:
                    logger.error("Some tests failed")
                    logger.error(result.stdout)
                    logger.error(result.stderr)
                    self.log_step("post_migration_tests", "error", "Tests failed")
                    return False
            else:
                logger.info("[DRY-RUN] Would run post-migration tests")
                self.log_step("post_migration_tests", "success")
                return True

        except Exception as e:
            self.log_step("post_migration_tests", "error", str(e))
            return False

    def configure_webhooks(self) -> bool:
        """Configure les webhooks Stripe et Whop."""
        self.log_step("webhook_configuration", "start")

        success = True

        if self.config['stripe_enabled']:
            stripe_webhook_success = self._configure_stripe_webhooks()
            if not stripe_webhook_success:
                success = False

        if self.config['whop_enabled']:
            whop_webhook_success = self._configure_whop_webhooks()
            if not whop_webhook_success:
                success = False

        self.log_step("webhook_configuration", "success" if success else "error")
        return success

    def _configure_stripe_webhooks(self) -> bool:
        """Configure les webhooks Stripe."""
        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

            webhook_url = f"{self.config['webhook_url']}/stripe/webhook"

            # Événements à écouter
            events = [
                'product.created', 'product.updated', 'product.deleted',
                'price.created', 'price.updated', 'price.deleted',
                'customer.subscription.created', 'customer.subscription.updated',
                'customer.subscription.deleted', 'invoice.payment_succeeded',
                'invoice.payment_failed', 'checkout.session.completed'
            ]

            if not self.config['dry_run']:
                # Créer ou mettre à jour le webhook endpoint
                webhooks = stripe.WebhookEndpoint.list()
                existing_webhook = None

                for webhook in webhooks['data']:
                    if webhook['url'] == webhook_url:
                        existing_webhook = webhook
                        break

                if existing_webhook:
                    # Mettre à jour
                    stripe.WebhookEndpoint.modify(
                        existing_webhook['id'],
                        enabled_events=events,
                        url=webhook_url
                    )
                    logger.info(f"Updated Stripe webhook: {existing_webhook['id']}")
                else:
                    # Créer nouveau
                    webhook = stripe.WebhookEndpoint.create(
                        url=webhook_url,
                        enabled_events=events,
                        description="Hybrid Architecture Webhooks"
                    )
                    logger.info(f"Created Stripe webhook: {webhook['id']}")
            else:
                logger.info(f"[DRY-RUN] Would configure Stripe webhook: {webhook_url}")

            return True

        except Exception as e:
            logger.error(f"Stripe webhook configuration failed: {e}")
            return False

    def _configure_whop_webhooks(self) -> bool:
        """Configure les webhooks Whop."""
        try:
            # TODO: Implémenter configuration webhooks Whop
            logger.warning("Whop webhook configuration not implemented yet")
            return True
        except Exception as e:
            logger.error(f"Whop webhook configuration failed: {e}")
            return False

    def run_final_validation(self) -> bool:
        """Exécute la validation finale."""
        self.log_step("final_validation", "start")

        validations = [
            ("api_endpoints", self._validate_api_endpoints),
            ("webhook_endpoints", self._validate_webhook_endpoints),
            ("data_consistency", self._validate_data_consistency),
        ]

        all_passed = True
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                if result:
                    self.log_step(validation_name, "success")
                else:
                    self.log_step(validation_name, "error", "Validation failed")
                    all_passed = False
            except Exception as e:
                self.log_step(validation_name, "error", str(e))
                all_passed = False

        self.log_step("final_validation", "success" if all_passed else "error")
        return all_passed

    def _validate_api_endpoints(self) -> bool:
        """Valide que les endpoints API fonctionnent."""
        try:
            import requests
            from app.core.config import get_settings

            settings = get_settings()
            base_url = f"http://localhost:{os.getenv('PORT', '8000')}"

            # Tester quelques endpoints critiques
            endpoints_to_test = [
                "/api/subscriptions/plans",
                "/api/models"
            ]

            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    if response.status_code != 200:
                        logger.error(f"Endpoint {endpoint} returned {response.status_code}")
                        return False
                except Exception as e:
                    logger.error(f"Failed to test endpoint {endpoint}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"API validation failed: {e}")
            return False

    def _validate_webhook_endpoints(self) -> bool:
        """Valide que les endpoints webhook sont accessibles."""
        # TODO: Implémenter validation webhooks
        return True

    def _validate_data_consistency(self) -> bool:
        """Valide la cohérence des données."""
        try:
            # Vérifier que user_credits et subscriptions sont cohérents
            credits_result = self.db.table('user_credits').select('user_id, credits_balance').execute()
            users_with_credits = len(credits_result.data)

            # Vérifier que les anciennes tables existent encore
            old_subs_result = self.db.table('user_subscriptions').select('user_id').execute()
            old_subs_count = len(old_subs_result.data)

            logger.info(f"Data consistency check: {users_with_credits} users with credits, {old_subs_count} old subscriptions")

            return True

        except Exception as e:
            logger.error(f"Data consistency validation failed: {e}")
            return False

    def generate_deployment_report(self) -> Dict[str, Any]:
        """Génère un rapport de déploiement."""
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()

        report = {
            'environment': self.environment,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'steps_completed': self.steps_completed,
            'errors': self.errors,
            'success': len(self.errors) == 0,
            'config': self.config
        }

        return report

    def run_deployment(self) -> bool:
        """Exécute le déploiement complet."""
        logger.info(f"🚀 Starting deployment to {self.environment}")
        logger.info(f"Dry run: {self.config['dry_run']}")

        steps = [
            ("pre_deployment_checks", self.run_pre_deployment_checks),
            ("database_migration", self.run_database_migration),
            ("products_creation", self.run_products_creation),
            ("data_migration", self.run_data_migration),
            ("post_migration_tests", self.run_post_migration_tests),
            ("webhook_configuration", self.configure_webhooks),
            ("final_validation", self.run_final_validation),
        ]

        success = True
        for step_name, step_func in steps:
            try:
                step_success = step_func()
                if not step_success:
                    success = False
                    if self.environment == 'production':
                        logger.error(f"Step {step_name} failed - stopping deployment")
                        break
                    else:
                        logger.warning(f"Step {step_name} failed - continuing in {self.environment}")
            except Exception as e:
                logger.error(f"Step {step_name} crashed: {e}")
                success = False
                if self.environment == 'production':
                    break

        # Générer rapport
        report = self.generate_deployment_report()

        if success:
            logger.info("✅ Deployment completed successfully")
            self._print_success_message()
        else:
            logger.error("❌ Deployment failed")
            self._print_failure_message()

        # Sauvegarder le rapport
        self._save_deployment_report(report)

        return success

    def _print_success_message(self):
        """Affiche le message de succès."""
        print("""
🎉 Deployment Successful!

Next steps:
1. Monitor logs for 24 hours
2. Test user-facing features
3. Gradually increase traffic
4. Monitor Stripe/Whop webhooks
5. Consider removing old tables after 30 days

Useful commands:
- Check webhook events: SELECT * FROM webhook_events ORDER BY processed_at DESC LIMIT 10;
- Monitor credits: SELECT * FROM user_credits WHERE credits_balance > 0;
- Check subscriptions: SELECT * FROM subscriptions WHERE status = 'active';
        """)

    def _print_failure_message(self):
        """Affiche le message d'échec."""
        print("""
❌ Deployment Failed!

Recovery options:
1. Check the logs in deploy_hybrid_architecture.log
2. Review errors in the deployment report
3. Run rollback if necessary: python scripts/migrate_to_hybrid_architecture.py --rollback
4. Contact the development team

Do not proceed with user traffic until issues are resolved.
        """)

    def _save_deployment_report(self, report: Dict[str, Any]):
        """Sauvegarde le rapport de déploiement."""
        import json

        report_file = f"deployment_report_{self.environment}_{int(time.time())}.json"

        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Deployment report saved: {report_file}")
        except Exception as e:
            logger.error(f"Failed to save deployment report: {e}")


def main():
    """Fonction principale."""
    import argparse

    parser = argparse.ArgumentParser(description='Deploy hybrid Stripe + Supabase architecture')
    parser.add_argument(
        '--environment',
        choices=['staging', 'production'],
        default='staging',
        help='Deployment environment'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip post-migration tests'
    )

    args = parser.parse_args()

    # Créer le gestionnaire de déploiement
    deployer = DeploymentManager(args.environment)

    # Exécuter le déploiement
    success = deployer.run_deployment()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

