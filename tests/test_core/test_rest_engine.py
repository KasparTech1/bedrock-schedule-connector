"""
REST Engine Tests
=================

Tests for REST engine error handling, retries, and rate limiting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import httpx

from kai_erp.core.rest_engine import RestEngine
from kai_erp.core.types import IDOSpec, RateLimitError
from kai_erp.config import SyteLineConfig


@pytest.fixture
def mock_config():
    """Create a mock SyteLine configuration."""
    return SyteLineConfig(
        base_url="https://test.syteline.com",
        config_name="TEST_CONFIG",
        username="test_user",
        password="test_pass",
    )


@pytest.fixture
def mock_response_success():
    """Create a successful mock response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {
        "value": [
            {"Job": "J-001", "Item": "ITEM-001"},
            {"Job": "J-002", "Item": "ITEM-002"},
        ]
    }
    return response


@pytest.fixture
def mock_response_rate_limited():
    """Create a rate-limited mock response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 429
    response.headers = {"Retry-After": "1"}
    return response


@pytest.fixture
def mock_response_error():
    """Create an error mock response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 500
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=response,
    )
    return response


class TestRestEngineInitialization:
    """Tests for RestEngine initialization."""
    
    @pytest.mark.asyncio
    async def test_engine_requires_context_manager(self, mock_config):
        """Engine methods should fail if not initialized via context manager."""
        engine = RestEngine(mock_config)
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
    
    @pytest.mark.asyncio
    async def test_staging_property_requires_init(self, mock_config):
        """Staging property should fail if not initialized."""
        engine = RestEngine(mock_config)
        
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = engine.staging


class TestRestEngineFetchIDO:
    """Tests for fetch_ido method."""
    
    @pytest.mark.asyncio
    async def test_fetch_ido_success(self, mock_config, mock_response_success):
        """Should successfully fetch IDO data."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                # Setup mocks
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response_success)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    result = await engine.fetch_ido(IDOSpec("SLJobs", ["Job", "Item"]))
                
                assert len(result) == 2
                assert result[0]["Job"] == "J-001"
    
    @pytest.mark.asyncio
    async def test_fetch_ido_with_max_records(self, mock_config, mock_response_success):
        """Should limit results to max_records."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response_success)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    result = await engine.fetch_ido(
                        IDOSpec("SLJobs", ["Job"]),
                        max_records=1
                    )
                
                assert len(result) == 1


class TestRestEngineRateLimiting:
    """Tests for rate limit handling."""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, mock_config, mock_response_success, mock_response_rate_limited):
        """Should retry on rate limit with backoff."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    mock_client = AsyncMock()
                    # First call rate limited, second succeeds
                    mock_client.get = AsyncMock(
                        side_effect=[mock_response_rate_limited, mock_response_success]
                    )
                    MockClient.return_value = mock_client
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock()
                    
                    mock_staging = AsyncMock()
                    MockStaging.return_value = mock_staging
                    mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                    mock_staging.__aexit__ = AsyncMock()
                    
                    async with RestEngine(mock_config) as engine:
                        result = await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
                    
                    # Should have slept once
                    mock_sleep.assert_called_once()
                    # Should have retried and succeeded
                    assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_config, mock_response_rate_limited):
        """Should raise RateLimitError after max retries."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    mock_client = AsyncMock()
                    # Always rate limited
                    mock_client.get = AsyncMock(return_value=mock_response_rate_limited)
                    MockClient.return_value = mock_client
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock()
                    
                    mock_staging = AsyncMock()
                    MockStaging.return_value = mock_staging
                    mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                    mock_staging.__aexit__ = AsyncMock()
                    
                    async with RestEngine(mock_config) as engine:
                        with pytest.raises(RateLimitError):
                            await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_config, mock_response_rate_limited, mock_response_success):
        """Should use exponential backoff on retries."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    mock_client = AsyncMock()
                    # Rate limited twice, then success
                    mock_client.get = AsyncMock(side_effect=[
                        mock_response_rate_limited,
                        mock_response_rate_limited,
                        mock_response_success,
                    ])
                    MockClient.return_value = mock_client
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock()
                    
                    mock_staging = AsyncMock()
                    MockStaging.return_value = mock_staging
                    mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                    mock_staging.__aexit__ = AsyncMock()
                    
                    async with RestEngine(mock_config) as engine:
                        result = await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
                    
                    # Should have slept twice with increasing backoff
                    assert mock_sleep.call_count == 2


class TestRestEngineParallelFetch:
    """Tests for parallel_fetch method."""
    
    @pytest.mark.asyncio
    async def test_parallel_fetch_multiple_idos(self, mock_config, mock_response_success):
        """Should fetch multiple IDOs in parallel."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response_success)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    specs = [
                        IDOSpec("SLJobs", ["Job"]),
                        IDOSpec("SLItems", ["Item"]),
                        IDOSpec("SLWcs", ["Wc"]),
                    ]
                    result = await engine.parallel_fetch(specs)
                
                assert "SLJobs" in result
                assert "SLItems" in result
                assert "SLWcs" in result
    
    @pytest.mark.asyncio
    async def test_parallel_fetch_handles_partial_failure(self, mock_config, mock_response_success, mock_response_error):
        """Should handle partial failures in parallel fetch."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                # First succeeds, second fails
                mock_client.get = AsyncMock(side_effect=[
                    mock_response_success,
                    mock_response_error,
                ])
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    specs = [
                        IDOSpec("SLJobs", ["Job"]),
                        IDOSpec("SLItems", ["Item"]),
                    ]
                    result = await engine.parallel_fetch(specs)
                
                # First should have data, second should be empty
                assert len(result["SLJobs"]) == 2
                assert len(result["SLItems"]) == 0


class TestRestEngineErrorHandling:
    """Tests for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_http_error_propagates(self, mock_config, mock_response_error):
        """Should propagate HTTP errors."""
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response_error)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    with pytest.raises(httpx.HTTPStatusError):
                        await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_config):
        """Should handle empty response gracefully."""
        empty_response = MagicMock(spec=httpx.Response)
        empty_response.status_code = 200
        empty_response.json.return_value = {"value": []}
        
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=empty_response)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    result = await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, mock_config):
        """Should handle malformed response."""
        malformed_response = MagicMock(spec=httpx.Response)
        malformed_response.status_code = 200
        malformed_response.json.return_value = {"unexpected": "structure"}
        
        with patch("kai_erp.core.rest_engine.AuthenticatedClient") as MockClient:
            with patch("kai_erp.core.rest_engine.StagingEngine") as MockStaging:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=malformed_response)
                MockClient.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                
                mock_staging = AsyncMock()
                MockStaging.return_value = mock_staging
                mock_staging.__aenter__ = AsyncMock(return_value=mock_staging)
                mock_staging.__aexit__ = AsyncMock()
                
                async with RestEngine(mock_config) as engine:
                    result = await engine.fetch_ido(IDOSpec("SLJobs", ["Job"]))
                
                # Should return empty list when 'value' key is missing
                assert result == []


class TestRestEngineBuildURL:
    """Tests for URL building."""
    
    def test_build_ido_url_basic(self, mock_config):
        """Should build basic IDO URL."""
        engine = RestEngine(mock_config)
        
        spec = IDOSpec("SLJobs", ["Job", "Item"])
        url = engine._build_ido_url(spec)
        
        assert "SLJobs" in url
        assert "$select=Job,Item" in url
        assert "_config=TEST_CONFIG" in url
    
    def test_build_ido_url_with_filter(self, mock_config):
        """Should include filter in URL."""
        engine = RestEngine(mock_config)
        
        spec = IDOSpec("SLJobs", ["Job"], filter="Stat='R'")
        url = engine._build_ido_url(spec)
        
        assert "$filter=Stat='R'" in url
    
    def test_build_ido_url_with_orderby(self, mock_config):
        """Should include orderby in URL."""
        engine = RestEngine(mock_config)
        
        spec = IDOSpec("SLJobs", ["Job"], orderby="Job desc")
        url = engine._build_ido_url(spec)
        
        assert "$orderby=Job desc" in url

