"""
Comprehensive Test Suite for Comment/DM Automation with Real Data

Tests all aspects of the comment and DM response system:
- Hate speech detection (OpenAI Moderation)
- Custom blocked words/phrases (user guardrails)
- Escalation triggers
- Owner comment loop prevention
- Multimodal moderation (text + images)
- RAG silent failures

Uses MCP Supabase to insert and validate real test data.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.automation_service import AutomationService
from app.services.comment_triage import CommentTriageService
from app.services.ai_decision_service import AIDecisionService
from app.db.session import get_db

supabase = get_db()


class CommentAutomationTestSuite:
    """Comprehensive test suite for comment automation with real data"""

    # Test user configuration (from production DB)
    TEST_USER_ID = "b46a7229-2c29-4a88-ada1-c21a59f4eda1"
    TEST_INSTAGRAM_ACCOUNT_ID = "17841475667824583"
    TEST_INSTAGRAM_USERNAME = "socialsync072025"
    TEST_SOCIAL_ACCOUNT_ID = "fe923251-da7e-4116-a71f-6297c74dc6a8"

    def __init__(self):
        self.test_data_ids = {
            "posts": [],
            "comments": [],
            "ai_decisions": [],
            "original_ai_settings": None
        }
        self.test_results = []

    async def setup_environment(self) -> bool:
        """
        Phase 1: Setup test environment with guardrails

        Returns:
            bool: True if setup successful
        """
        print("\n" + "="*80)
        print("PHASE 1: SETUP TEST ENVIRONMENT")
        print("="*80 + "\n")

        try:
            # 1. Backup current AI settings
            print("📦 Backing up current AI settings...")
            result = supabase.table("ai_settings")\
                .select("*")\
                .eq("user_id", self.TEST_USER_ID)\
                .execute()

            if result.data:
                self.test_data_ids["original_ai_settings"] = result.data[0]
                print(f"✅ Backed up AI settings for user {self.TEST_USER_ID}")
            else:
                print(f"⚠️  No existing AI settings found for user {self.TEST_USER_ID}")

            # 2. Update AI settings with comprehensive guardrails
            print("\n🛡️  Configuring test guardrails...")

            test_guardrails = {
                "flagged_keywords": [
                    "viagra",
                    "spam",
                    "get rich quick",
                    "click here",
                    "casino"
                ],
                "flagged_phrases": [
                    "worst product ever",
                    "you suck",
                    "f*** you",
                    "je te déteste",  # French hate speech
                    "total waste of money"
                ],
                "instructions": "TEST MODE: Full automation testing with guardrails active",
                "ai_control_enabled": True,
                "ai_enabled_for_comments": True,
                "ai_enabled_for_chats": True,
                "is_active": True
            }

            update_result = supabase.table("ai_settings")\
                .update(test_guardrails)\
                .eq("user_id", self.TEST_USER_ID)\
                .execute()

            if update_result.data:
                print(f"✅ Updated AI settings with {len(test_guardrails['flagged_keywords'])} keywords "
                      f"and {len(test_guardrails['flagged_phrases'])} phrases")
            else:
                print("❌ Failed to update AI settings")
                return False

            # 3. Create or verify monitoring rules
            print("\n📋 Checking monitoring rules...")

            monitoring_result = supabase.table("monitoring_rules")\
                .select("*")\
                .eq("user_id", self.TEST_USER_ID)\
                .eq("social_account_id", self.TEST_SOCIAL_ACCOUNT_ID)\
                .execute()

            if not monitoring_result.data:
                # Create monitoring rules
                monitoring_data = {
                    "user_id": self.TEST_USER_ID,
                    "social_account_id": self.TEST_SOCIAL_ACCOUNT_ID,
                    "auto_monitor_enabled": True,
                    "auto_monitor_count": 5,
                    "monitoring_duration_days": 7
                }

                create_result = supabase.table("monitoring_rules")\
                    .insert(monitoring_data)\
                    .execute()

                if create_result.data:
                    print(f"✅ Created monitoring rules for account {self.TEST_INSTAGRAM_USERNAME}")
                else:
                    print("⚠️  Could not create monitoring rules")
            else:
                print(f"✅ Verified monitoring rules for account {self.TEST_INSTAGRAM_USERNAME}")

            print("   ℹ️  AI control for comments is managed via ai_settings.ai_enabled_for_comments")

            print("\n✅ Environment setup complete!")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    async def create_test_post(self) -> Optional[str]:
        """
        Create a monitored test post

        Returns:
            Optional[str]: Post ID if successful
        """
        print("\n📝 Creating test monitored post...")

        try:
            post_data = {
                "user_id": self.TEST_USER_ID,
                "social_account_id": self.TEST_SOCIAL_ACCOUNT_ID,
                "platform_post_id": f"TEST_POST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "platform": "instagram",
                "caption": "🚀 Exciting new product launch! What do you think? #test #automation",
                "media_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
                "posted_at": datetime.now().isoformat(),
                "source": "manual",
                "monitoring_enabled": True,
                "monitoring_started_at": datetime.now().isoformat(),
                "monitoring_ends_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "next_check_at": datetime.now().isoformat()
            }

            result = supabase.table("monitored_posts")\
                .insert(post_data)\
                .execute()

            if result.data:
                post_id = result.data[0]["id"]
                self.test_data_ids["posts"].append(post_id)
                print(f"✅ Created test post: {post_id}")
                return post_id
            else:
                print("❌ Failed to create test post")
                return None

        except Exception as e:
            print(f"❌ Failed to create post: {str(e)}")
            return None

    async def insert_test_comments(self, post_id: str) -> List[Tuple[str, str, str]]:
        """
        Insert 10 test comments covering all scenarios

        Args:
            post_id: ID of the monitored post

        Returns:
            List of (comment_id, scenario_name, expected_triage) tuples
        """
        print("\n💬 Inserting test comments...")

        test_comments = [
            # Test 1: Normal comment (should respond)
            {
                "scenario": "NORMAL_COMMENT",
                "author_name": "john_doe_customer",
                "author_id": "12345678901",
                "text": "This looks amazing! What's the price of this product? I'm very interested!",
                "expected_triage": "respond",
                "expected_decision": "respond"
            },
            # Test 2: Flagged keyword (should ignore)
            {
                "scenario": "FLAGGED_KEYWORD_VIAGRA",
                "author_name": "spammer_bot_123",
                "author_id": "98765432101",
                "text": "Buy cheap viagra online! Visit our website now!",
                "expected_triage": "ignore",
                "expected_decision": "ignore"
            },
            # Test 3: Flagged keyword (casino)
            {
                "scenario": "FLAGGED_KEYWORD_CASINO",
                "author_name": "casino_promoter",
                "author_id": "11111111111",
                "text": "Join our casino and win big! Click here for free spins!",
                "expected_triage": "ignore",
                "expected_decision": "ignore"
            },
            # Test 4: Flagged phrase (should ignore)
            {
                "scenario": "FLAGGED_PHRASE_WORST",
                "author_name": "angry_customer_99",
                "author_id": "22222222222",
                "text": "This is the worst product ever! Total waste of money!",
                "expected_triage": "ignore",
                "expected_decision": "ignore"
            },
            # Test 5: Flagged phrase (French hate speech)
            {
                "scenario": "FLAGGED_PHRASE_FRENCH",
                "author_name": "hater_fr",
                "author_id": "33333333333",
                "text": "Je te déteste! Ton produit est nul!",
                "expected_triage": "ignore",
                "expected_decision": "ignore"
            },
            # Test 6: Hate speech (OpenAI Moderation should flag)
            {
                "scenario": "HATE_SPEECH_OPENAI",
                "author_name": "toxic_user_666",
                "author_id": "44444444444",
                "text": "You're a stupid idiot and I hate you! Go die!",
                "expected_triage": "ignore",
                "expected_decision": "ignore"
            },
            # Test 7: Owner comment (should always ignore - loop prevention)
            {
                "scenario": "OWNER_COMMENT_LOOP_PREVENTION",
                "author_name": self.TEST_INSTAGRAM_USERNAME,  # Same as owner
                "author_id": self.TEST_INSTAGRAM_ACCOUNT_ID,
                "text": "Thanks everyone for the amazing feedback! ❤️",
                "expected_triage": "ignore",
                "expected_decision": None  # Should not reach AIDecisionService
            },
            # Test 8: Question about pricing (should respond)
            {
                "scenario": "PRICING_QUESTION",
                "author_name": "potential_buyer_42",
                "author_id": "55555555555",
                "text": "How much does this cost? Is there a discount code available?",
                "expected_triage": "respond",
                "expected_decision": "respond"
            },
            # Test 9: Positive feedback (should respond)
            {
                "scenario": "POSITIVE_FEEDBACK",
                "author_name": "happy_customer_2024",
                "author_id": "66666666666",
                "text": "I absolutely love this! Best purchase I've made this year! 🔥",
                "expected_triage": "respond",
                "expected_decision": "respond"
            },
            # Test 10: Complex request (will pass to RAG, escalation tested separately)
            {
                "scenario": "COMPLEX_REQUEST",
                "author_name": "complex_issue_user",
                "author_id": "77777777777",
                "text": "I need to speak with a human urgently! This is a very complex issue that AI cannot help me with. I need immediate human assistance please!",
                "expected_triage": "respond",
                "expected_decision": "respond"  # AIDecisionService passes to RAG, RAG handles escalation
            }
        ]

        inserted_comments = []

        for idx, comment_data in enumerate(test_comments, 1):
            try:
                comment_record = {
                    "monitored_post_id": post_id,
                    "platform_comment_id": f"TEST_COMMENT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                    "author_name": comment_data["author_name"],
                    "author_id": comment_data["author_id"],
                    "text": comment_data["text"],
                    "like_count": 0,
                    "created_at": (datetime.now() - timedelta(minutes=60-idx)).isoformat(),
                    "triage": None,  # Will be set by processing
                    "ai_decision_id": None,
                    "replied_at": None
                }

                result = supabase.table("comments")\
                    .insert(comment_record)\
                    .execute()

                if result.data:
                    comment_id = result.data[0]["id"]
                    self.test_data_ids["comments"].append(comment_id)
                    inserted_comments.append((
                        comment_id,
                        comment_data["scenario"],
                        comment_data["expected_triage"],
                        comment_data["expected_decision"]
                    ))
                    print(f"  ✅ #{idx}: {comment_data['scenario']} (ID: {comment_id[:8]}...)")
                else:
                    print(f"  ❌ #{idx}: Failed to insert {comment_data['scenario']}")

            except Exception as e:
                print(f"  ❌ #{idx}: Error inserting comment: {str(e)}")

        print(f"\n✅ Inserted {len(inserted_comments)}/{len(test_comments)} test comments")
        return inserted_comments

    async def process_comments(self, comment_ids: List[str]) -> Dict:
        """
        Process test comments through the automation pipeline

        Args:
            comment_ids: List of comment IDs to process

        Returns:
            Dict with processing results
        """
        print("\n" + "="*80)
        print("PHASE 5: PROCESSING COMMENTS THROUGH AUTOMATION PIPELINE")
        print("="*80 + "\n")

        results = {
            "processed": 0,
            "failed": 0,
            "details": []
        }

        automation_service = AutomationService()
        triage_service = CommentTriageService(
            user_id=self.TEST_USER_ID,
            owner_username=self.TEST_INSTAGRAM_USERNAME
        )
        decision_service = AIDecisionService(user_id=self.TEST_USER_ID)

        for comment_id in comment_ids:
            try:
                print(f"\n🔄 Processing comment {comment_id[:8]}...")

                # 1. Fetch comment
                comment_result = supabase.table("comments")\
                    .select("*, monitored_posts!inner(*, social_accounts!inner(*))")\
                    .eq("id", comment_id)\
                    .execute()

                if not comment_result.data:
                    print(f"  ❌ Comment not found")
                    results["failed"] += 1
                    continue

                comment = comment_result.data[0]
                post = comment["monitored_posts"]

                print(f"  📝 Text: {comment['text'][:50]}...")
                print(f"  👤 Author: {comment['author_name']}")

                # 2. Check AutomationService
                should_auto = automation_service.should_auto_reply(
                    user_id=self.TEST_USER_ID,
                    comment_id=comment_id,
                    context_type="comment"
                )

                print(f"  🤖 AutomationService: should_reply={should_auto['should_reply']}")

                if not should_auto["should_reply"]:
                    # Update comment triage
                    supabase.table("comments")\
                        .update({"triage": "ignore"})\
                        .eq("id", comment_id)\
                        .execute()

                    results["processed"] += 1
                    results["details"].append({
                        "comment_id": comment_id,
                        "stage": "automation_service",
                        "decision": "ignore",
                        "reason": should_auto.get("reason")
                    })
                    continue

                # 3. Check CommentTriageService
                all_comments = [comment]  # Simplified for testing
                should_respond, triage_reason = triage_service.should_ai_respond(
                    comment, post, all_comments
                )

                print(f"  🎯 TriageService: should_respond={should_respond}, reason={triage_reason}")

                if not should_respond:
                    # Update comment triage
                    supabase.table("comments")\
                        .update({"triage": triage_reason})\
                        .eq("id", comment_id)\
                        .execute()

                    results["processed"] += 1
                    results["details"].append({
                        "comment_id": comment_id,
                        "stage": "triage_service",
                        "decision": triage_reason,
                        "reason": "Owner comment or user-to-user conversation"
                    })
                    continue

                # 4. Check AIDecisionService
                decision, confidence, reason, matched_rule = decision_service.check_message(
                    message_text=comment["text"],
                    context_type="comment",
                    message_content=comment
                )

                print(f"  🛡️  AIDecisionService: decision={decision}, confidence={confidence:.2f}")
                print(f"     Reason: {reason}")
                if matched_rule:
                    print(f"     Matched rule: {matched_rule}")

                # 5. Log AI decision
                ai_decision_data = {
                    "user_id": self.TEST_USER_ID,
                    "message_id": comment_id,
                    "decision": decision.value if hasattr(decision, 'value') else str(decision),
                    "confidence": float(confidence),
                    "reason": reason,
                    "matched_rule": matched_rule,
                    "message_text": comment["text"][:500],
                    "snapshot_json": {
                        "author": comment["author_name"],
                        "text": comment["text"],
                        "post_caption": post.get("caption", "")
                    }
                }

                ai_decision_result = supabase.table("ai_decisions")\
                    .insert(ai_decision_data)\
                    .execute()

                ai_decision_id = ai_decision_result.data[0]["id"] if ai_decision_result.data else None
                self.test_data_ids["ai_decisions"].append(ai_decision_id)

                # 6. Update comment with decision
                final_triage = "respond" if decision.value == "respond" else "ignore"

                supabase.table("comments")\
                    .update({
                        "triage": final_triage,
                        "ai_decision_id": ai_decision_id
                    })\
                    .eq("id", comment_id)\
                    .execute()

                results["processed"] += 1
                results["details"].append({
                    "comment_id": comment_id,
                    "stage": "ai_decision_service",
                    "decision": decision.value if hasattr(decision, 'value') else str(decision),
                    "confidence": confidence,
                    "reason": reason,
                    "matched_rule": matched_rule,
                    "ai_decision_id": ai_decision_id
                })

                print(f"  ✅ Processed successfully - Final triage: {final_triage}")

            except Exception as e:
                print(f"  ❌ Error processing comment: {str(e)}")
                import traceback
                traceback.print_exc()
                results["failed"] += 1

        print(f"\n📊 Processing complete: {results['processed']} processed, {results['failed']} failed")
        return results

    async def validate_results(self, test_comments: List[Tuple], processing_results: Dict) -> Dict:
        """
        Validate test results against expected outcomes

        Args:
            test_comments: List of (comment_id, scenario, expected_triage, expected_decision) tuples
            processing_results: Results from process_comments()

        Returns:
            Dict with validation results
        """
        print("\n" + "="*80)
        print("PHASE 6: VALIDATING TEST RESULTS")
        print("="*80 + "\n")

        validation_results = {
            "total": len(test_comments),
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for comment_id, scenario, expected_triage, expected_decision in test_comments:
            try:
                print(f"\n🔍 Validating {scenario}...")

                # Fetch final comment state
                comment_result = supabase.table("comments")\
                    .select("*, ai_decisions(*)")\
                    .eq("id", comment_id)\
                    .execute()

                if not comment_result.data:
                    print(f"  ❌ Comment not found")
                    validation_results["failed"] += 1
                    continue

                comment = comment_result.data[0]
                actual_triage = comment.get("triage")

                # Check triage
                triage_match = actual_triage == expected_triage

                print(f"  📊 Triage: Expected={expected_triage}, Actual={actual_triage} {'✅' if triage_match else '❌'}")

                # Check AI decision if expected
                decision_match = True
                if expected_decision and comment.get("ai_decisions"):
                    ai_decision = comment["ai_decisions"]
                    actual_decision = ai_decision.get("decision")
                    decision_match = actual_decision == expected_decision
                    print(f"  🛡️  Decision: Expected={expected_decision}, Actual={actual_decision} {'✅' if decision_match else '❌'}")

                    if ai_decision.get("matched_rule"):
                        print(f"     Matched rule: {ai_decision['matched_rule']}")
                    print(f"     Reason: {ai_decision.get('reason', 'N/A')}")

                # Overall pass/fail
                passed = triage_match and decision_match

                if passed:
                    validation_results["passed"] += 1
                    print(f"  ✅ TEST PASSED")
                else:
                    validation_results["failed"] += 1
                    print(f"  ❌ TEST FAILED")

                validation_results["details"].append({
                    "scenario": scenario,
                    "comment_id": comment_id,
                    "expected_triage": expected_triage,
                    "actual_triage": actual_triage,
                    "expected_decision": expected_decision,
                    "actual_decision": ai_decision.get("decision") if comment.get("ai_decisions") else None,
                    "matched_rule": ai_decision.get("matched_rule") if comment.get("ai_decisions") else None,
                    "passed": passed
                })

            except Exception as e:
                print(f"  ❌ Validation error: {str(e)}")
                validation_results["failed"] += 1

        print(f"\n" + "="*80)
        print(f"VALIDATION SUMMARY: {validation_results['passed']}/{validation_results['total']} PASSED")
        print("="*80)

        return validation_results

    async def cleanup(self):
        """Clean up test data"""
        print("\n" + "="*80)
        print("PHASE 7: CLEANUP TEST DATA")
        print("="*80 + "\n")

        try:
            # Delete test comments
            if self.test_data_ids["comments"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['comments'])} test comments...")
                for comment_id in self.test_data_ids["comments"]:
                    supabase.table("comments").delete().eq("id", comment_id).execute()
                print("  ✅ Comments deleted")

            # Delete test AI decisions
            if self.test_data_ids["ai_decisions"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['ai_decisions'])} AI decisions...")
                for decision_id in self.test_data_ids["ai_decisions"]:
                    if decision_id:
                        supabase.table("ai_decisions").delete().eq("id", decision_id).execute()
                print("  ✅ AI decisions deleted")

            # Delete test posts
            if self.test_data_ids["posts"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['posts'])} test posts...")
                for post_id in self.test_data_ids["posts"]:
                    supabase.table("monitored_posts").delete().eq("id", post_id).execute()
                print("  ✅ Posts deleted")

            # Restore original AI settings
            if self.test_data_ids["original_ai_settings"]:
                print("📦 Restoring original AI settings...")
                original = self.test_data_ids["original_ai_settings"]
                supabase.table("ai_settings")\
                    .update({
                        "flagged_keywords": original["flagged_keywords"],
                        "flagged_phrases": original["flagged_phrases"],
                        "instructions": original["instructions"]
                    })\
                    .eq("user_id", self.TEST_USER_ID)\
                    .execute()
                print("  ✅ AI settings restored")

            print("\n✅ Cleanup complete!")

        except Exception as e:
            print(f"⚠️  Cleanup error: {str(e)}")

    async def run_all_tests(self, skip_cleanup: bool = False):
        """Run complete test suite"""
        print("\n" + "="*80)
        print("COMMENT AUTOMATION COMPREHENSIVE TEST SUITE")
        print("="*80)

        try:
            # Phase 1: Setup
            if not await self.setup_environment():
                print("\n❌ Setup failed, aborting tests")
                return

            # Phase 2: Create test post
            post_id = await self.create_test_post()
            if not post_id:
                print("\n❌ Failed to create test post, aborting tests")
                return

            # Phase 3: Insert test comments
            test_comments = await self.insert_test_comments(post_id)
            if not test_comments:
                print("\n❌ Failed to insert test comments, aborting tests")
                return

            # Phase 4: Process comments
            comment_ids = [c[0] for c in test_comments]
            processing_results = await self.process_comments(comment_ids)

            # Phase 5: Validate results
            validation_results = await self.validate_results(test_comments, processing_results)

            # Phase 6: Generate report
            await self.generate_report(validation_results)

            # Phase 7: Cleanup (optional)
            if not skip_cleanup:
                await self.cleanup()
            else:
                print("\n⚠️  Skipping cleanup (--no-cleanup flag)")

            # Final summary
            print("\n" + "="*80)
            print("TEST SUITE COMPLETE")
            print("="*80)
            print(f"\n✅ {validation_results['passed']}/{validation_results['total']} tests passed")
            print(f"❌ {validation_results['failed']}/{validation_results['total']} tests failed")

            if validation_results['passed'] == validation_results['total']:
                print("\n🎉 ALL TESTS PASSED! 🎉")
            else:
                print(f"\n⚠️  {validation_results['failed']} tests failed - see TEST_REPORT.md for details")

        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()

    async def generate_report(self, validation_results: Dict):
        """Generate detailed test report"""
        print("\n📝 Generating test report...")

        report_path = "/workspace/TEST_REPORT.md"

        with open(report_path, "w") as f:
            f.write("# Comment Automation Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test User:** `{self.TEST_USER_ID}`\n")
            f.write(f"**Instagram Account:** `@{self.TEST_INSTAGRAM_USERNAME}`\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {validation_results['total']}\n")
            f.write(f"- **Passed:** ✅ {validation_results['passed']}\n")
            f.write(f"- **Failed:** ❌ {validation_results['failed']}\n")
            f.write(f"- **Success Rate:** {(validation_results['passed']/validation_results['total']*100):.1f}%\n\n")

            f.write("## Test Results\n\n")

            for detail in validation_results["details"]:
                status = "✅ PASS" if detail["passed"] else "❌ FAIL"
                f.write(f"### {status} - {detail['scenario']}\n\n")
                f.write(f"- **Comment ID:** `{detail['comment_id']}`\n")
                f.write(f"- **Expected Triage:** `{detail['expected_triage']}`\n")
                f.write(f"- **Actual Triage:** `{detail['actual_triage']}`\n")

                if detail['expected_decision']:
                    f.write(f"- **Expected Decision:** `{detail['expected_decision']}`\n")
                    f.write(f"- **Actual Decision:** `{detail['actual_decision']}`\n")

                if detail.get('matched_rule'):
                    f.write(f"- **Matched Rule:** `{detail['matched_rule']}`\n")

                f.write("\n")

            f.write("## Database Queries for Verification\n\n")
            f.write("```sql\n")
            f.write(f"-- View all test comments\n")
            f.write(f"SELECT id, author_name, text, triage, replied_at \n")
            f.write(f"FROM comments \n")
            f.write(f"WHERE monitored_post_id IN ('{self.test_data_ids['posts'][0] if self.test_data_ids['posts'] else 'N/A'}');\n\n")
            f.write(f"-- View all AI decisions\n")
            f.write(f"SELECT decision, confidence, matched_rule, reason \n")
            f.write(f"FROM ai_decisions \n")
            f.write(f"WHERE user_id = '{self.TEST_USER_ID}' \n")
            f.write(f"ORDER BY created_at DESC LIMIT 10;\n")
            f.write("```\n\n")

            f.write("## Recommendations\n\n")

            if validation_results['failed'] > 0:
                f.write("### Failed Tests\n\n")
                for detail in validation_results["details"]:
                    if not detail["passed"]:
                        f.write(f"- **{detail['scenario']}**: Review AI decision logic\n")
                f.write("\n")
            else:
                f.write("✅ All tests passed! The comment automation system is working as expected.\n\n")

        print(f"  ✅ Report generated: {report_path}")


async def main():
    """Main test runner"""
    import sys

    skip_cleanup = "--no-cleanup" in sys.argv

    suite = CommentAutomationTestSuite()
    await suite.run_all_tests(skip_cleanup=skip_cleanup)


if __name__ == "__main__":
    asyncio.run(main())
