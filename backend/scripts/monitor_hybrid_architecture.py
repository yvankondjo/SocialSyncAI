#!/usr/bin/env python3
"""
Script de monitoring pour l'architecture hybride Stripe + Supabase.

Surveille:
- Santé des webhooks Stripe/Whop
- Cohérence des données
- Métriques de performance
- Alertes en cas de problèmes

Usage:
    python scripts/monitor_hybrid_architecture.py [--continuous] [--alert-threshold=5]

Options:
    --continuous: Surveillance continue (toutes les 5 minutes)
    --alert-threshold: Seuil d'alertes avant notification (défaut: 5)
"""

import sys
import os
import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from app.core.config import get_settings
from app.services.webhook_helpers import get_webhook_stats

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_hybrid_architecture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HybridArchitectureMonitor:
    """Moniteur pour l'architecture hybride."""

    def __init__(self, alert_threshold: int = 5):
        self.alert_threshold = alert_threshold
        self.db = None
        self.alerts = []
        self.metrics = {}

        self._init_database()

    def _init_database(self):
        """Initialise la connexion à la base de données."""
        try:
            settings = get_settings()
            self.db = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)

    def run_health_check(self) -> Dict[str, Any]:
        """Exécute un contrôle de santé complet."""
        logger.info("🏥 Running health check...")

        checks = {
            'database_connectivity': self._check_database_connectivity,
            'table_integrity': self._check_table_integrity,
            'data_consistency': self._check_data_consistency,
            'webhook_health': self._check_webhook_health,
            'stripe_sync': self._check_stripe_sync,
            'whop_sync': self._check_whop_sync,
            'credit_system': self._check_credit_system,
        }

        results = {}
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                results[check_name] = result

                if result['status'] == 'error':
                    self._add_alert('error', check_name, result.get('message', 'Check failed'))
                elif result['status'] == 'warning':
                    self._add_alert('warning', check_name, result.get('message', 'Check warning'))

            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                self._add_alert('error', check_name, str(e))

        # Calculer score de santé global
        health_score = self._calculate_health_score(results)

        health_check = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health_score': health_score,
            'results': results,
            'alerts': self.alerts,
            'metrics': self.metrics
        }

        return health_check

    def _check_database_connectivity(self) -> Dict[str, Any]:
        """Vérifie la connectivité à la base de données."""
        try:
            # Test simple de connectivité
            result = self.db.table('users').select('count', count='exact').execute()

            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'user_count': result.count
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database connection failed: {str(e)}'
            }

    def _check_table_integrity(self) -> Dict[str, Any]:
        """Vérifie l'intégrité des tables."""
        required_tables = [
            'customers', 'products', 'prices', 'subscriptions',
            'user_credits', 'webhook_events', 'credit_transactions'
        ]

        missing_tables = []
        for table in required_tables:
            try:
                self.db.table(table).select('id').limit(1).execute()
            except Exception:
                missing_tables.append(table)

        if missing_tables:
            return {
                'status': 'error',
                'message': f'Missing tables: {", ".join(missing_tables)}'
            }

        return {
            'status': 'healthy',
            'message': f'All {len(required_tables)} tables present'
        }

    def _check_data_consistency(self) -> Dict[str, Any]:
        """Vérifie la cohérence des données."""
        try:
            issues = []

            # Vérifier que tous les user_credits ont un user_id valide
            orphaned_credits = self.db.table('user_credits').select(
                'user_id'
            ).not_.in_('user_id', self.db.table('auth.users').select('id')).execute()

            if orphaned_credits.data:
                issues.append(f'{len(orphaned_credits.data)} orphaned user_credits entries')

            # Vérifier que les subscriptions ont des user_id valides
            orphaned_subs = self.db.table('subscriptions').select(
                'user_id'
            ).not_.in_('user_id', self.db.table('auth.users').select('id')).execute()

            if orphaned_subs.data:
                issues.append(f'{len(orphaned_subs.data)} orphaned subscriptions entries')

            # Vérifier cohérence crédits vs transactions
            credits_result = self.db.table('user_credits').select('user_id, credits_balance').execute()
            for user_credits in credits_result.data:
                # Calculer balance depuis transactions
                transactions = self.db.table('credit_transactions').select(
                    'credits_amount'
                ).eq('user_id', user_credits['user_id']).execute()

                calculated_balance = sum(t['credits_amount'] for t in transactions.data)

                if abs(calculated_balance - user_credits['credits_balance']) > 0.01:  # Tolérance flottante
                    issues.append(f'Balance mismatch for user {user_credits["user_id"]}: '
                                f'expected {calculated_balance}, got {user_credits["credits_balance"]}')

            if issues:
                return {
                    'status': 'warning' if len(issues) < 5 else 'error',
                    'message': f'Data consistency issues: {"; ".join(issues[:5])}'
                }

            return {
                'status': 'healthy',
                'message': 'Data consistency verified'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Data consistency check failed: {str(e)}'
            }

    def _check_webhook_health(self) -> Dict[str, Any]:
        """Vérifie la santé des webhooks."""
        try:
            # Statistiques des 24 dernières heures
            webhook_stats = get_webhook_stats(self.db, days=1)

            # Vérifier taux d'erreur
            total_events = webhook_stats.get('total_events', 0)
            error_events = 0  # TODO: Compter les événements en erreur

            error_rate = (error_events / total_events * 100) if total_events > 0 else 0

            if error_rate > 10:  # Plus de 10% d'erreurs
                return {
                    'status': 'error',
                    'message': f'High webhook error rate: {error_rate:.1f}% ({error_events}/{total_events})'
                }
            elif error_rate > 5:  # Plus de 5% d'erreurs
                return {
                    'status': 'warning',
                    'message': f'Elevated webhook error rate: {error_rate:.1f}% ({error_events}/{total_events})'
                }

            return {
                'status': 'healthy',
                'message': f'Webhook health good: {total_events} events processed',
                'stats': webhook_stats
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Webhook health check failed: {str(e)}'
            }

    def _check_stripe_sync(self) -> Dict[str, Any]:
        """Vérifie la synchronisation Stripe."""
        try:
            # Compter produits Stripe actifs
            stripe_products = self.db.table('products').select('id').eq('source', 'stripe').eq('active', True).execute()

            # Compter prix actifs
            stripe_prices = self.db.table('prices').select('id').execute()

            # Compter abonnements actifs
            stripe_subs = self.db.table('subscriptions').select('id').eq('source', 'stripe').in_('status', ['active', 'trialing']).execute()

            return {
                'status': 'healthy',
                'message': f'Stripe sync: {len(stripe_products.data)} products, {len(stripe_prices.data)} prices, {len(stripe_subs.data)} subscriptions'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Stripe sync check failed: {str(e)}'
            }

    def _check_whop_sync(self) -> Dict[str, Any]:
        """Vérifie la synchronisation Whop."""
        try:
            # Compter produits Whop actifs
            whop_products = self.db.table('products').select('id').eq('source', 'whop').eq('active', True).execute()

            # Compter abonnements Whop actifs
            whop_subs = self.db.table('subscriptions').select('id').eq('source', 'whop').in_('status', ['active', 'trialing']).execute()

            if len(whop_products.data) == 0 and len(whop_subs.data) == 0:
                return {
                    'status': 'info',
                    'message': 'Whop not configured or no active data'
                }

            return {
                'status': 'healthy',
                'message': f'Whop sync: {len(whop_products.data)} products, {len(whop_subs.data)} subscriptions'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Whop sync check failed: {str(e)}'
            }

    def _check_credit_system(self) -> Dict[str, Any]:
        """Vérifie le système de crédits."""
        try:
            # Statistiques des crédits
            credits_stats = self.db.table('user_credits').select(
                'credits_balance',
                count='exact'
            ).execute()

            total_users_with_credits = credits_stats.count
            total_credits = sum(c['credits_balance'] for c in credits_stats.data)

            # Transactions récentes (dernières 24h)
            recent_transactions = self.db.table('credit_transactions').select(
                'id',
                count='exact'
            ).gte('created_at', (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()).execute()

            # Crédits utilisés récemment
            credits_used_24h = self.db.table('credit_transactions').select(
                'credits_amount'
            ).gte('created_at', (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                 ).eq('transaction_type', 'deduction').execute()

            total_used_24h = sum(abs(t['credits_amount']) for t in credits_used_24h.data)

            self.metrics.update({
                'total_users_with_credits': total_users_with_credits,
                'total_credits_system': total_credits,
                'transactions_24h': recent_transactions.count,
                'credits_used_24h': total_used_24h
            })

            return {
                'status': 'healthy',
                'message': f'Credit system: {total_users_with_credits} users, {total_credits:.0f} total credits, {recent_transactions.count} transactions/24h'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Credit system check failed: {str(e)}'
            }

    def _calculate_health_score(self, results: Dict[str, Any]) -> float:
        """Calcule un score de santé global (0-100)."""
        total_checks = len(results)
        error_weight = 3
        warning_weight = 1
        healthy_weight = 0

        total_weight = 0

        for check_result in results.values():
            status = check_result.get('status', 'unknown')
            if status == 'error':
                total_weight += error_weight
            elif status == 'warning':
                total_weight += warning_weight
            elif status == 'healthy':
                total_weight += healthy_weight

        max_possible_weight = total_checks * error_weight
        health_score = 100 * (1 - total_weight / max_possible_weight)

        return max(0, min(100, health_score))

    def _add_alert(self, level: str, component: str, message: str):
        """Ajoute une alerte."""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'component': component,
            'message': message
        }

        self.alerts.append(alert)

        # Log selon le niveau
        if level == 'error':
            logger.error(f"🚨 {component}: {message}")
        elif level == 'warning':
            logger.warning(f"⚠️  {component}: {message}")
        else:
            logger.info(f"ℹ️  {component}: {message}")

    def send_alerts_if_needed(self):
        """Envoie les alertes si le seuil est dépassé."""
        if len(self.alerts) >= self.alert_threshold:
            self._send_alert_notification()

    def _send_alert_notification(self):
        """Envoie une notification d'alerte."""
        # TODO: Implémenter notification (email, Slack, etc.)
        logger.warning(f"🚨 {len(self.alerts)} alerts detected - notification would be sent")

    def run_continuous_monitoring(self, interval_minutes: int = 5):
        """Surveillance continue."""
        logger.info(f"🔄 Starting continuous monitoring (every {interval_minutes} minutes)")

        try:
            while True:
                health_check = self.run_health_check()
                self.send_alerts_if_needed()

                # Sauvegarder métriques
                self._save_metrics(health_check)

                # Attendre jusqu'au prochain check
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            logger.info("🛑 Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Continuous monitoring crashed: {e}")

    def _save_metrics(self, health_check: Dict[str, Any]):
        """Sauvegarde les métriques."""
        try:
            metrics_file = f"health_metrics_{int(time.time())}.json"

            with open(metrics_file, 'w') as f:
                json.dump(health_check, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport de monitoring."""
        health_check = self.run_health_check()

        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'period': 'current',
            'health_check': health_check,
            'recommendations': self._generate_recommendations(health_check)
        }

        return report

    def _generate_recommendations(self, health_check: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur les résultats."""
        recommendations = []

        results = health_check.get('results', {})

        # Recommandations basées sur les checks
        if results.get('webhook_health', {}).get('status') == 'error':
            recommendations.append("Investigate webhook failures - check Stripe/Whop dashboard")

        if results.get('data_consistency', {}).get('status') in ['warning', 'error']:
            recommendations.append("Fix data consistency issues - run data migration repair")

        if results.get('credit_system', {}).get('status') == 'error':
            recommendations.append("Credit system issues detected - check transaction logs")

        if health_check.get('health_score', 100) < 80:
            recommendations.append("Overall health degraded - consider rollback or investigation")

        if not recommendations:
            recommendations.append("All systems healthy - no action required")

        return recommendations


def main():
    """Fonction principale."""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor hybrid Stripe + Supabase architecture')
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Monitoring interval in minutes (default: 5)'
    )
    parser.add_argument(
        '--alert-threshold',
        type=int,
        default=5,
        help='Alert threshold before notification (default: 5)'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate and display a monitoring report'
    )

    args = parser.parse_args()

    # Créer le moniteur
    monitor = HybridArchitectureMonitor(alert_threshold=args.alert_threshold)

    if args.report:
        # Générer un rapport
        report = monitor.generate_report()

        print("📊 Hybrid Architecture Health Report")
        print("=" * 50)
        print(json.dumps(report, indent=2, default=str))

    elif args.continuous:
        # Surveillance continue
        monitor.run_continuous_monitoring(interval_minutes=args.interval)

    else:
        # Check unique
        health_check = monitor.run_health_check()

        print("🏥 Health Check Results")
        print("=" * 30)

        score = health_check.get('health_score', 0)
        status = "✅ Healthy" if score >= 90 else "⚠️  Warning" if score >= 70 else "🚨 Critical"

        print(f"Health Score: {score:.1f}/100 - {status}")
        print(f"Timestamp: {health_check['timestamp']}")
        print()

        print("Component Status:")
        for component, result in health_check.get('results', {}).items():
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️ ',
                'error': '🚨',
                'info': 'ℹ️ '
            }.get(result.get('status', 'unknown'), '❓')

            print(f"  {status_icon} {component}: {result.get('message', 'Unknown')}")

        print()
        print(f"Alerts: {len(health_check.get('alerts', []))}")

        if health_check.get('alerts'):
            print("Alert Details:")
            for alert in health_check['alerts'][:5]:  # Max 5 alerts
                print(f"  {alert['level'].upper()}: {alert['component']} - {alert['message']}")

        # Sauvegarder si des erreurs
        if score < 90 or health_check.get('alerts'):
            monitor._save_metrics(health_check)
            print(f"\n💾 Detailed report saved: health_metrics_{int(time.time())}.json")


if __name__ == "__main__":
    main()

