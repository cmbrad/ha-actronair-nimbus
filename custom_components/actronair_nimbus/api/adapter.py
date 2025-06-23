import aiohttp
import asyncio
import logging

from asyncio import Lock

# Configure logging
logger = logging.getLogger(__name__)


class APIAdapter:
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts
        self.lock = Lock()

    async def _execute_request(self, session, method, url, **kwargs):
        attempt = 0
        while attempt < self.max_attempts:
            try:
                async with session.request(
                    method=method, url=url, raise_for_status=True, **kwargs
                ) as response:
                    logger.debug(
                        f"Response status: {response.status}, Response text: {await response.text()}"
                    )
                    return response
            except aiohttp.ClientError as e:
                # at max attempts or an uretryable error raise exception and stop
                if attempt == self.max_attempts - 1 or not self._exception_is_retryable(
                    e
                ):
                    logger.exception(f"API call failed after {attempt} attempts.")
                    raise e from None

                wait_time = 2**attempt
                attempt += 1
                logger.warning(
                    f"API call encountered an error: {e}. Attempt {attempt}/{self.max_attempts}, retrying after {wait_time} seconds..."
                )
                await asyncio.sleep(wait_time)
        return None

    async def request(self, method, url, **kwargs):
        async with self.lock, aiohttp.ClientSession() as session:
            return await self._execute_request(session, method, url, **kwargs)
        return None

    def _exception_is_retryable(self, e):
        # if our exception has a status code then check it
        if hasattr(e, "status"):
            return e.status not in [400]
        # if not then always retry
        return True
