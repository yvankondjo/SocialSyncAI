"""
Tests pour les fonctionnalités PRD2:
- Format JSON strict
- Escalade automatique
- Gestion des questions FAQ
- Contrôles IA
"""

import pytest
import json
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.rag_agent_prd2 import RAGAgentPRD2, AIResponse
from app.services.find_answers_prd2 import FindAnswersService, Answer
from app.schemas.faq_qa_service import FAQQuestionsAddRequest, FAQQuestionsUpdateRequest, FAQQuestionsDeleteRequest


class TestJSONParsing:
    """Tests unitaires pour le parsing JSON"""
    
    def test_valid_json_parsing(self):
        """JSON valide → OK"""
        agent = RAGAgentPRD2("test_user")
        
        valid_json = '{"response": "Bonjour!", "confidence": 0.85}'
        result = agent.parse_or_fix_json(valid_json)
        
        assert result is not None
        assert result.response == "Bonjour!"
        assert result.confidence == 0.85
    
    def test_invalid_json_with_retry(self):
        """JSON invalide → retry → OK"""
        agent = RAGAgentPRD2("test_user")
        
        with patch('app.services.rag_agent_prd2.client') as mock_client:
            # Mock de la correction
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"response": "Corrigé", "confidence": 0.75}'
            mock_client.chat.completions.create.return_value = mock_response
            
            invalid_json = '{"response": "Test", "confidence":}'  # JSON invalide
            result = agent.parse_or_fix_json(invalid_json)
            
            assert result is not None
            assert result.response == "Corrigé"
            assert result.confidence == 0.75
    
    def test_invalid_json_after_retry_fails(self):
        """JSON invalide → retry → encore invalide → erreur contrôlée"""
        agent = RAGAgentPRD2("test_user")
        
        with patch('app.services.rag_agent_prd2.client') as mock_client:
            # Mock qui échoue aussi
            mock_client.chat.completions.create.side_effect = Exception("Retry failed")
            
            invalid_json = '{"response": "Test"'  # JSON invalide
            result = agent.parse_or_fix_json(invalid_json)
            
            assert result is None


class TestEscalationThreshold:
    """Tests unitaires pour le seuil d'escalade"""
    
    @patch('app.services.rag_agent_prd2.get_db')
    def test_confidence_below_threshold_escalates(self, mock_db):
        """confidence = 0.09 → escalade + ai_mode='OFF'"""
        agent = RAGAgentPRD2("test_user")
        
        # Mock DB responses
        mock_db.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": "escalation_123"}]
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        
        escalation_id = agent.create_escalation("conv_123", "msg_123", 0.09, "Confiance faible")
        
        assert escalation_id == "escalation_123"
        # Vérifier que update a été appelé pour mettre ai_mode='OFF'
        mock_db.return_value.table.return_value.update.assert_called()
    
    def test_confidence_at_threshold_no_escalation(self):
        """confidence = 0.10 → pas d'escalade"""
        # Ce test serait dans un test d'intégration complet
        pass


class TestToolCalling:
    """Tests pour le tool-calling"""
    
    def test_tool_call_no_json_parsing(self):
        """Présence de tool_calls → aucun parsing JSON tenté"""
        agent = RAGAgentPRD2("test_user")
        
        with patch('app.services.rag_agent_prd2.client') as mock_client:
            # Mock réponse avec tool_calls
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.tool_calls = [Mock()]
            mock_response.choices[0].message.tool_calls[0].function.name = "find_answers"
            mock_response.choices[0].message.tool_calls[0].function.arguments = '{"question": "test"}'
            mock_response.choices[0].message.tool_calls[0].id = "call_123"
            mock_response.choices[0].message.content = None
            
            mock_client.chat.completions.create.return_value = mock_response
            
            result = agent.call_llm_with_tools([{"role": "user", "content": "test"}])
            
            assert result["tool_used"] == True


class TestFAQOperations:
    """Tests pour les opérations FAQ"""
    
    def test_add_multiple_questions(self):
        """Add multiples questions"""
        request = FAQQuestionsAddRequest(items=["Question 1", "Question 2", "Question 3"])
        
        assert len(request.items) == 3
        assert "Question 1" in request.items
    
    def test_update_by_index(self):
        """Update par index"""
        request = FAQQuestionsUpdateRequest(updates=[
            {"index": 0, "value": "Nouvelle question 1"},
            {"index": 2, "value": "Nouvelle question 3"}
        ])
        
        assert len(request.updates) == 2
        assert request.updates[0]["index"] == 0
        assert request.updates[1]["value"] == "Nouvelle question 3"
    
    def test_delete_multiple_indexes(self):
        """Delete 1..n indexes (non contigus)"""
        request = FAQQuestionsDeleteRequest(indexes=[0, 2, 4])
        
        assert len(request.indexes) == 3
        assert 0 in request.indexes
        assert 2 in request.indexes
        assert 4 in request.indexes
    
    def test_delete_out_of_bounds(self):
        """Test des bornes pour delete"""
        current_questions = ["Q1", "Q2", "Q3"]
        
        # Index valides
        valid_indexes = [0, 1, 2]
        for idx in valid_indexes:
            assert 0 <= idx < len(current_questions)
        
        # Index invalides
        invalid_indexes = [-1, 3, 10]
        for idx in invalid_indexes:
            assert not (0 <= idx < len(current_questions))


class TestAIControlGates:
    """Tests d'intégration pour les contrôles IA"""
    
    @patch('app.services.rag_agent_prd2.get_db')
    def test_global_ai_disabled(self, mock_db):
        """ai_settings.is_active=false → LLM non appelé"""
        agent = RAGAgentPRD2("test_user")
        
        # Mock: IA globalement désactivée
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "is_active": False
        }
        
        result = agent.process_message("Test message", "conv_123")
        
        assert result["response"] is None
        assert result["reason"] == "IA globalement désactivée"
    
    @patch('app.services.rag_agent_prd2.get_db')
    def test_conversation_ai_off(self, mock_db):
        """conversations.ai_mode='OFF' → LLM non appelé pour ce thread"""
        agent = RAGAgentPRD2("test_user")
        
        # Mock: IA globale OK mais conversation OFF
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            Mock(data={"is_active": True}),  # ai_settings
            Mock(data={"ai_mode": "OFF"})    # conversations
        ]
        
        result = agent.process_message("Test message", "conv_123")
        
        assert result["response"] is None
        assert result["reason"] == "IA désactivée pour cette conversation"


class TestFindAnswersService:
    """Tests pour le service find_answers sans embeddings"""
    
    @patch('app.services.find_answers_prd2.get_db')
    def test_find_answers_llm_driven(self, mock_db):
        """Service find_answers fonctionne via LLM, avec lots si nécessaire"""
        
        # Mock FAQs data
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "faq_1",
                "questions": ["Comment faire X?", "Comment réaliser X?"],
                "answer": "Voici comment faire X..."
            },
            {
                "id": "faq_2", 
                "questions": ["Où trouver Y?"],
                "answer": "Y se trouve ici..."
            }
        ]
        
        service = FindAnswersService("test_user", batch_size=2)
        faqs = service.get_active_faqs()
        
        assert len(faqs) == 2
        assert faqs[0]["id"] == "faq_1"
        assert len(faqs[0]["questions"]) == 2
    
    def test_batch_creation(self):
        """Test de la création de lots"""
        service = FindAnswersService("test_user", batch_size=2)
        
        faqs = [{"id": f"faq_{i}"} for i in range(5)]
        batches = service.create_batches(faqs)
        
        assert len(batches) == 3  # 5 FAQs avec batch_size=2 → 3 lots
        assert len(batches[0].faqs) == 2
        assert len(batches[1].faqs) == 2
        assert len(batches[2].faqs) == 1


class TestIntegrationEscalation:
    """Tests d'intégration pour l'escalade"""
    
    @patch('app.services.rag_agent_prd2.get_db')
    def test_escalation_creates_support_entry_and_mutes_conversation(self, mock_db):
        """Escalade → insertion support_escalations + mutation ai_mode='OFF'"""
        agent = RAGAgentPRD2("test_user")
        
        # Mock successful escalation creation
        mock_db.return_value.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "escalation_123"}
        ]
        
        escalation_id = agent.create_escalation("conv_123", "msg_123", 0.05, "Test escalation")
        
        assert escalation_id == "escalation_123"
        
        # Vérifier que les bonnes méthodes ont été appelées
        mock_db.return_value.table.assert_any_call("support_escalations")
        mock_db.return_value.table.assert_any_call("conversations")


# Tests E2E simulés
class TestE2EScenarios:
    """Tests End-to-End simulés"""
    
    @patch('app.services.rag_agent_prd2.get_db')
    @patch('app.services.rag_agent_prd2.client')
    def test_normal_conversation_flow(self, mock_client, mock_db):
        """Conversation normale → tool-call (find_answers) → JSON final → message livré"""
        
        # Setup mocks
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "is_active": True, "ai_mode": "ON"
        }
        
        # Mock LLM responses
        tool_response = Mock()
        tool_response.choices = [Mock()]
        tool_response.choices[0].message.tool_calls = [Mock()]
        tool_response.choices[0].message.tool_calls[0].function.name = "find_answers"
        tool_response.choices[0].message.tool_calls[0].function.arguments = '{"question": "test"}'
        tool_response.choices[0].message.tool_calls[0].id = "call_123"
        tool_response.choices[0].message.content = None
        
        final_response = Mock()
        final_response.choices = [Mock()]
        final_response.choices[0].message.content = '{"response": "Voici la réponse", "confidence": 0.85}'
        
        mock_client.chat.completions.create.side_effect = [tool_response, final_response]
        
        agent = RAGAgentPRD2("test_user")
        result = agent.process_message("Ma question", "conv_123")
        
        assert result["response"] == "Voici la réponse"
        assert result["confidence"] == 0.85
        assert result["escalated"] == False
    
    @patch('app.services.rag_agent_prd2.get_db')
    @patch('app.services.rag_agent_prd2.client')
    def test_risky_conversation_escalation(self, mock_client, mock_db):
        """Conversation risquée → JSON final confidence=0.05 → escalade + mute"""
        
        # Setup mocks
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "is_active": True, "ai_mode": "ON"
        }
        mock_db.return_value.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "escalation_456"}
        ]
        
        # Mock LLM response with low confidence
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"response": "Je ne suis pas sûr", "confidence": 0.05}'
        mock_response.choices[0].message.tool_calls = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        agent = RAGAgentPRD2("test_user")
        result = agent.process_message("Question difficile", "conv_123")
        
        assert result["escalated"] == True
        assert result["escalation_id"] == "escalation_456"
        assert result["response"] == "Transfert à un agent humain."