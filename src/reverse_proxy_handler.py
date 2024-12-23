class ReverseProxyHandler(tornado.web.RequestHandler):
    async def prepare(self):
        self.flask_url = "http://localhost:8502"
        self.target_url = f"{self.flask_url}{self.request.uri[len('/proxy'):]}"
        self.http_client = tornado.httpclient.AsyncHTTPClient()

    async def get(self):
        try:
            response = await self.http_client.fetch(self.target_url, method="GET", headers=self.request.headers)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.write(response.body)
        except tornado.httpclient.HTTPClientError as e:
            if e.code == 304:
                self.set_status(304)
                self.finish()
            else:
                raise

    async def post(self):
        body = self.request.body
        response = await self.http_client.fetch(self.target_url, method="POST", headers=self.request.headers, body=body)
        self.set_status(response.code)
        for header, value in response.headers.get_all():
            self.set_header(header, value)
        self.write(response.body)

    async def put(self):
        body = self.request.body
        response = await self.http_client.fetch(self.target_url, method="PUT", headers=self.request.headers, body=body)
        self.set_status(response.code)
        for header, value in response.headers.get_all():
            self.set_header(header, value)
        self.write(response.body)

    async def delete(self):
        response = await self.http_client.fetch(self.target_url, method="DELETE", headers=self.request.headers)
        self.set_status(response.code)
        for header, value in response.headers.get_all():
            self.set_header(header, value)
        self.write(response.body)
