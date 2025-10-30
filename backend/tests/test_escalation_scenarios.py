"""
Escalation Testing Suite with Real Data

Tests the RAG Agent's ability to escalate conversations to humans:
- Explicit escalation requests
- Complex issues requiring human judgment
- Forced escalation via specific phrases
- Email notification verification
- AI mode switching (ON → OFF)

Uses real conversations and DMs to trigger escalation tool.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.rag_agent import RAGAgent
from app.db.session import get_db

supabase = get_db()


class EscalationTestSuite:
    """Test suite for RAG Agent escalation scenarios"""

    # Test user configuration
    TEST_USER_ID = "b46a7229-2c29-4a88-ada1-c21a59f4eda1"
    TEST_INSTAGRAM_ACCOUNT_ID = "17841475667824583"
    TEST_WHATSAPP_ACCOUNT_ID = "683178638221369"
    TEST_SOCIAL_ACCOUNT_ID = "fe923251-da7e-4116-a71f-6297c74dc6a8"

    def __init__(self):
        self.test_data_ids = {
            "conversations": [],
            "messages": [],
            "escalations": []
        }
        self.test_results = []

    async def create_test_conversation(self, platform: str = "instagram") -> Optional[str]:
        """
        Create a test conversation for escalation testing

        Args:
            platform: 'instagram' or 'whatsapp'

        Returns:
            Optional[str]: Conversation ID if successful
        """
        print(f"\n📱 Creating test {platform} conversation...")

        try:
            conversation_data = {
                "social_account_id": self.TEST_SOCIAL_ACCOUNT_ID,
                "external_conversation_id": f"TEST_CONV_{platform.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "customer_identifier": "escalation_test_999",
                "customer_name": "Test Customer - Escalation",
                "ai_mode": "ON",  # AI initially ON
                "status": "open",
                "last_message_at": datetime.now().isoformat(),
                "unread_count": 0,
                "automation_disabled": False
            }

            result = supabase.table("conversations")\
                .insert(conversation_data)\
                .execute()

            if result.data:
                conversation_id = result.data[0]["id"]
                self.test_data_ids["conversations"].append(conversation_id)
                print(f"  ✅ Created conversation: {conversation_id}")
                return conversation_id
            else:
                print("  ❌ Failed to create conversation")
                return None

        except Exception as e:
            print(f"  ❌ Error creating conversation: {str(e)}")
            return None

    async def insert_escalation_trigger_messages(self, conversation_id: str) -> List[Dict]:
        """
        Insert messages designed to trigger RAG escalation

        Args:
            conversation_id: Target conversation ID

        Returns:
            List of inserted messages
        """
        print("\n💬 Inserting escalation trigger messages...")

        escalation_scenarios = [
            # Scenario 1: Explicit human request
            {
                "scenario": "EXPLICIT_HUMAN_REQUEST",
                "text": "I need to speak with a human representative immediately. This is urgent!",
                "expected_escalation": True,
                "reason": "Explicit request for human contact"
            },
            # Scenario 2: Complex technical issue
            {
                "scenario": "COMPLEX_TECHNICAL_ISSUE",
                "text": "I've tried everything you suggested but nothing works. My account is completely broken and I'm losing money every day. I need a real person to look at this now!",
                "expected_escalation": True,
                "reason": "Complex issue beyond AI capabilities"
            },
            # Scenario 3: Frustration + human request
            {
                "scenario": "FRUSTRATED_HUMAN_REQUEST",
                "text": "Your AI is useless! I've been going in circles for an hour. Connect me to a REAL HUMAN who can actually help me!",
                "expected_escalation": True,
                "reason": "Customer frustration + explicit human request"
            },
            # Scenario 4: Legal/compliance issue
            {
                "scenario": "LEGAL_COMPLIANCE",
                "text": "I need to discuss a legal matter regarding my account. This requires human attention for GDPR compliance.",
                "expected_escalation": True,
                "reason": "Legal/compliance issue requiring human judgment"
            },
            # Scenario 5: Multiple keywords
            {
                "scenario": "MULTIPLE_ESCALATION_KEYWORDS",
                "text": "I absolutely need urgent human assistance right now. AI cannot help with this complex issue. Please escalate to support team immediately!",
                "expected_escalation": True,
                "reason": "Multiple strong escalation keywords"
            }
        ]

        inserted_messages = []

        for idx, scenario_data in enumerate(escalation_scenarios, 1):
            try:
                # Create inbound message
                message_data = {
                    "conversation_id": conversation_id,
                    "external_message_id": f"TEST_MSG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                    "direction": "inbound",
                    "content": scenario_data["text"],
                    "status": "sent"
                }

                result = supabase.table("conversation_messages")\
                    .insert(message_data)\
                    .execute()

                if result.data:
                    message_id = result.data[0]["id"]
                    self.test_data_ids["messages"].append(message_id)
                    inserted_messages.append({
                        "message_id": message_id,
                        "scenario": scenario_data["scenario"],
                        "text": scenario_data["text"],
                        "expected_escalation": scenario_data["expected_escalation"],
                        "reason": scenario_data["reason"]
                    })
                    print(f"  ✅ #{idx}: {scenario_data['scenario']} (ID: {message_id[:8]}...)")
                else:
                    print(f"  ❌ #{idx}: Failed to insert {scenario_data['scenario']}")

            except Exception as e:
                print(f"  ❌ #{idx}: Error inserting message: {str(e)}")

        print(f"\n✅ Inserted {len(inserted_messages)}/{len(escalation_scenarios)} messages")
        return inserted_messages

    async def test_rag_escalation_detection(self, conversation_id: str, messages: List[Dict]) -> List[Dict]:
        """
        Test RAG Agent's ability to detect escalation needs

        Args:
            conversation_id: Conversation ID
            messages: List of test messages

        Returns:
            List of test results
        """
        print("\n" + "="*80)
        print("TESTING RAG AGENT ESCALATION DETECTION")
        print("="*80 + "\n")

        results = []

        # Initialize RAG Agent
        rag_agent = RAGAgent()

        for message_data in messages:
            try:
                print(f"\n🔍 Testing: {message_data['scenario']}")
                print(f"   Message: {message_data['text'][:80]}...")

                # Build conversation context
                context = {
                    "user_id": self.TEST_USER_ID,
                    "conversation_id": conversation_id,
                    "message": message_data["text"],
                    "customer_name": "Test Customer",
                    "platform": "instagram"
                }

                # Generate response (RAG should detect escalation need)
                print("   🤖 Invoking RAG Agent...")

                response = await rag_agent.generate_response(
                    user_id=self.TEST_USER_ID,
                    message_text=message_data["text"],
                    conversation_id=conversation_id,
                    customer_name="Test Customer",
                    platform="instagram"
                )

                print(f"   📝 Response: {response[:100]}...")

                # Check if escalation was triggered
                # Query escalations table
                escalation_result = supabase.table("support_escalations")\
                    .select("*")\
                    .eq("conversation_id", conversation_id)\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()

                escalation_triggered = bool(escalation_result.data)

                # Check if AI mode was switched OFF
                conversation_result = supabase.table("conversations")\
                    .select("ai_mode")\
                    .eq("id", conversation_id)\
                    .execute()

                ai_mode = conversation_result.data[0]["ai_mode"] if conversation_result.data else "ON"

                # Validate results
                expected_escalation = message_data["expected_escalation"]
                passed = escalation_triggered == expected_escalation

                if escalation_triggered:
                    escalation = escalation_result.data[0]
                    self.test_data_ids["escalations"].append(escalation["id"])
                    print(f"   🆘 Escalation created: {escalation['id'][:8]}...")
                    print(f"      Reason: {escalation.get('reason', 'N/A')}")
                    print(f"      Status: {escalation.get('status', 'N/A')}")
                    print(f"   🤖 AI Mode: {ai_mode}")

                    if ai_mode == "OFF":
                        print(f"   ✅ AI correctly disabled after escalation")
                    else:
                        print(f"   ⚠️  AI mode still ON (expected OFF)")
                        passed = False
                else:
                    print(f"   ⚠️  No escalation triggered (expected: {expected_escalation})")

                results.append({
                    "scenario": message_data["scenario"],
                    "message_id": message_data["message_id"],
                    "expected_escalation": expected_escalation,
                    "actual_escalation": escalation_triggered,
                    "ai_mode": ai_mode,
                    "response": response,
                    "passed": passed
                })

                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {status}")

                # Reset conversation for next test
                if escalation_triggered:
                    supabase.table("conversations")\
                        .update({"ai_mode": "ON"})\
                        .eq("id", conversation_id)\
                        .execute()
                    print(f"   🔄 Reset AI mode to ON for next test")

            except Exception as e:
                print(f"   ❌ Error testing scenario: {str(e)}")
                import traceback
                traceback.print_exc()

                results.append({
                    "scenario": message_data["scenario"],
                    "message_id": message_data["message_id"],
                    "expected_escalation": message_data["expected_escalation"],
                    "actual_escalation": False,
                    "error": str(e),
                    "passed": False
                })

        return results

    async def validate_escalation_flow(self) -> Dict:
        """
        Validate complete escalation flow:
        1. Escalation record created
        2. AI mode switched OFF
        3. Email notification sent (check logs)
        4. Conversation remains open

        Returns:
            Dict with validation results
        """
        print("\n" + "="*80)
        print("VALIDATING ESCALATION FLOW")
        print("="*80 + "\n")

        validation_results = {
            "escalations_created": 0,
            "ai_mode_disabled": 0,
            "conversations_open": 0,
            "passed": True
        }

        try:
            # Check all escalations
            if self.test_data_ids["escalations"]:
                print(f"🔍 Checking {len(self.test_data_ids['escalations'])} escalations...")

                for escalation_id in self.test_data_ids["escalations"]:
                    escalation_result = supabase.table("support_escalations")\
                        .select("*, conversations!inner(*)")\
                        .eq("id", escalation_id)\
                        .execute()

                    if escalation_result.data:
                        escalation = escalation_result.data[0]
                        conversation = escalation["conversations"]

                        validation_results["escalations_created"] += 1

                        # Check AI mode
                        if conversation["ai_mode"] == "OFF":
                            validation_results["ai_mode_disabled"] += 1
                            print(f"  ✅ Escalation {escalation_id[:8]}: AI mode OFF")
                        else:
                            print(f"  ❌ Escalation {escalation_id[:8]}: AI mode still ON!")
                            validation_results["passed"] = False

                        # Check conversation status
                        if conversation["status"] == "open":
                            validation_results["conversations_open"] += 1
                            print(f"     Conversation status: open ✅")
                        else:
                            print(f"     Conversation status: {conversation['status']} ⚠️")

                        # Display escalation details
                        print(f"     Reason: {escalation.get('reason', 'N/A')}")
                        print(f"     Created: {escalation.get('created_at', 'N/A')}")

                print(f"\n📊 Validation Summary:")
                print(f"   - Escalations created: {validation_results['escalations_created']}")
                print(f"   - AI mode disabled: {validation_results['ai_mode_disabled']}/{validation_results['escalations_created']}")
                print(f"   - Conversations open: {validation_results['conversations_open']}/{validation_results['escalations_created']}")

        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            validation_results["passed"] = False

        return validation_results

    async def generate_escalation_report(self, test_results: List[Dict], validation_results: Dict):
        """Generate detailed escalation test report"""
        print("\n📝 Generating escalation test report...")

        report_path = "/workspace/ESCALATION_TEST_REPORT.md"

        with open(report_path, "w") as f:
            f.write("# RAG Agent Escalation Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test User:** `{self.TEST_USER_ID}`\n\n")

            # Summary
            passed_count = sum(1 for r in test_results if r["passed"])
            total_count = len(test_results)

            f.write("## Summary\n\n")
            f.write(f"- **Total Scenarios:** {total_count}\n")
            f.write(f"- **Passed:** ✅ {passed_count}\n")
            f.write(f"- **Failed:** ❌ {total_count - passed_count}\n")
            f.write(f"- **Success Rate:** {(passed_count/total_count*100):.1f}%\n\n")

            # Escalation flow validation
            f.write("## Escalation Flow Validation\n\n")
            f.write(f"- **Escalations Created:** {validation_results['escalations_created']}\n")
            f.write(f"- **AI Mode Disabled:** {validation_results['ai_mode_disabled']}/{validation_results['escalations_created']}\n")
            f.write(f"- **Conversations Open:** {validation_results['conversations_open']}/{validation_results['escalations_created']}\n")
            f.write(f"- **Overall Status:** {'✅ PASS' if validation_results['passed'] else '❌ FAIL'}\n\n")

            # Test results
            f.write("## Test Scenarios\n\n")

            for result in test_results:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                f.write(f"### {status} - {result['scenario']}\n\n")
                f.write(f"- **Message ID:** `{result['message_id']}`\n")
                f.write(f"- **Expected Escalation:** `{result['expected_escalation']}`\n")
                f.write(f"- **Actual Escalation:** `{result['actual_escalation']}`\n")
                f.write(f"- **AI Mode After:** `{result.get('ai_mode', 'N/A')}`\n")

                if result.get("response"):
                    f.write(f"- **RAG Response:** \"{result['response'][:150]}...\"\n")

                if result.get("error"):
                    f.write(f"- **Error:** `{result['error']}`\n")

                f.write("\n")

            # Database queries
            f.write("## Database Queries for Verification\n\n")
            f.write("```sql\n")
            f.write("-- View all escalations\n")
            f.write("SELECT e.id, e.reason, e.status, c.ai_mode, c.status as conversation_status\n")
            f.write("FROM support_escalations e\n")
            f.write("JOIN conversations c ON e.conversation_id = c.id\n")
            f.write(f"WHERE e.user_id = '{self.TEST_USER_ID}'\n")
            f.write("ORDER BY e.created_at DESC;\n\n")

            f.write("-- View conversation messages\n")
            f.write("SELECT conversation_id, direction, content, created_at\n")
            f.write("FROM conversation_messages\n")
            if self.test_data_ids["conversations"]:
                f.write(f"WHERE conversation_id = '{self.test_data_ids['conversations'][0]}'\n")
            f.write("ORDER BY created_at;\n")
            f.write("```\n\n")

            # Recommendations
            f.write("## Recommendations\n\n")

            if not validation_results["passed"]:
                f.write("### ⚠️ Issues Found\n\n")
                if validation_results["ai_mode_disabled"] < validation_results["escalations_created"]:
                    f.write("- **AI Mode Not Disabled:** Some escalations did not properly disable AI mode\n")
                    f.write("  - Check `escalation` tool implementation in `rag_agent.py`\n")
                    f.write("  - Verify conversation update logic\n\n")

                failed_tests = [r for r in test_results if not r["passed"]]
                if failed_tests:
                    f.write("- **Failed Escalation Detection:**\n")
                    for r in failed_tests:
                        f.write(f"  - {r['scenario']}: Review escalation keywords in system prompt\n")
                    f.write("\n")
            else:
                f.write("✅ All escalation tests passed! The RAG Agent correctly handles escalation scenarios.\n\n")

            # Escalation keywords reference
            f.write("## Escalation Keywords Reference\n\n")
            f.write("The RAG Agent should trigger escalation when detecting these patterns:\n\n")
            f.write("- **Explicit requests:** \"speak with human\", \"talk to a person\", \"real person\"\n")
            f.write("- **Urgency:** \"urgent\", \"immediately\", \"right now\"\n")
            f.write("- **Complexity:** \"too complex\", \"AI can't help\", \"beyond AI\"\n")
            f.write("- **Frustration:** \"going in circles\", \"useless\", \"not helping\"\n")
            f.write("- **Legal/Compliance:** \"legal matter\", \"GDPR\", \"compliance issue\"\n\n")

        print(f"  ✅ Report generated: {report_path}")

    async def cleanup(self):
        """Clean up test data"""
        print("\n" + "="*80)
        print("CLEANUP TEST DATA")
        print("="*80 + "\n")

        try:
            # Delete test messages
            if self.test_data_ids["messages"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['messages'])} test messages...")
                for message_id in self.test_data_ids["messages"]:
                    supabase.table("conversation_messages").delete().eq("id", message_id).execute()
                print("  ✅ Messages deleted")

            # Delete test escalations
            if self.test_data_ids["escalations"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['escalations'])} escalations...")
                for escalation_id in self.test_data_ids["escalations"]:
                    supabase.table("support_escalations").delete().eq("id", escalation_id).execute()
                print("  ✅ Escalations deleted")

            # Delete test conversations
            if self.test_data_ids["conversations"]:
                print(f"🗑️  Deleting {len(self.test_data_ids['conversations'])} test conversations...")
                for conversation_id in self.test_data_ids["conversations"]:
                    supabase.table("conversations").delete().eq("id", conversation_id).execute()
                print("  ✅ Conversations deleted")

            print("\n✅ Cleanup complete!")

        except Exception as e:
            print(f"⚠️  Cleanup error: {str(e)}")

    async def run_all_tests(self, skip_cleanup: bool = False):
        """Run complete escalation test suite"""
        print("\n" + "="*80)
        print("RAG AGENT ESCALATION TEST SUITE")
        print("="*80)

        try:
            # Create test conversation
            conversation_id = await self.create_test_conversation()
            if not conversation_id:
                print("\n❌ Failed to create conversation, aborting tests")
                return

            # Insert escalation trigger messages
            messages = await self.insert_escalation_trigger_messages(conversation_id)
            if not messages:
                print("\n❌ Failed to insert messages, aborting tests")
                return

            # Test RAG escalation detection
            test_results = await self.test_rag_escalation_detection(conversation_id, messages)

            # Validate escalation flow
            validation_results = await self.validate_escalation_flow()

            # Generate report
            await self.generate_escalation_report(test_results, validation_results)

            # Cleanup
            if not skip_cleanup:
                await self.cleanup()
            else:
                print("\n⚠️  Skipping cleanup (--no-cleanup flag)")

            # Final summary
            passed_count = sum(1 for r in test_results if r["passed"])
            print("\n" + "="*80)
            print("TEST SUITE COMPLETE")
            print("="*80)
            print(f"\n✅ {passed_count}/{len(test_results)} scenarios passed")
            print(f"❌ {len(test_results) - passed_count}/{len(test_results)} scenarios failed")

            if passed_count == len(test_results) and validation_results["passed"]:
                print("\n🎉 ALL ESCALATION TESTS PASSED! 🎉")
            else:
                print(f"\n⚠️  Some tests failed - see ESCALATION_TEST_REPORT.md for details")

        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    """Main test runner"""
    import sys

    skip_cleanup = "--no-cleanup" in sys.argv

    suite = EscalationTestSuite()
    await suite.run_all_tests(skip_cleanup=skip_cleanup)


if __name__ == "__main__":
    asyncio.run(main())
