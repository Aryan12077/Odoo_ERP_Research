import requests

from config import config


class OdooClient:
    """
    Simple Odoo JSON-RPC Client
    """

    def __init__(self):
        self.url = f"{config.url}/jsonrpc"

        self.db = config.database
        self.username = config.username
        self.secret = config.secret

        self.timeout = config.timeout
        self.verify_ssl = config.verify_ssl

        self.uid = None

    ####################################################################
    # PRIVATE
    ####################################################################

    def _call(self, service, method, args):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args
            },
            "id": 1
        }

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                response.raise_for_status()
                result = response.json()

                if "error" in result:
                    raise Exception(result["error"])

                return result["result"]
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1.5 * (attempt + 1))

    ####################################################################
    # AUTHENTICATION
    ####################################################################

    def authenticate(self):
        uid = self._call(
            "common",
            "authenticate",
            [
                self.db,
                self.username,
                self.secret,
                {}
            ]
        )

        if not uid:
            raise Exception("Authentication Failed.")

        self.uid = uid

        return uid

    ####################################################################
    # GENERIC RPC
    ####################################################################

    def execute_kw(
        self,
        model,
        method,
        args=None,
        kwargs=None
    ):
        if self.uid is None:
            raise Exception("Authenticate first.")

        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        return self._call(
            "object",
            "execute_kw",
            [
                self.db,
                self.uid,
                self.secret,
                model,
                method,
                args,
                kwargs
            ]
        )

    ####################################################################
    # READ OPERATIONS
    ####################################################################

    def search(
        self,
        model,
        domain=None
    ):
        if domain is None:
            domain = []

        return self.execute_kw(
            model=model,
            method="search",
            args=[domain]
        )

    def read(
        self,
        model,
        ids,
        fields=None
    ):
        if fields is None:
            fields = []

        return self.execute_kw(
            model=model,
            method="read",
            args=[ids],
            kwargs={
                "fields": fields
            }
        )

    def search_read(
        self,
        model,
        domain=None,
        fields=None,
        limit=0,
        offset=0,
        order=""
    ):
        if domain is None:
            domain = []

        if fields is None:
            fields = []

        kwargs = {"fields": fields}
        if limit > 0:
            kwargs["limit"] = limit
        if offset > 0:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        return self.execute_kw(
            model=model,
            method="search_read",
            args=[domain],
            kwargs=kwargs
        )

    def search_count(
        self,
        model,
        domain=None
    ):
        if domain is None:
            domain = []

        return self.execute_kw(
            model=model,
            method="search_count",
            args=[domain]
        )
