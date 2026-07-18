import pytest
from unittest.mock import patch, MagicMock
import youtube_uploader

@patch("youtube_uploader.get_credentials")
@patch("youtube_uploader.googleapiclient.discovery.build")
@patch("youtube_uploader.MediaFileUpload")
def test_upload_to_youtube(mock_media, mock_build, mock_creds):
    # Setup mocks
    mock_creds.return_value = MagicMock()
    
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    
    mock_videos = MagicMock()
    mock_youtube.videos.return_value = mock_videos
    
    mock_insert = MagicMock()
    mock_videos.insert.return_value = mock_insert
    
    mock_insert.execute.return_value = {"id": "test_video_id"}
    
    # Call function
    url = youtube_uploader.upload_to_youtube(
        "dummy.mp4", 
        "Test Title", 
        "Test Description", 
        ["tag1", "tag2"]
    )
    
    # Verify
    assert url == "https://youtu.be/test_video_id"
    mock_build.assert_called_once()
    mock_videos.insert.assert_called_once()
    
    # Check that insert was called with the right snippet
    call_args = mock_videos.insert.call_args[1]
    assert call_args["body"]["snippet"]["title"] == "Test Title"
    assert call_args["body"]["snippet"]["tags"] == ["tag1", "tag2"]
