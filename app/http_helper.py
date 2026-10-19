import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)


async def send_with_retries(
    client: httpx.AsyncClient,
    request: httpx.Request,
) -> httpx.Response:
    def should_retry(exc: BaseException) -> bool:
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
            return True

        if request.method == "GET" and isinstance(
            exc, (httpx.ReadError, httpx.ReadTimeout)
        ):
            return True

        return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
            429,
            502,
            503,
            504,
        }

    async for attempt in AsyncRetrying(
        retry=retry_if_exception(should_retry),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=0.5, max=5),
        reraise=True,
    ):
        with attempt:
            response = await client.send(request)
            _ = response.raise_for_status()
            return response

    raise RuntimeError("Retry loop exited unexpectedly")
