"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Save original state
    original_activities = {
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and inter-school games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn and practice tennis skills on the school courts",
            "schedule": "Saturdays, 10:00 AM - 12:00 PM",
            "max_participants": 10,
            "participants": ["sarah@mergington.edu"]
        },
        "Drama Club": {
            "description": "Act in school plays and theatrical productions",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "isabella@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills through competitive debate",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["james@mergington.edu", "ava@mergington.edu"]
        },
        "Robotics Club": {
            "description": "Build and program robots for competitions",
            "schedule": "Fridays, 3:30 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["ryan@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Reset activities before test
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestRoot:
    """Tests for root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Basketball Team" in data
        assert "Tennis Club" in data
    
    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_have_initial_participants(self, client):
        """Test that activities have the expected initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "alex@mergington.edu" in data["Basketball Team"]["participants"]
        assert "sarah@mergington.edu" in data["Tennis Club"]["participants"]
        assert len(data["Drama Club"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successfully signing up for an activity"""
        response = client.post("/activities/Basketball%20Team/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        assert "newstudent@mergington.edu" in activities_response.json()["Basketball Team"]["participants"]
    
    def test_signup_duplicate_email(self, client):
        """Test signing up with an email already registered for the activity"""
        response = client.post("/activities/Basketball%20Team/signup?email=alex@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for an activity that doesn't exist"""
        response = client.post("/activities/Nonexistent%20Activity/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_signup_activity_full(self, client):
        """Test signing up for a full activity"""
        # First, fill up the Chess Club (max 12, currently has 2)
        activity = activities["Chess Club"]
        for i in range(10):
            activity["participants"].append(f"student{i}@mergington.edu")
        
        # Now try to sign up when full
        response = client.post("/activities/Chess%20Club/signup?email=fulltest@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successfully unregistering from an activity"""
        # First verify the student is registered
        activities_response = client.get("/activities")
        assert "alex@mergington.edu" in activities_response.json()["Basketball Team"]["participants"]
        
        # Unregister
        response = client.delete("/activities/Basketball%20Team/unregister?email=alex@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        assert "alex@mergington.edu" not in activities_response.json()["Basketball Team"]["participants"]
    
    def test_unregister_not_registered(self, client):
        """Test unregistering a student who isn't registered"""
        response = client.delete("/activities/Basketball%20Team/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete("/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_multiple_participants(self, client):
        """Test unregistering one participant doesn't affect others"""
        # Drama Club has 2 participants
        activity = activities["Drama Club"]
        original_participants = activity["participants"].copy()
        
        # Unregister one
        response = client.delete("/activities/Drama%20Club/unregister?email=lucas@mergington.edu")
        assert response.status_code == 200
        
        # Verify only one was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()["Drama Club"]["participants"]
        assert "lucas@mergington.edu" not in participants
        assert "isabella@mergington.edu" in participants
        assert len(participants) == len(original_participants) - 1


class TestActivityParticipantLimits:
    """Tests for activity participant limits"""
    
    def test_participant_count_respects_max(self, client):
        """Test that participant count cannot exceed max_participants"""
        activity = activities["Tennis Club"]
        original_max = activity["max_participants"]
        original_count = len(activity["participants"])
        
        # Try to add more than max allowed
        for i in range(original_max):
            response = client.post(f"/activities/Tennis%20Club/signup?email=student{i}@mergington.edu")
            if i < original_max - original_count:
                assert response.status_code == 200
            else:
                assert response.status_code == 400
