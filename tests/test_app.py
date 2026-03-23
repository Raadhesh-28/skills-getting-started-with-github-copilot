"""
Unit tests for the High School Management System API

Tests cover all endpoints and validation logic for the activity management system.
Uses AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


# Create test client
client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static index.html"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: Check redirect status and location
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that /activities returns all activities"""
        # Arrange: Activities are pre-loaded in the app
        
        # Act: Make GET request to activities endpoint
        response = client.get("/activities")
        
        # Assert: Check response status and content
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_activity_structure(self):
        """Test that activities have the correct structure"""
        # Arrange: Get activities data
        
        # Act: Request activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Check structure of one activity
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        # Arrange: Choose an activity and email
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        # Act: Make signup request
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        
        # Assert: Check response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Assert: Verify student was added to activity
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_already_enrolled(self):
        """Test that signup fails if student is already enrolled"""
        # Arrange: Use an email that's already signed up
        email = "michael@mergington.edu"
        
        # Act: Attempt to sign up again
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        # Assert: Check error response
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_activity_not_found(self):
        """Test that signup fails if activity doesn't exist"""
        # Arrange: Use non-existent activity
        email = "test@mergington.edu"
        
        # Act: Attempt signup for invalid activity
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": email}
        )
        
        # Assert: Check error response
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    @pytest.fixture(autouse=True)
    def reset_activities(self):
        """Reset activities to original state after each test"""
        yield
        # Restore original participants list
        activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
        activities["Basketball Team"]["participants"] = ["lucas@mergington.edu"]
        activities["Tennis Club"]["participants"] = ["ava@mergington.edu", "noah@mergington.edu"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # Arrange: Choose an enrolled student
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act: Make unregister request
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        
        # Assert: Check response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Assert: Verify student was removed
        activities_data = client.get("/activities").json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_student_not_enrolled(self):
        """Test that unregister fails if student is not enrolled"""
        # Arrange: Use email not in the activity
        email = "unknown@mergington.edu"
        
        # Act: Attempt unregister
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        # Assert: Check error response
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_activity_not_found(self):
        """Test that unregister fails if activity doesn't exist"""
        # Arrange: Use non-existent activity
        email = "michael@mergington.edu"
        
        # Act: Attempt unregister for invalid activity
        response = client.delete(
            "/activities/Nonexistent%20Club/signup",
            params={"email": email}
        )
        
        # Assert: Check error response
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    @pytest.fixture(autouse=True)
    def reset_activities(self):
        """Reset activities to original state after each test"""
        yield
        # Restore original participants list
        activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
        activities["Basketball Team"]["participants"] = ["lucas@mergington.edu"]
        activities["Tennis Club"]["participants"] = ["ava@mergington.edu", "noah@mergington.edu"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_signup_then_unregister(self):
        """Test signing up and then unregistering"""
        # Arrange: Choose test data
        email = "integration@mergington.edu"
        activity = "Art Studio"
        
        # Act: Sign up
        response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        
        # Assert: Signup successful
        assert response.status_code == 200
        
        # Assert: Verify signed up
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity]["participants"]
        
        # Act: Unregister
        response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        
        # Assert: Unregister successful
        assert response.status_code == 200
        
        # Assert: Verify unregistered
        activities_data = client.get("/activities").json()
        assert email not in activities_data[activity]["participants"]