import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.subscriber_service import SubscriberService
from app.models.schemas import SubscriberCreate, SubscriberUpdate, PhoneType, ServiceType
from app.database.postgres_db import Subscriber

class TestSubscriberService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_session = AsyncMock()

    @patch('app.services.subscriber_service.Neo4jService')
    async def test_create_subscriber(self, mock_neo4j):
        """Test Case 1: Create a new subscriber"""
        data = SubscriberCreate(
            ric_number="1234567890",
            pin_code="1234",
            full_name="John Doe",
            phone_model="iPhone 15",
            phone_type=PhoneType.SMARTPHONE,
            service_type=ServiceType.PREPAID,
            contract_duration_months=12,
            contract_start_date=date.today(),
            monthly_cost=50.0
        )
        
        result = await SubscriberService.create(self.db_session, data)

        self.db_session.add.assert_called_once()
        self.db_session.flush.assert_called_once()
        self.db_session.refresh.assert_called_once()
        self.assertEqual(result.full_name, "John Doe")
        self.assertEqual(result.ric_number, "1234567890")

    async def test_get_by_id(self):
        """Test Case 2: Get subscriber by ID"""
        subscriber_id = 1
        mock_subscriber = Subscriber(id=subscriber_id, full_name="John Doe")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_subscriber
        self.db_session.execute.return_value = mock_result

        result = await SubscriberService.get_by_id(self.db_session, subscriber_id)

        self.assertEqual(result.id, subscriber_id)
        self.assertEqual(result.full_name, "John Doe")

    async def test_update_subscriber(self):
        """Test Case 3: Update subscriber info"""

        subscriber_id = 1
        existing_subscriber = Subscriber(id=subscriber_id, full_name="Old Name", phone_model="Old Model")
        

        with patch.object(SubscriberService, 'get_by_id', return_value=existing_subscriber):
            update_data = SubscriberUpdate(full_name="New Name")
            

            result = await SubscriberService.update(self.db_session, subscriber_id, update_data)


            self.assertEqual(result.full_name, "New Name")
            self.assertEqual(result.phone_model, "Old Model") 
            self.db_session.flush.assert_called_once()
            self.db_session.refresh.assert_called_once()

    async def test_delete_subscriber(self):
        """Test Case 4: Delete subscriber"""
        subscriber_id = 1
        existing_subscriber = Subscriber(id=subscriber_id)
        
        with patch.object(SubscriberService, 'get_by_id', return_value=existing_subscriber):
            result = await SubscriberService.delete(self.db_session, subscriber_id)

            self.assertTrue(result)
            self.db_session.delete.assert_called_once_with(existing_subscriber)

if __name__ == '__main__':
    unittest.main()
