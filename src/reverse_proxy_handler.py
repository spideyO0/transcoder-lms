import logging
import tornado.web
import tornado.httpclient

class ReverseProxyHandler(tornado.web.RequestHandler):
    async def prepare(self):
        self.flask_url = "http://localhost:8502"
        self.target_url = f"{self.flask_url}{self.request.uri[len('/proxy'):]}"
        self.http_client = tornado.httpclient.AsyncHTTPClient()
        logging.debug(f"Proxying request to: {self.target_url}")

        # Log request headers
        logging.debug(f"Request headers: {self.request.headers}")

        # Optionally modify headers to bypass caching
        self.request.headers.pop("If-None-Match", None)
        self.request.headers.pop("If-Modified-Since", None)

        # Dynamically determine the forward proxy URL
        self.forward_proxy_url = self._determine_forward_proxy_url()

    def _determine_forward_proxy_url(self) -> str | None:
        # Example logic to determine the forward proxy URL based on the request
        host = self.request.headers.get("Host", "")
        if "streamlit.app" in host:
            # Attempt to infer the forward proxy URL from the request headers
            via = self.request.headers.get("Via", "")
            if via:
                # Extract the proxy URL from the Via header
                proxy_url = via.split(",")[-1].strip()
                if proxy_url:
                    return proxy_url
            # Fallback to a default proxy URL if no Via header is present
            return "http://default.proxy.server:8080"
        return None

    async def fetch_with_forward_proxy(self, url, method, headers, body=None):
        if self.forward_proxy_url:
            proxy_host, proxy_port = self.forward_proxy_url.split(":")
            request = tornado.httpclient.HTTPRequest(
                url=url,
                method=method,
                headers=headers,
                body=body,
                proxy_host=proxy_host,
                proxy_port=int(proxy_port),
                follow_redirects=True,
                allow_nonstandard_methods=True,
            )
        else:
            request = tornado.httpclient.HTTPRequest(
                url=url,
                method=method,
                headers=headers,
                body=body,
                follow_redirects=True,
                allow_nonstandard_methods=True,
            )
        return await self.http_client.fetch(request)

    async def get(self):
        try:
            response = await self.fetch_with_forward_proxy(self.target_url, "GET", self.request.headers)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.set_header("Content-Security-Policy", "upgrade-insecure-requests")
            self.write(response.body)
        except tornado.httpclient.HTTPClientError as e:
            logging.error(f"HTTPClientError: {e.code} - {e.message}")
            if e.code == 304:
                self.set_status(304)
                self.finish()
            else:
                self.set_status(e.code)
                self.write(f"Error: {e.message}")
        except ConnectionRefusedError:
            logging.error("ConnectionRefusedError: Connection refused")
            self.set_status(502)
            self.write("Error: Connection refused")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self.set_status(500)
            self.write(f"Unexpected error: {str(e)}")

    async def post(self):
        try:
            body = self.request.body
            response = await self.fetch_with_forward_proxy(self.target_url, "POST", self.request.headers, body)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.set_header("Content-Security-Policy", "upgrade-insecure-requests")
            self.write(response.body)
        except tornado.httpclient.HTTPClientError as e:
            logging.error(f"HTTPClientError: {e.code} - {e.message}")
            self.set_status(e.code)
            self.write(f"Error: {e.message}")
        except ConnectionRefusedError:
            logging.error("ConnectionRefusedError: Connection refused")
            self.set_status(502)
            self.write("Error: Connection refused")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self.set_status(500)
            self.write(f"Unexpected error: {str(e)}")

    async def put(self):
        try:
            body = self.request.body
            response = await self.fetch_with_forward_proxy(self.target_url, "PUT", self.request.headers, body)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.set_header("Content-Security-Policy", "upgrade-insecure-requests")
            self.write(response.body)
        except tornado.httpclient.HTTPClientError as e:
            logging.error(f"HTTPClientError: {e.code} - {e.message}")
            self.set_status(e.code)
            self.write(f"Error: {e.message}")
        except ConnectionRefusedError:
            logging.error("ConnectionRefusedError: Connection refused")
            self.set_status(502)
            self.write("Error: Connection refused")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self.set_status(500)
            self.write(f"Unexpected error: {str(e)}")

    async def delete(self):
        try:
            response = await self.fetch_with_forward_proxy(self.target_url, "DELETE", self.request.headers)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.set_header("Content-Security-Policy", "upgrade-insecure-requests")
            self.write(response.body)
        except tornado.httpclient.HTTPClientError as e:
            logging.error(f"HTTPClientError: {e.code} - {e.message}")
            self.set_status(e.code)
            self.write(f"Error: {e.message}")
        except ConnectionRefusedError:
            logging.error("ConnectionRefusedError: Connection refused")
            self.set_status(502)
            self.write("Error: Connection refused")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            self.set_status(500)
            self.write(f"Unexpected error: {str(e)}")
