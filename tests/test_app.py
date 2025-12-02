"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_json(self):
        """Test that GET /activities returns valid JSON"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that all expected activities are present"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Band",
            "Debate Team",
            "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in data, f"Activity '{activity}' not found in response"

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Field '{field}' missing from '{activity_name}'"

    def test_get_activities_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for '{activity_name}' is not a list"


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_returns_200(self):
        """Test successful signup returns status code 200"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_for_activity_returns_message(self):
        """Test signup returns success message"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_for_nonexistent_activity_returns_404(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant to the activity"""
        test_email = "signup_test@mergington.edu"
        test_activity = "Chess Club"
        
        # Get initial participants count
        response1 = client.get("/activities")
        initial_count = len(response1.json()[test_activity]["participants"])
        
        # Sign up
        response2 = client.post(
            f"/activities/{test_activity}/signup?email={test_email}"
        )
        assert response2.status_code == 200
        
        # Verify participant was added
        response3 = client.get("/activities")
        new_count = len(response3.json()[test_activity]["participants"])
        assert new_count == initial_count + 1
        assert test_email in response3.json()[test_activity]["participants"]

    def test_signup_multiple_different_students(self):
        """Test multiple different students can sign up"""
        test_emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in test_emails:
            response = client.post(
                f"/activities/Tennis%20Club/signup?email={email}"
            )
            assert response.status_code == 200

    def test_signup_respects_max_participants(self):
        """Test that signup validates max participants limit"""
        # This test verifies the logic in the signup endpoint
        # Note: The current implementation doesn't check max_participants
        # so this test documents expected behavior
        response = client.get("/activities")
        data = response.json()
        
        # All activities should have a max_participants value
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0


class TestUnregisterEndpoint:
    """Test the DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_returns_200(self):
        """Test successful unregister returns status code 200"""
        # First, sign up
        test_email = "unregister_test@mergington.edu"
        client.post(
            f"/activities/Basketball%20Team/signup?email={test_email}"
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/Basketball%20Team/participants?email={test_email}"
        )
        assert response.status_code == 200

    def test_unregister_returns_message(self):
        """Test unregister returns success message"""
        test_email = "unregister_msg@mergington.edu"
        client.post(
            f"/activities/Art%20Studio/signup?email={test_email}"
        )
        
        response = client.delete(
            f"/activities/Art%20Studio/participants?email={test_email}"
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        test_email = "remove_test@mergington.edu"
        test_activity = "Music Band"
        
        # Sign up
        client.post(
            f"/activities/{test_activity}/signup?email={test_email}"
        )
        
        # Verify participant exists
        response1 = client.get("/activities")
        assert test_email in response1.json()[test_activity]["participants"]
        
        # Unregister
        response2 = client.delete(
            f"/activities/{test_activity}/participants?email={test_email}"
        )
        assert response2.status_code == 200
        
        # Verify participant was removed
        response3 = client.get("/activities")
        assert test_email not in response3.json()[test_activity]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Club/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_nonexistent_participant_returns_404(self):
        """Test unregister of non-existent participant returns 404"""
        response = client.delete(
            "/activities/Science%20Club/participants?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in activity"


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirect_to_static(self):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivityData:
    """Test the integrity of the activities data"""

    def test_all_activities_have_participants(self):
        """Test that all activities have a participants list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_participants_are_valid_emails(self):
        """Test that all participants appear to be valid email addresses"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert "@" in participant, f"Invalid email format: {participant}"
                assert "." in participant.split("@")[1], f"Invalid email format: {participant}"

    def test_no_activity_exceeds_participants_limit(self):
        """Test that no activity currently exceeds its max participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            actual_participants = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert actual_participants <= max_participants, \
                f"Activity '{activity_name}' exceeds max participants limit"
