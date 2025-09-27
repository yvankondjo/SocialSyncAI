"""
Tests pour les nouvelles routes FAQ PRD2
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from app.main import app

client = TestClient(app)


class TestFAQQuestionsRoutes:
    """Tests pour les routes de gestion des questions FAQ"""
    
    @patch('app.routers.faq_qa.get_authenticated_db')
    @patch('app.routers.faq_qa.get_current_user_id')
    def test_add_faq_questions(self, mock_user_id, mock_db):
        """Test POST /faq-qa/{faq_id}/questions:add"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock existing FAQ
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "faq_123",
            "questions": ["Question existante"]
        }
        
        # Mock successful update
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        response = client.post(
            "/api/faq-qa/faq_123/questions:add",
            json={"items": ["Nouvelle question 1", "Nouvelle question 2"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions ajoutées avec succès" in data["message"]
        assert len(data["questions"]) == 3  # 1 existante + 2 nouvelles
    
    @patch('app.routers.faq_qa.get_authenticated_db')
    @patch('app.routers.faq_qa.get_current_user_id')
    def test_update_faq_questions(self, mock_user_id, mock_db):
        """Test POST /faq-qa/{faq_id}/questions:update"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock existing FAQ with questions
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "faq_123",
            "questions": ["Question 1", "Question 2", "Question 3"]
        }
        
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        response = client.post(
            "/api/faq-qa/faq_123/questions:update",
            json={
                "updates": [
                    {"index": 0, "value": "Question 1 modifiée"},
                    {"index": 2, "value": "Question 3 modifiée"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions mises à jour" in data["message"]
        assert data["questions"][0] == "Question 1 modifiée"
        assert data["questions"][2] == "Question 3 modifiée"
    
    @patch('app.routers.faq_qa.get_authenticated_db')
    @patch('app.routers.faq_qa.get_current_user_id')
    def test_delete_faq_questions(self, mock_user_id, mock_db):
        """Test POST /faq-qa/{faq_id}/questions:delete"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock existing FAQ with questions
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "faq_123",
            "questions": ["Question 1", "Question 2", "Question 3", "Question 4"]
        }
        
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        response = client.post(
            "/api/faq-qa/faq_123/questions:delete",
            json={"indexes": [0, 2]}  # Supprimer questions aux index 0 et 2
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions supprimées" in data["message"]
        assert len(data["questions"]) == 2  # 4 - 2 = 2 restantes
        assert data["questions"] == ["Question 2", "Question 4"]
    
    @patch('app.routers.faq_qa.get_authenticated_db')
    @patch('app.routers.faq_qa.get_current_user_id')
    def test_delete_questions_out_of_bounds(self, mock_user_id, mock_db):
        """Test validation des indexes hors limites"""
        mock_user_id.return_value = "test_user_id"
        
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "faq_123",
            "questions": ["Question 1", "Question 2"]
        }
        
        response = client.post(
            "/api/faq-qa/faq_123/questions:delete",
            json={"indexes": [0, 5]}  # Index 5 hors limites
        )
        
        assert response.status_code == 400
        assert "Index 5 hors limites" in response.json()["detail"]
    
    @patch('app.routers.faq_qa.get_authenticated_db')
    @patch('app.routers.faq_qa.get_current_user_id')
    def test_delete_all_questions_forbidden(self, mock_user_id, mock_db):
        """Test qu'on ne peut pas supprimer toutes les questions"""
        mock_user_id.return_value = "test_user_id"
        
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "faq_123",
            "questions": ["Seule question"]
        }
        
        response = client.post(
            "/api/faq-qa/faq_123/questions:delete",
            json={"indexes": [0]}  # Supprimer la seule question
        )
        
        assert response.status_code == 400
        assert "au moins une question" in response.json()["detail"]


class TestConversationAIModeRoute:
    """Tests pour la route de contrôle IA par conversation"""
    
    @patch('app.routers.conversations.get_authenticated_db')
    @patch('app.routers.conversations.get_current_user_id')
    def test_update_conversation_ai_mode_to_off(self, mock_user_id, mock_db):
        """Test PATCH /conversations/{conversation_id}/ai_mode"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock conversation exists
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "conv_123"}
        ]
        
        # Mock successful update
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        response = client.patch(
            "/api/conversations/conv_123/ai_mode",
            json={"mode": "OFF"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_mode"] == "OFF"
        assert "conv_123" in data["conversation_id"]
    
    @patch('app.routers.conversations.get_authenticated_db')
    @patch('app.routers.conversations.get_current_user_id')
    def test_invalid_ai_mode(self, mock_user_id, mock_db):
        """Test validation du mode IA"""
        mock_user_id.return_value = "test_user_id"
        
        response = client.patch(
            "/api/conversations/conv_123/ai_mode",
            json={"mode": "INVALID"}
        )
        
        assert response.status_code == 400
        assert "ON" in response.json()["detail"] and "OFF" in response.json()["detail"]
    
    @patch('app.routers.conversations.get_authenticated_db')
    @patch('app.routers.conversations.get_current_user_id')
    def test_conversation_not_found(self, mock_user_id, mock_db):
        """Test conversation inexistante"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock conversation not found
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.patch(
            "/api/conversations/nonexistent/ai_mode",
            json={"mode": "OFF"}
        )
        
        assert response.status_code == 404
        assert "non trouvée" in response.json()["detail"]


class TestSupportEscalationRoutes:
    """Tests pour les routes d'escalade support"""
    
    @patch('app.routers.support.get_authenticated_db')
    @patch('app.routers.support.get_current_user_id')
    def test_get_user_escalations(self, mock_user_id, mock_db):
        """Test GET /support/escalations"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock escalations data
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {
                "id": "esc_1",
                "user_id": "test_user_id",
                "conversation_id": "conv_123",
                "message_id": "msg_123",
                "confidence": 0.05,
                "reason": "Confiance faible",
                "notified": False,
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        response = client.get("/api/support/escalations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["confidence"] == 0.05
        assert data[0]["notified"] == False
    
    @patch('app.routers.support.get_authenticated_db')
    @patch('app.routers.support.get_current_user_id')
    def test_notify_escalation(self, mock_user_id, mock_db):
        """Test POST /support/escalations/{escalation_id}/notify"""
        mock_user_id.return_value = "test_user_id"
        
        # Mock escalation exists
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "esc_1",
            "user_id": "test_user_id"
        }
        
        # Mock successful update
        mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        response = client.post("/api/support/escalations/esc_1/notify")
        
        assert response.status_code == 200
        data = response.json()
        assert data["notified"] == True
        assert "Notification envoyée" in data["message"]
    
    @patch('app.routers.support.get_authenticated_db')
    @patch('app.routers.support.get_current_user_id')
    def test_get_specific_escalation(self, mock_user_id, mock_db):
        """Test GET /support/escalations/{escalation_id}"""
        mock_user_id.return_value = "test_user_id"
        
        mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "esc_1",
            "user_id": "test_user_id",
            "conversation_id": "conv_123",
            "message_id": "msg_123",
            "confidence": 0.08,
            "reason": "Test escalation",
            "notified": True,
            "created_at": "2024-01-01T10:00:00Z"
        }
        
        response = client.get("/api/support/escalations/esc_1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "esc_1"
        assert data["confidence"] == 0.08
        assert data["notified"] == True