import typing
from httpx import Client as _Client, AsyncClient as _AsyncClient, USE_CLIENT_DEFAULT, Response, BaseTransport
from httpx._client import UseClientDefault, EventHook
from httpx._config import DEFAULT_MAX_REDIRECTS, Limits, DEFAULT_LIMITS, DEFAULT_TIMEOUT_CONFIG
from httpx._types import URLTypes, RequestContent, RequestData, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, \
    AuthTypes, TimeoutTypes, RequestExtensions, ProxiesTypes, ProxyTypes, CertTypes, VerifyTypes
from sensei._base_client import BaseClient
from .rate_limiter import IRateLimit, RateLimiter, AsyncRateLimiter


class Client(_Client, BaseClient):
    def __init__(
            self,
            *,
            host: str,
            port: int | None = None,
            rate_limit: IRateLimit | None = None,
            auth: AuthTypes | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            verify: VerifyTypes = True,
            cert: CertTypes | None = None,
            http1: bool = True,
            http2: bool = False,
            proxy: ProxyTypes | None = None,
            proxies: ProxiesTypes | None = None,
            mounts: typing.Mapping[str, BaseTransport | None] | None = None,
            timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
            follow_redirects: bool = False,
            limits: Limits = DEFAULT_LIMITS,
            max_redirects: int = DEFAULT_MAX_REDIRECTS,
            event_hooks: typing.Mapping[str, list[EventHook]] | None = None,
            transport: BaseTransport | None = None,
            app: typing.Callable[..., typing.Any] | None = None,
            trust_env: bool = True,
            default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
    ) -> None:
        BaseClient.__init__(self, host=host, port=port, rate_limit=rate_limit)
        _Client.__init__(
            self,
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxy=proxy,
            proxies=proxies,
            mounts=mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            transport=transport,
            app=app,
            default_encoding=default_encoding,
            trust_env=trust_env,
            base_url=self._api_url
        )

    def request(
            self,
            method: str,
            url: URLTypes,
            *,
            content: RequestContent | None = None,
            data: RequestData | None = None,
            files: RequestFiles | None = None,
            json: typing.Any | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
            follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
            timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
            extensions: RequestExtensions | None = None,
    ) -> Response:
        if self.rate_limit:
            RateLimiter(self.rate_limit).wait_for_slot()

        return super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions
        )


class AsyncClient(_AsyncClient, BaseClient):
    def __init__(
            self,
            *,
            host: str,
            port: int | None = None,
            rate_limit: IRateLimit | None = None,
            auth: AuthTypes | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            verify: VerifyTypes = True,
            cert: CertTypes | None = None,
            http1: bool = True,
            http2: bool = False,
            proxy: ProxyTypes | None = None,
            proxies: ProxiesTypes | None = None,
            mounts: typing.Mapping[str, BaseTransport | None] | None = None,
            timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
            follow_redirects: bool = False,
            limits: Limits = DEFAULT_LIMITS,
            max_redirects: int = DEFAULT_MAX_REDIRECTS,
            event_hooks: typing.Mapping[str, list[EventHook]] | None = None,
            transport: BaseTransport | None = None,
            app: typing.Callable[..., typing.Any] | None = None,
            trust_env: bool = True,
            default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
    ) -> None:
        BaseClient.__init__(self, host=host, port=port, rate_limit=rate_limit)
        _AsyncClient.__init__(
            self,
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxy=proxy,
            proxies=proxies,
            mounts=mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            transport=transport,
            app=app,
            default_encoding=default_encoding,
            trust_env=trust_env,
            base_url=self._api_url
        )

    async def request(
            self,
            method: str,
            url: URLTypes,
            *,
            content: RequestContent | None = None,
            data: RequestData | None = None,
            files: RequestFiles | None = None,
            json: typing.Any | None = None,
            params: QueryParamTypes | None = None,
            headers: HeaderTypes | None = None,
            cookies: CookieTypes | None = None,
            auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
            follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
            timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
            extensions: RequestExtensions | None = None,
    ) -> Response:
        if self.rate_limit:
            await AsyncRateLimiter(self.rate_limit).wait_for_slot()

        return await super().request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions
        )
