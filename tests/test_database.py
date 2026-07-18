import os
import pytest
from database import init_db, load_job, save_job, list_jobs, delete_job_db

TEST_DB = "test_database.sqlite"

@pytest.fixture(autouse=True)
def setup_db():
    # Remove old test DB if it exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Initialize fresh DB
    init_db(TEST_DB)
    yield
    # Cleanup after test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_save_and_load_job():
    job_data = {
        "job_id": "test_123",
        "script_id": "script_abc",
        "status": "queued",
        "progress": 0,
        "message": "En cola",
        "created_at": "2024-01-01T00:00:00",
        "output_files": []
    }
    
    save_job("test_123", job_data, db_path=TEST_DB)
    loaded = load_job("test_123", db_path=TEST_DB)
    
    assert loaded is not None
    assert loaded["job_id"] == "test_123"
    assert loaded["status"] == "queued"

def test_list_jobs():
    job_data_1 = {"job_id": "job_1", "created_at": "2024-01-01"}
    job_data_2 = {"job_id": "job_2", "created_at": "2024-01-02"}
    
    save_job("job_1", job_data_1, db_path=TEST_DB)
    save_job("job_2", job_data_2, db_path=TEST_DB)
    
    jobs = list_jobs(db_path=TEST_DB)
    assert len(jobs) == 2
    # Should be sorted by created_at DESC
    assert jobs[0]["job_id"] == "job_2"
    assert jobs[1]["job_id"] == "job_1"

def test_delete_job():
    job_data = {"job_id": "job_delete"}
    save_job("job_delete", job_data, db_path=TEST_DB)
    
    assert load_job("job_delete", db_path=TEST_DB) is not None
    
    deleted = delete_job_db("job_delete", db_path=TEST_DB)
    assert deleted is True
    assert load_job("job_delete", db_path=TEST_DB) is None

    deleted_again = delete_job_db("job_delete", db_path=TEST_DB)
    assert deleted_again is False
